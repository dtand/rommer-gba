import os
import json
import argparse
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torchvision.models as models
from tqdm import tqdm

print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

TARGET_SIZE = (160, 160)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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

def load_classifier(model_dir, target_field):
    """Load trained classifier and its classes"""
    # Load class names
    classes_path = os.path.join(model_dir, f"{target_field}_classes.npy")
    if not os.path.exists(classes_path):
        print(f"❌ Classes file not found: {classes_path}")
        return None, None
    
    classes = np.load(classes_path, allow_pickle=True)
    num_classes = len(classes)
    
    # Load model
    model = EfficientNetClassifier(num_classes).to(device)
    model_path = os.path.join(model_dir, "best_model.pth")
    if not os.path.exists(model_path):
        model_path = os.path.join(model_dir, "final_model.pth")
    
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        return None, None
    
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    
    print(f"✅ Loaded {target_field} classifier with {num_classes} classes")
    return model, classes

def preprocess_image(image_path):
    """Load and preprocess image for classification"""
    try:
        img = Image.open(image_path).convert("RGB")
        img = img.resize(TARGET_SIZE)
        
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        return transform(img).unsqueeze(0).to(device)
    except Exception as e:
        print(f"⚠️ Error loading image {image_path}: {e}")
        return None

def classify_frame(model, classes, image_tensor):
    """Classify a single frame and return prediction with confidence"""
    if image_tensor is None:
        return None, 0.0
    
    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probabilities, 1)
        
        predicted_class = classes[predicted.item()]
        confidence_score = confidence.item()
        
        return predicted_class, confidence_score

def get_frame_directories(data_uuid):
    """Get all frame directories for a given UUID"""
    data_dir = os.path.join("data", data_uuid)
    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        return []
    
    frame_dirs = []
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if os.path.isdir(item_path) and item.isdigit():
            frame_dirs.append(item_path)
    
    frame_dirs.sort(key=lambda x: int(os.path.basename(x)))
    return frame_dirs

def classify_all_frames(data_uuid, context_model=None, context_classes=None, 
                       scene_model=None, scene_classes=None):
    """Classify all frames in a dataset and save CNN annotations"""
    frame_dirs = get_frame_directories(data_uuid)
    
    if len(frame_dirs) == 0:
        print(f"❌ No frame directories found for UUID: {data_uuid}")
        return
    
    print(f"🔍 Classifying {len(frame_dirs)} frames for UUID: {data_uuid}")
    
    processed_count = 0
    skipped_count = 0
    
    for frame_dir in tqdm(frame_dirs, desc="Classifying frames"):
        frame_num = os.path.basename(frame_dir)
        image_path = os.path.join(frame_dir, f"{frame_num}.png")
        cnn_annotations_path = os.path.join(frame_dir, "cnn_annotations.json")
        
        # Skip if image doesn't exist
        if not os.path.exists(image_path):
            skipped_count += 1
            continue
        
        # Load and preprocess image
        image_tensor = preprocess_image(image_path)
        if image_tensor is None:
            skipped_count += 1
            continue
        
        # Prepare CNN annotations
        cnn_annotations = {
            "frame": int(frame_num),
            "timestamp": None,  # Could be added if available
        }
        
        # Classify with context model if available
        if context_model is not None and context_classes is not None:
            context_pred, context_conf = classify_frame(context_model, context_classes, image_tensor)
            cnn_annotations["context"] = {
                "prediction": context_pred,
                "confidence": round(context_conf, 4)
            }
        
        # Classify with scene model if available
        if scene_model is not None and scene_classes is not None:
            scene_pred, scene_conf = classify_frame(scene_model, scene_classes, image_tensor)
            cnn_annotations["scene"] = {
                "prediction": scene_pred,
                "confidence": round(scene_conf, 4)
            }
        
        # Save CNN annotations
        try:
            with open(cnn_annotations_path, 'w') as f:
                json.dump(cnn_annotations, f, indent=2)
            processed_count += 1
        except Exception as e:
            print(f"⚠️ Error saving {cnn_annotations_path}: {e}")
            skipped_count += 1
    
    print(f"✅ Classification complete!")
    print(f"   Processed: {processed_count} frames")
    print(f"   Skipped: {skipped_count} frames")

def find_classifier_models(data_uuid):
    """Find available classifier models for a UUID"""
    models_dir = "models"
    context_model_dir = None
    scene_model_dir = None
    
    if os.path.exists(models_dir):
        for item in os.listdir(models_dir):
            if data_uuid in item and "fixed" in item:
                if "context_classifier" in item:
                    context_model_dir = os.path.join(models_dir, item)
                elif "scene_classifier" in item:
                    scene_model_dir = os.path.join(models_dir, item)
    
    return context_model_dir, scene_model_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify all frames using trained CNN models")
    parser.add_argument("uuid", help="UUID of the dataset to classify")
    parser.add_argument("--context-model", help="Path to context classifier model directory")
    parser.add_argument("--scene-model", help="Path to scene classifier model directory")
    parser.add_argument("--auto-find", action="store_true", 
                       help="Automatically find model directories based on UUID")
    args = parser.parse_args()
    
    context_model, context_classes = None, None
    scene_model, scene_classes = None, None
    
    # Auto-find models if requested
    if args.auto_find:
        context_model_dir, scene_model_dir = find_classifier_models(args.uuid)
        if context_model_dir:
            print(f"🔍 Found context model: {context_model_dir}")
            args.context_model = context_model_dir
        if scene_model_dir:
            print(f"🔍 Found scene model: {scene_model_dir}")
            args.scene_model = scene_model_dir
    
    # Load context classifier if specified
    if args.context_model:
        if os.path.exists(args.context_model):
            context_model, context_classes = load_classifier(args.context_model, "context")
        else:
            print(f"⚠️ Context model directory not found: {args.context_model}")
    
    # Load scene classifier if specified
    if args.scene_model:
        if os.path.exists(args.scene_model):
            scene_model, scene_classes = load_classifier(args.scene_model, "scene")
        else:
            print(f"⚠️ Scene model directory not found: {args.scene_model}")
    
    # Check if at least one model was loaded
    if context_model is None and scene_model is None:
        print("❌ No valid models found. Use --auto-find or specify model paths.")
        print("Available options:")
        print("  --auto-find                    # Automatically find models")
        print("  --context-model <path>         # Specify context model directory")
        print("  --scene-model <path>           # Specify scene model directory")
        exit(1)
    
    # Run classification
    classify_all_frames(
        args.uuid,
        context_model=context_model,
        context_classes=context_classes,
        scene_model=scene_model,
        scene_classes=scene_classes
    )
