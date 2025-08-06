import os
import json
import argparse
import numpy as np
from PIL import Image
from sklearn.preprocessing import LabelEncoder
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
import torchvision.models as models

print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

TARGET_SIZE = (160, 160)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def get_frame_directories(data_uuid):
    """Get all frame directories for a given UUID that contain annotations.json"""
    data_dir = os.path.join("data", data_uuid)
    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        return []
    
    frame_dirs = []
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if os.path.isdir(item_path) and item.isdigit():
            annotations_path = os.path.join(item_path, "annotations.json")
            if os.path.exists(annotations_path):
                frame_dirs.append(item_path)
    
    frame_dirs.sort(key=lambda x: int(os.path.basename(x)))
    print(f"📁 Found {len(frame_dirs)} frame directories with annotations.")
    return frame_dirs

def load_annotations(frame_dir, target_field="context"):
    """Load annotations from annotations.json file"""
    annotations_path = os.path.join(frame_dir, "annotations.json")
    try:
        with open(annotations_path, "r") as f:
            annotations = json.load(f)
            target_value = annotations.get(target_field)
            if target_value:
                return target_value
            else:
                print(f"⚠️ No {target_field} found in {annotations_path}")
                return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠️ Error reading {annotations_path}: {e}")
        return None

def load_image(frame_path):
    """Load and preprocess image from frame directory"""
    frame_num = os.path.basename(frame_path)
    img_filename = f"{frame_num}.png"
    img_path = os.path.join(frame_path, img_filename)
    
    if os.path.exists(img_path):
        try:
            img = Image.open(img_path).convert("RGB")
            img = img.resize(TARGET_SIZE)
            transform = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            return transform(img)
        except Exception as e:
            print(f"⚠️ Error loading image {img_path}: {e}")
            return None
    
    print(f"⚠️ No valid image found: {img_path}")
    return None

def create_temporal_split(frame_dirs, test_size=0.2, min_gap=20):
    """
    Create train/test split that avoids temporal data leakage.
    Uses systematic sampling with gaps to ensure no consecutive frames
    in different splits.
    """
    frame_numbers = [int(os.path.basename(f)) for f in frame_dirs]
    
    # Sort by frame number
    sorted_indices = np.argsort(frame_numbers)
    sorted_frame_dirs = [frame_dirs[i] for i in sorted_indices]
    sorted_frame_numbers = [frame_numbers[i] for i in sorted_indices]
    
    # Use systematic sampling every N frames for test set
    n_test = int(len(frame_dirs) * test_size)
    step = max(3, len(frame_dirs) // n_test)  # Ensure step is at least 3
    
    test_indices = []
    train_indices = []
    
    # Select test frames with systematic sampling
    test_frames = set()
    for i in range(0, len(sorted_frame_dirs), step):
        if len(test_indices) < n_test:
            test_indices.append(i)
            test_frames.add(sorted_frame_numbers[i])
    
    # Add remaining frames to train, but skip those too close to test frames
    for i, frame_num in enumerate(sorted_frame_numbers):
        if i not in test_indices:
            # Check if this frame is too close to any test frame
            too_close = False
            for test_frame in test_frames:
                if abs(frame_num - test_frame) < min_gap:
                    too_close = True
                    break
            
            if not too_close:
                train_indices.append(i)
    
    # If we don't have enough train samples, reduce the gap
    if len(train_indices) < len(frame_dirs) * 0.5:
        print(f"⚠️ Reducing gap from {min_gap} to {min_gap//2} to get more train samples")
        return create_temporal_split(frame_dirs, test_size, min_gap//2)
    
    train_dirs = [sorted_frame_dirs[i] for i in train_indices]
    test_dirs = [sorted_frame_dirs[i] for i in test_indices]
    
    print(f"🔄 Temporal split:")
    print(f"  Train frames: {len(train_dirs)}")
    print(f"  Test frames: {len(test_dirs)}")
    print(f"  Minimum gap between train/test: {min_gap} frames")
    
    return train_dirs, test_dirs

def downsample_sequences(frame_dirs, max_consecutive=5, target_field="context"):
    """
    Downsample long sequences of the same context/scene to reduce memorization
    """
    # Load contexts/scenes first
    contexts = []
    valid_dirs = []
    
    for frame_dir in frame_dirs:
        context = load_annotations(frame_dir, target_field)
        if context:
            contexts.append(context)
            valid_dirs.append(frame_dir)
    
    # Downsample consecutive sequences
    downsampled_dirs = []
    downsampled_contexts = []
    
    if len(contexts) == 0:
        return [], []
    
    current_context = contexts[0]
    consecutive_count = 1
    downsampled_dirs.append(valid_dirs[0])
    downsampled_contexts.append(contexts[0])
    
    for i in range(1, len(contexts)):
        if contexts[i] == current_context:
            consecutive_count += 1
            # Only keep every nth frame in long sequences
            if consecutive_count <= max_consecutive or consecutive_count % 3 == 0:
                downsampled_dirs.append(valid_dirs[i])
                downsampled_contexts.append(contexts[i])
        else:
            # Context changed, reset counter
            current_context = contexts[i]
            consecutive_count = 1
            downsampled_dirs.append(valid_dirs[i])
            downsampled_contexts.append(contexts[i])
    
    print(f"📉 Downsampled from {len(frame_dirs)} to {len(downsampled_dirs)} frames")
    return downsampled_dirs, downsampled_contexts

def collect_dataset(data_uuid, use_temporal_split=True, downsample=True, target_field="context"):
    """Collect images and labels with proper validation strategy"""
    frame_dirs = get_frame_directories(data_uuid)
    
    # Downsample long sequences
    if downsample:
        frame_dirs, contexts = downsample_sequences(frame_dirs, target_field=target_field)
    else:
        contexts = [load_annotations(fd, target_field) for fd in frame_dirs]
        frame_dirs = [fd for fd, ctx in zip(frame_dirs, contexts) if ctx is not None]
        contexts = [ctx for ctx in contexts if ctx is not None]
    
    # Split with temporal awareness
    if use_temporal_split:
        train_dirs, test_dirs = create_temporal_split(frame_dirs)
    else:
        # Fallback to random split (for comparison)
        from sklearn.model_selection import train_test_split
        train_dirs, test_dirs = train_test_split(frame_dirs, test_size=0.2, random_state=42)
    
    # Load images and contexts/scenes for each split
    def load_split_data(dirs):
        images, labels = [], []
        for frame_dir in dirs:
            image = load_image(frame_dir)
            context = load_annotations(frame_dir, target_field)
            if image is not None and context is not None:
                images.append(image)
                labels.append(context)
        return images, labels
    
    train_images, train_labels = load_split_data(train_dirs)
    test_images, test_labels = load_split_data(test_dirs)
    
    if len(train_images) == 0 or len(test_images) == 0:
        print("❌ No valid samples found!")
        return None, None, None, None, None, None
    
    # Encode labels
    all_labels = train_labels + test_labels
    le = LabelEncoder()
    le.fit(all_labels)
    
    train_y = le.transform(train_labels)
    test_y = le.transform(test_labels)
    num_classes = len(le.classes_)
    
    print(f"🖼️ Train: {len(train_images)} frames, Test: {len(test_images)} frames")
    print(f"🏷️ Detected {num_classes} unique {target_field}s: {le.classes_.tolist()}")
    
    # Save the label encoder classes
    model_dir = f"models/{target_field}_classifier_{data_uuid}_fixed"
    os.makedirs(model_dir, exist_ok=True)
    np.save(os.path.join(model_dir, f"{target_field}_classes.npy"), le.classes_)
    
    # Convert to tensors
    train_images_tensor = torch.stack(train_images)
    test_images_tensor = torch.stack(test_images)
    train_labels_tensor = torch.tensor(train_y, dtype=torch.long)
    test_labels_tensor = torch.tensor(test_y, dtype=torch.long)
    
    return train_images_tensor, test_images_tensor, train_labels_tensor, test_labels_tensor, num_classes, model_dir

class ClassificationDataset(Dataset):
    def __init__(self, images, labels):
        self.images = images
        self.labels = labels
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        return self.images[idx], self.labels[idx]

class EfficientNetClassifier(nn.Module):
    def __init__(self, num_classes):
        super(EfficientNetClassifier, self).__init__()
        self.backbone = models.efficientnet_b0(weights='IMAGENET1K_V1')
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(self.backbone.classifier[1].in_features, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x):
        return self.backbone(x)

def build_model(num_classes):
    print(f"🛠️ Building EfficientNet model for {num_classes}-class classification")
    model = EfficientNetClassifier(num_classes).to(device)
    return model

def train_model(model, train_loader, val_loader, num_epochs, model_dir):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', patience=3, factor=0.2)
    
    best_val_acc = 0.0
    patience_counter = 0
    patience = 5
    
    for epoch in range(num_epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(device), target.to(device)
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            _, predicted = torch.max(output.data, 1)
            train_total += target.size(0)
            train_correct += (predicted == target).sum().item()
            
            if batch_idx % 10 == 0:
                print(f'Epoch {epoch+1}/{num_epochs}, Batch {batch_idx}, Loss: {loss.item():.4f}')
        
        train_acc = 100 * train_correct / train_total
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for data, target in val_loader:
                data, target = data.to(device), target.to(device)
                output = model(data)
                loss = criterion(output, target)
                
                val_loss += loss.item()
                _, predicted = torch.max(output.data, 1)
                val_total += target.size(0)
                val_correct += (predicted == target).sum().item()
        
        val_acc = 100 * val_correct / val_total
        
        print(f'Epoch {epoch+1}/{num_epochs}:')
        print(f'  Train Loss: {train_loss/len(train_loader):.4f}, Train Acc: {train_acc:.2f}%')
        print(f'  Val Loss: {val_loss/len(val_loader):.4f}, Val Acc: {val_acc:.2f}%')
        
        scheduler.step(val_acc)
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            torch.save(model.state_dict(), os.path.join(model_dir, "best_model.pth"))
            print(f'  New best model saved! Val Acc: {val_acc:.2f}%')
        else:
            patience_counter += 1
            
        if patience_counter >= patience:
            print(f'Early stopping after {epoch+1} epochs')
            break
    
    return best_val_acc

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train CNN classifier with proper validation")
    parser.add_argument("uuid", help="UUID of the dataset to train on")
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for training")
    parser.add_argument("--no-temporal-split", action="store_true", help="Use random split instead of temporal")
    parser.add_argument("--no-downsample", action="store_true", help="Don't downsample long sequences")
    parser.add_argument("--target", choices=["context", "scene"], default="context", 
                       help="Classification target: 'context' for high-level contexts or 'scene' for detailed scenes")
    args = parser.parse_args()

    print(f"🎯 Training CNN {args.target} classifier with proper validation")
    print(f"   Dataset: {args.uuid}")
    print(f"   Target: {args.target}")
    print(f"   Temporal split: {not args.no_temporal_split}")
    print(f"   Downsampling: {not args.no_downsample}")
    
    # Load dataset with proper validation strategy
    X_train, X_test, y_train, y_test, num_classes, model_dir = collect_dataset(
        args.uuid, 
        use_temporal_split=not args.no_temporal_split,
        downsample=not args.no_downsample,
        target_field=args.target
    )
    
    if X_train is None:
        print("❌ Failed to load dataset. Exiting.")
        exit(1)

    # Create data loaders
    train_dataset = ClassificationDataset(X_train, y_train)
    test_dataset = ClassificationDataset(X_test, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)

    # Build and train model
    model = build_model(num_classes)
    
    print("🚀 Starting training...")
    best_val_acc = train_model(model, train_loader, test_loader, args.epochs, model_dir)
    
    print(f"🎯 Best Validation Accuracy: {best_val_acc:.2f}%")
    torch.save(model.state_dict(), os.path.join(model_dir, "final_model.pth"))
    print(f"💾 Model saved to {model_dir}/final_model.pth")
