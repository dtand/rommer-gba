#!/usr/bin/env python3
"""
Setup script for GBA Memory Analysis Training Pipeline

This script helps set up the environment for training and running
the GBA memory analysis model with QLoRA.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

def check_gpu():
    """Check if CUDA GPU is available."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"✅ GPU detected: {gpu_name}")
            print(f"   Memory: {gpu_memory:.1f} GB")
            print(f"   CUDA version: {torch.version.cuda}")
            return True
        else:
            print("❌ No CUDA GPU detected")
            return False
    except ImportError:
        print("❓ PyTorch not installed - cannot check GPU")
        return False

def install_requirements():
    """Install the required packages."""
    requirements_file = Path(__file__).parent / "ml_requirements.txt"
    
    if not requirements_file.exists():
        print(f"❌ Requirements file not found: {requirements_file}")
        return False
        
    print("📦 Installing ML requirements...")
    try:
        # Install PyTorch with CUDA support first
        print("Installing PyTorch with CUDA support...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "torch", "torchvision", "torchaudio", 
            "--index-url", "https://download.pytorch.org/whl/cu121"
        ])
        
        # Install other requirements
        print("Installing other ML dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def check_huggingface_auth():
    """Check if Hugging Face authentication is set up for Llama access."""
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        user = api.whoami()
        print(f"✅ Hugging Face authenticated as: {user['name']}")
        return True
    except Exception:
        print("❌ Hugging Face authentication not set up")
        print("   Run: huggingface-cli login")
        print("   You'll need access to meta-llama/Llama-3.1-8B")
        return False

def create_directories():
    """Create necessary directories."""
    directories = [
        "models",
        "training_data",
        "outputs",
        "logs"
    ]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
        print(f"📁 Created directory: {dir_path}")

def check_training_data():
    """Check if training data exists."""
    training_dir = Path("training_data")
    jsonl_files = list(training_dir.glob("*.jsonl"))
    
    if jsonl_files:
        print(f"✅ Found {len(jsonl_files)} training files:")
        for file in jsonl_files:
            size_mb = file.stat().st_size / (1024*1024)
            print(f"   - {file.name} ({size_mb:.1f} MB)")
        return True
    else:
        print("❌ No training data found in training_data/")
        print("   Generate training data first using generate_training_jsonl.py")
        return False

def test_model_access():
    """Test if we can access the Llama model."""
    try:
        from transformers import AutoTokenizer
        print("🧪 Testing model access...")
        tokenizer = AutoTokenizer.from_pretrained(
            "meta-llama/Llama-3.1-8B",
            trust_remote_code=True
        )
        print("✅ Model access successful")
        return True
    except Exception as e:
        print(f"❌ Cannot access model: {e}")
        print("   Make sure you have access to meta-llama/Llama-3.1-8B")
        return False

def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "="*60)
    print("🚀 SETUP COMPLETE - NEXT STEPS")
    print("="*60)
    print("\n1. Train the model:")
    print("   python src/scripts/train_gba_analyzer.py training_data/your_file.jsonl")
    print("\n2. Test the trained model:")
    print("   python src/scripts/inference_gba_analyzer.py ./models/gba-analyzer")
    print("\n3. Example training command with custom parameters:")
    print("   python src/scripts/train_gba_analyzer.py \\")
    print("     training_data/98cc9f85-0567-4392-8b0e-636a8d65b3a2-full.jsonl \\")
    print("     --epochs 5 --learning-rate 1e-4 --batch-size 2")
    print("\n4. Example queries to test:")
    print("   - Which addresses are associated with player health?")
    print("   - Which memory locations track enemy positions?")
    print("   - Which addresses control battle mechanics?")

def main():
    parser = argparse.ArgumentParser(description="Setup GBA Memory Analysis Training Environment")
    parser.add_argument("--install", action="store_true", help="Install required packages")
    parser.add_argument("--check-only", action="store_true", help="Only check environment, don't install")
    
    args = parser.parse_args()
    
    print("🔧 GBA Memory Analysis Training Setup")
    print("="*40)
    
    # Create directories
    create_directories()
    
    # Check environment
    all_good = True
    
    if not args.check_only and args.install:
        if not install_requirements():
            all_good = False
    
    if not check_gpu():
        print("⚠️  GPU not detected. Training will be very slow on CPU.")
        all_good = False
    
    if not check_huggingface_auth():
        all_good = False
        
    if not check_training_data():
        print("ℹ️  Generate training data first if you haven't already")
        
    if not test_model_access():
        all_good = False
    
    if all_good:
        print("\n✅ Environment setup complete!")
        print_next_steps()
    else:
        print("\n❌ Setup incomplete. Please resolve the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
