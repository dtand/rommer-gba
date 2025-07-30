import os
import numpy as np
from PIL import Image
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf

print(tf.config.list_physical_devices('GPU'))

SNAPSHOTS_DIR = "snapshots"
TARGET_SIZE = (160, 160)
BATCH_SIZE = 4
EPOCHS = 10
TEST_SPLIT = 0.2

gpus = tf.config.list_physical_devices('GPU')
tf.config.experimental.set_virtual_device_configuration(
    gpus[0],
    [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=6144)]
)

def get_snapshot_folders():
    folders = sorted([
        os.path.join(SNAPSHOTS_DIR, d)
        for d in os.listdir(SNAPSHOTS_DIR)
        if os.path.isdir(os.path.join(SNAPSHOTS_DIR, d))
    ])
    print(f"📁 Found {len(folders)} snapshot directories.")
    return folders

def load_tags(folder):
    tag_file = os.path.join(folder, "tags.txt")
    if not os.path.exists(tag_file):
        return None
    with open(tag_file, "r") as f:
        # Take only the first tag
        raw = f.read().strip().split(",")
        return raw[0].strip() if raw else None

def load_image(frame_path):
    img = Image.open(frame_path).convert("RGB")
    img = img.resize(TARGET_SIZE)
    return np.array(img) / 255.0

def collect_dataset():
    images, labels = [], []
    folders = get_snapshot_folders()

    for folder in folders:
        frame_path = os.path.join(folder, "frame.png")
        if not os.path.exists(frame_path):
            print(f"⚠️ Skipping {folder} (no frame.png)")
            continue
        label = load_tags(folder)
        if label is None:
            print(f"⚠️ Skipping {folder} (no label)")
            continue
        images.append(load_image(frame_path))
        labels.append(label)

    le = LabelEncoder()
    y = le.fit_transform(labels)
    num_classes = len(le.classes_)
    y = tf.keras.utils.to_categorical(y, num_classes=num_classes)

    print(f"🖼️ Loaded {len(images)} labeled frames.")
    print(f"🏷️ Detected {num_classes} unique labels: {le.classes_.tolist()}")
    np.save("tag_classes.npy", le.classes_)
    return np.array(images), y, num_classes

def build_tf_dataset(X, y, name="dataset"):
    print(f"🔄 Creating tf.data.Dataset for {name} (size={len(X)})")
    return tf.data.Dataset.from_tensor_slices((X, y)) \
        .shuffle(len(X)) \
        .batch(BATCH_SIZE) \
        .prefetch(tf.data.AUTOTUNE)

def build_model(output_dim):
    print(f"🛠️ Building EfficientNetV2S model for {output_dim}-class softmax")
    base_model = tf.keras.applications.EfficientNetV2S(
        include_top=False,
        weights="imagenet",
        input_shape=(TARGET_SIZE[0], TARGET_SIZE[1], 3),
        pooling="avg"
    )
    x = tf.keras.layers.Dense(128, activation="relu")(base_model.output)
    output = tf.keras.layers.Dense(output_dim, activation="softmax")(x)
    model = tf.keras.Model(inputs=base_model.input, outputs=output)

    model.compile(
        optimizer="adam",
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    model.summary()
    return model

if __name__ == "__main__":
    print("🚀 Starting GBA Single-Label Classifier Training\n")
    X, y, output_dim = collect_dataset()

    print("\n✂️ Splitting dataset...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SPLIT, random_state=42)
    print(f"📊 Train set: {len(X_train)} samples")
    print(f"📊 Test  set: {len(X_test)} samples")

    train_ds = build_tf_dataset(X_train, y_train, "train")
    test_ds = build_tf_dataset(X_test, y_test, "test")

    model = build_model(output_dim)

    print("\n🔁 Starting model.fit() with validation...\n")
    model.fit(train_ds, epochs=EPOCHS, validation_data=test_ds)

    print("\n💾 Saving model to gba_single_classifier.h5")
    model.save("gba_single_classifier.h5")
    print("✅ Training complete.")
