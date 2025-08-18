# GBA Memory Tracing, Analysis & ML Training Project

## Overview
This project provides a comprehensive toolkit for automated memory event logging, frame set-based data organization, synchronized visual snapshotting, and **machine learning model training** for Game Boy Advance (GBA) emulation using BizHawk and Python. It supports machine learning training data generation, reinforcement learning research, advanced gameplay analysis, and **specialized language model training** for understanding memory patterns and game semantics.

## 🎯 Project Goals

- **Memory Analysis**: Automated tracking and analysis of GBA memory state changes
- **Data Organization**: Frame set-based organization for consistent annotation and training
- **Web Interface**: Browser-based annotation tool for labeling training data
- **CNN Classification**: Context and scene classification using computer vision
- **LLM Training**: Specialized language models for understanding memory-game semantic relationships

## Key Features
- **Chunked Memory Scanning**: Optimized 5-chunk system for IWRAM/EWRAM monitoring with 50% performance improvement
- **Frame Set Organization**: Groups related frames (5 frames per set) for consistent data annotation
- **CNN Integration**: EfficientNet-B0 dual classification (context: 10 classes, scene: 19 classes)
- **Robust Logging**: Enhanced safety with multiple exit handlers and periodic log flushing
- **Web Interface**: Flask-based annotation tool with CNN predictions for labeling training data
- **LLM Training Pipeline**: QLoRA-based training for specialized memory analysis models
- **Automatic Data Processing**: Seamless conversion from raw logs to organized training datasets

## 🚀 Quick Start Guide

### 1. Environment Setup
```bash
# Clone and setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# For ML training capabilities
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers datasets accelerate peft trl bitsandbytes
```

### 2. Data Collection
```bash
# Start BizHawk and load your GBA ROM
# Run the event_logger.lua script in BizHawk's Lua Console
# The script will automatically begin monitoring and taking screenshots
```

### 3. Data Processing
```bash
# Process collected data into organized frame sets
python src/scripts/combine_event_data.py \
  --csv "C:\path\to\event_log.csv" \
  --snapshots "C:\path\to\snapshots" \
  --output data \
  --game_config resources/game_configs/metabots_rokusho.json
```

### 4. Web Annotation Interface
```bash
# Start the Flask web application with CNN integration
cd src/web_app
python app.py

# Access locally: http://localhost:5000
# CNN predictions will be automatically displayed for each frame
```

## 🤖 Machine Learning Training Pipeline

### Model Recommendations for RTX 2070 Super (8GB VRAM)

| Model | Size | Training Time | Access Required | Status |
|-------|------|---------------|-----------------|--------|
| **Llama 3.2 1B** ⭐ | 1.2B | 1-3 hours | Yes (free) | **RECOMMENDED** |
| **Llama 3.2 3B** | 3.2B | 2-4 hours | Yes (free) | Good alternative |
| Microsoft Phi-3.5 Mini | 3.8B | 2-4 hours | Yes (free) | Available |
| **Llama 3.1 8B** ❌ | 8B | 120+ hours | Yes (free) | **TOO SLOW** |

### LLM Training Quick Start
```bash
# 1. Get model access at https://huggingface.co/meta-llama/Llama-3.2-1B
# 2. Authenticate with Hugging Face
huggingface-cli login

# 3. Generate training data
python src/ml/generate_training_jsonl.py <session-uuid> \
  --output training_data/session.jsonl

# 4. Train the model (1-3 hours)
python src/ml/train_gba_analyzer_1b.py training_data/98cc9f85-0567-4392-8b0e-636a8d65b3a2.jsonl \
  --model-name meta-llama/Llama-3.2-1B \
  --output-dir ./models/gba-analyzer-llama-1b \
  --epochs 2 --batch-size 1 --gradient-accumulation 8

# 5. Test the trained model
python src/ml/inference_gba_analyzer.py ./models/gba-analyzer-llama-1b \
  --query "Which addresses are associated with player health during battle?"
```

## 🏗️ System Architecture

### Core Workflow
1. **BizHawk Lua Script (`event_logger.lua`)**
   - Monitors GBA memory regions (IWRAM/EWRAM) using optimized 5-chunk scanning per frame
   - Logs memory events with frame set tracking to CSV format (12 columns including frame_set_id and chunk_id)
   - Takes synchronized screenshots named by frame_set_id (`0.png`, `1.png`, etc.)
   - Enhanced safety with multiple exit handlers and periodic log flushing (every 300 frames)
   - Automatic log rotation and snapshot directory cleanup at script start

2. **Python Data Processing (`combine_event_data.py`)**
   - Processes CSV logs and organizes data by frame_set_id instead of individual frames
   - Creates directories named by frame_set_id (e.g., `1/`, `2/`, `3/`) containing:
     - `event.json` - Clean JSON with memory changes, timing, and metadata (no redundant fields)
     - `{frame_set_id}.png` - Corresponding screenshot
   - Maps console buttons using game configuration files
   - Generates session metadata with frame_set_id ranges and statistics
   - Optional cleanup of source snapshots directory

3. **CNN Classification System**
   - EfficientNet-B0 models for context and scene classification
   - Dual classification: 10 context classes, 19 scene classes
   - Integrated into web interface for automatic annotation suggestions

4. **Web Annotation Interface (`src/web_app/`)**
   - Flask-based application with CNN prediction integration
   - Browse frame sets and add labels/annotations
   - Network accessible for remote annotation work
   - RESTful API for programmatic access

5. **LLM Training Pipeline**
   - QLoRA-based training for memory pattern understanding
   - Supports multiple model architectures (Llama, Phi, Gemma)
   - Optimized for consumer GPU hardware (RTX 2070 Super+)

## Frame Set System
The project uses a **frame set approach** where:
- Each frame set contains **5 frames** of memory scanning (chunks 0-4)
- Memory regions are scanned in chunks: IWRAM (4KB chunks) and EWRAM (32KB chunks)
- Screenshots are taken after completing each frame set to capture the final state
- All data is organized by `frame_set_id` for consistent annotation and training

## 📁 Directory Structure
```
rommer-gba/
├── bizhawk/
│   └── event_logger.lua              # BizHawk Lua script for memory monitoring
├── src/
│   ├── scripts/
│   │   ├── combine_event_data.py     # Data processing and organization
│   │   └── generate_training_jsonl.py# Training data preparation
│   ├── web_app/                      # Flask annotation interface
│   │   ├── app.py                    # Main Flask application
│   │   ├── routes/                   # API endpoints
│   │   │   ├── frame_event.py        # Frame data with CNN predictions
│   │   │   └── frame_context.py      # Frame context routing
│   │   └── templates/                # Web interface templates
│   ├── ml/                           # Machine learning components
│   │   ├── train_gba_analyzer.py     # Main training script (8B models)
│   │   ├── train_gba_analyzer_1b.py  # Optimized training (1B-3B models)
│   │   ├── inference_gba_analyzer.py # Model inference and testing
│   │   └── cnn_context_classifier.py # CNN classification system
│   ├── classifiers/                  # Pre-trained CNN models
│   │   ├── context_classifier.pth    # Context classification model
│   │   └── scene_classifier.pth      # Scene classification model
│   └── reward_modules/               # Future RL components
├── resources/
│   └── game_configs/                 # Game-specific key mappings
├── training_data/                    # Generated training datasets
│   └── *.jsonl                      # Training data files
├── models/                           # Trained model outputs
│   ├── gba-analyzer-llama-1b/        # Llama 3.2 1B model
│   └── gba-analyzer-llama-8b/        # Llama 3.1 8B model (if trained)
├── data/                             # Session data (gitignored)
│   └── <session_id>/                 # Session-based organization
│       ├── session_metadata.json
│       ├── 1/                        # Frame set directories
│       │   ├── event.json
│       │   └── 1.png
│       └── ...
└── requirements.txt                  # All dependencies
```

## 📊 Data Formats

### CSV Log Format (12 columns):
```
timestamp,region,frame,address,prev_val,curr_val,freq,pc,key_history,current_keys,frame_set_id,chunk_id
```

### JSON Event Format:
```json
{
  "timestamp": 1753996829216,
  "pc": "000001F8",
  "current_keys": [],
  "frame_set_id": 1,
  "frames_in_set": [8, 9, 11, 12, 13],
  "memory_changes": [
    {
      "region": "iwram",
      "frame": 8,
      "address": "03000000",
      "prev_val": "00000000",
      "curr_val": "00000003",
      "freq": 1
    }
  ]
}
```

### ML Training Data Format (JSONL):
```json
{
  "inputs": {
    "buttons": ["None", "A", "B"],
    "frame_range": 10,
    "memory_changes": [
      {
        "address": "03002A49",
        "prev_val": "00FFFFFF",
        "curr_val": "05FFFFFF"
      }
    ]
  },
  "outputs": {
    "context": "battle",
    "scene": "battle_main", 
    "description": "Enemy health decreased from 45 to 7",
    "action": "damage_dealt",
    "intent": "attack_enemy",
    "outcome": "success"
  }
}
```

## 🔧 Advanced Configuration

### LLM Training Parameters
```bash
# QLoRA Configuration for Llama 3.2 1B
python src/ml/train_gba_analyzer_1b.py training_data/session.jsonl \
  --model-name meta-llama/Llama-3.2-1B \
  --output-dir ./models/gba-analyzer-1b \
  --epochs 2 \
  --learning-rate 2e-4 \
  --batch-size 1 \
  --gradient-accumulation 8 \
  --max-length 1024 \
  --verbose
```

### CNN Classification Training
```bash
# Train context classifier
python src/ml/cnn_context_classifier.py \
  --mode train \
  --data-path data/ \
  --model-type context \
  --epochs 50

# Train scene classifier
python src/ml/cnn_context_classifier.py \
  --mode train \
  --data-path data/ \
  --model-type scene \
  --epochs 50
```

### Web Interface Network Setup (Windows)
```cmd
# Configure Windows Firewall for network access
netsh advfirewall firewall add rule name="Flask App Port 5000" dir=in action=allow protocol=TCP localport=5000

# Find your IP address
ipconfig

# Access from other devices: http://<your-ip>:5000
```

## 🎯 Model Capabilities

The trained LLM learns to:

1. **Associate memory patterns with game events**
   - Links specific address changes to high-level semantics
   - Understands context like "battle", "overworld", "menu"

2. **Identify functional groups of addresses**
   - Recognizes patterns in address ranges
   - Associates similar changes across different contexts

3. **Recommend relevant addresses for queries**
   - Suggests addresses based on training patterns
   - Provides confidence and reasoning for recommendations

### Example Queries and Responses

**Query**: "Which addresses are associated with player health during battle?"

**Expected Response**: "Based on training patterns, addresses like `03002A49`, `03002A7D`, and `03002AB1` frequently change during battle contexts when damage is dealt or healing occurs. These addresses show patterns consistent with health tracking..."

## 🖥️ Hardware Requirements

### Minimum Requirements
- **GPU**: GTX 1060 6GB or better (for inference only)
- **RAM**: 8GB+ system RAM
- **Storage**: 20GB+ free space

### Recommended for Training
- **GPU**: RTX 2070 Super (8GB VRAM) or better
- **RAM**: 16GB+ system RAM
- **Storage**: 50GB+ free space for models and training data

## 📈 Performance Optimizations

- **5-Chunk Memory System**: 50% performance improvement over previous 4-chunk system
- **Buffered Logging**: 200-entry buffer with periodic flushing to minimize I/O impact
- **Combined Processing**: IWRAM and EWRAM processed together to reduce overhead
- **QLoRA Training**: 4-bit quantization enables large model training on consumer hardware
- **CNN Integration**: Efficient EfficientNet-B0 models for real-time classification
- **Robust Error Handling**: Multiple exit handlers ensure data preservation

## 🧪 Current Training Status

As of August 5, 2025:
- ✅ **Llama 3.2 1B training active**: Model downloading and training in progress
- ✅ **CNN models trained**: Context and scene classifiers operational
- ✅ **Web interface functional**: CNN predictions integrated
- ✅ **Training data prepared**: 98cc9f85-0567-4392-8b0e-636a8d65b3a2.jsonl ready
- 🔄 **Expected completion**: 1-3 hours from training start

## 🔍 Troubleshooting

### Common Issues

1. **CUDA Out of Memory**
   - Reduce batch size to 1
   - Increase gradient accumulation steps
   - Use Llama 3.2 1B instead of 8B

2. **Model Access Denied**
   - Ensure Hugging Face authentication: `huggingface-cli login`
   - Request access to models on Hugging Face

3. **Slow Training**
   - Verify GPU utilization with `nvidia-smi`
   - Use smaller models (1B-3B parameters)
   - Check CUDA installation

4. **404 Errors in Web Interface**
   - These are expected for frames without manual annotations
   - CNN predictions are working correctly

## 🤝 Contributing

To improve this project:
1. Experiment with different LoRA configurations for training
2. Add more sophisticated memory pattern analysis
3. Implement additional CNN architectures
4. Enhance the web interface with more annotation features
5. Add evaluation metrics for address recommendation quality

## 📝 License
See [LICENSE](LICENSE).

---

**Note**: This project represents a complete pipeline from raw memory data collection to trained language models capable of understanding GBA memory patterns and game semantics.
