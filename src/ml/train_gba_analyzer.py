#!/usr/bin/env python3
"""
QLoRA Fine-tuning Pipeline for GBA Memory Analysis using Llama 3.1 8B

This script trains a specialized model to understand relationships between:
- Memory address changes (inputs)
- High-level game semantics (context, scene, action, description)

Goal: Enable the model to answer questions like:
- "Which addresses are associated with player location?"
- "Which memory locations track enemy health?"
- "Which addresses are used for experience points?"
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)
import accelerate

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GBAMemoryAnalysisTrainer:
    """Trainer for GBA memory analysis using QLoRA on Llama 3.1 8B."""
    
    def __init__(self, model_name: str = "meta-llama/Llama-3.1-8B", output_dir: str = "gba-analyzer"):
        self.model_name = model_name
        self.output_dir = output_dir
        self.tokenizer = None
        self.model = None
        
    def setup_model_and_tokenizer(self):
        """Initialize the model and tokenizer with QLoRA configuration."""
        logger.info("Setting up model and tokenizer...")
        
        # Configure 4-bit quantization
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            padding_side="right"
        )
        
        # Add pad token if it doesn't exist
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        # Load model with quantization
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.bfloat16
        )
        
        # Prepare model for k-bit training
        self.model = prepare_model_for_kbit_training(self.model)
        
        # Configure LoRA
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            inference_mode=False,
            r=16,  # LoRA rank
            lora_alpha=32,  # LoRA scaling parameter
            lora_dropout=0.1,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
        )
        
        # Apply LoRA to model
        self.model = get_peft_model(self.model, lora_config)
        
        logger.info("Model and tokenizer setup complete")
        logger.info(f"Trainable parameters: {self.model.num_parameters()}")
        logger.info(f"Total parameters: {self.model.num_parameters(only_trainable=False)}")
        
    def load_training_data(self, jsonl_file: str) -> List[Dict[str, Any]]:
        """Load training data from JSONL file."""
        logger.info(f"Loading training data from {jsonl_file}")
        
        if not Path(jsonl_file).exists():
            raise FileNotFoundError(f"Training file not found: {jsonl_file}")
            
        training_data = []
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    sample = json.loads(line.strip())
                    training_data.append(sample)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                    
        logger.info(f"Loaded {len(training_data)} training samples")
        return training_data
        
    def format_training_sample(self, sample: Dict[str, Any]) -> str:
        """
        Format a training sample into a prompt-response format for memory analysis.
        
        This creates training examples that teach the model to associate:
        - Memory changes + game context → Semantic understanding
        """
        inputs = sample.get('inputs', {})
        outputs = sample.get('outputs', {})
        
        # Extract key information
        memory_changes = inputs.get('memory_changes', [])
        buttons = inputs.get('buttons', [])
        frame_range = inputs.get('frame_range', 0)
        
        context = outputs.get('context', 'unknown')
        scene = outputs.get('scene', 'unknown')
        description = outputs.get('description', '')
        action_type = outputs.get('action_type', '')
        intent = outputs.get('intent', '')
        outcome = outputs.get('outcome', '')
        
        # Create memory change summary
        memory_summary = []
        address_list = []
        for change in memory_changes[:20]:  # Limit to first 20 changes to avoid token limits
            addr = change.get('address', '')
            prev_val = change.get('prev_val', '')
            curr_val = change.get('curr_val', '')
            address_list.append(addr)
            memory_summary.append(f"{addr}: {prev_val} → {curr_val}")
            
        # Create comprehensive prompt that teaches memory-semantic relationships
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a GBA (Game Boy Advance) memory analysis expert. You understand the relationships between memory address changes and game events. Your goal is to identify patterns between memory locations and game semantics like player actions, enemy states, locations, and game mechanics.

<|eot_id|><|start_header_id|>user<|end_header_id|>

Analyze this GBA memory state change:

Game Context: {context}
Scene: {scene}
Buttons Pressed: {buttons}
Frame Range: {frame_range}

Memory Changes:
{chr(10).join(memory_summary)}

What is happening in the game based on these memory changes?<|eot_id|><|start_header_id|>assistant<|end_header_id|>

Based on the memory analysis:

**Game Event**: {description}

**Context Analysis**:
- Game Context: {context}
- Scene: {scene}
- Action Type: {action_type}
- Player Intent: {intent}
- Outcome: {outcome}

**Memory Pattern Analysis**:
The key memory addresses involved in this event are: {', '.join(address_list[:10])}

This memory pattern suggests {context.replace('_', ' ')} behavior, specifically related to {action_type or 'game state changes'}. The addresses show {description.lower()}<|eot_id|>"""

        return prompt
        
    def prepare_dataset(self, training_data: List[Dict[str, Any]]) -> Dataset:
        """Prepare the dataset for training."""
        logger.info("Preparing dataset...")
        
        # Format all samples
        formatted_samples = []
        for sample in training_data:
            try:
                formatted_text = self.format_training_sample(sample)
                formatted_samples.append({"text": formatted_text})
            except Exception as e:
                logger.warning(f"Skipping sample due to formatting error: {e}")
                continue
                
        logger.info(f"Prepared {len(formatted_samples)} formatted samples")
        
        # Create dataset
        dataset = Dataset.from_list(formatted_samples)
        
        # Tokenize dataset
        def tokenize_function(examples):
            tokenized = self.tokenizer(
                examples["text"],
                truncation=True,
                padding=False,
                max_length=2048,  # Adjust based on your needs
                return_overflowing_tokens=False,
            )
            return tokenized
            
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )
        
        logger.info(f"Tokenized dataset created with {len(tokenized_dataset)} samples")
        return tokenized_dataset
        
    def train(self, jsonl_file: str, num_epochs: int = 3, learning_rate: float = 2e-4, 
              batch_size: int = 1, gradient_accumulation_steps: int = 8):
        """Train the model on GBA memory analysis data."""
        logger.info("Starting training process...")
        
        # Setup model and tokenizer
        self.setup_model_and_tokenizer()
        
        # Load and prepare data
        training_data = self.load_training_data(jsonl_file)
        tokenized_dataset = self.prepare_dataset(training_data)
        
        # Configure training arguments
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            warmup_steps=100,
            max_steps=-1,
            learning_rate=learning_rate,
            fp16=False,
            bf16=True,
            logging_steps=10,
            optim="adamw_torch",
            weight_decay=0.001,
            lr_scheduler_type="cosine",
            save_steps=100,
            save_total_limit=3,
            remove_unused_columns=False,
            push_to_hub=False,
            report_to=None,
            dataloader_drop_last=True,
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
        )
        
        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
        )
        
        # Start training
        logger.info("Beginning training...")
        trainer.train()
        
        # Save the final model
        logger.info("Saving trained model...")
        trainer.save_model()
        self.tokenizer.save_pretrained(self.output_dir)
        
        logger.info(f"Training complete! Model saved to {self.output_dir}")
        
    def generate_analysis_prompt(self, query: str) -> str:
        """Generate a prompt for querying the trained model about memory addresses."""
        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a GBA (Game Boy Advance) memory analysis expert. You have been trained on memory patterns from a specific GBA game. Based on your training, you can identify which memory addresses are likely associated with different game mechanics and states.

<|eot_id|><|start_header_id|>user<|end_header_id|>

{query}

Based on your training on this GBA game's memory patterns, which memory addresses would you recommend investigating?<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""


def main():
    """Main training script."""
    parser = argparse.ArgumentParser(
        description="Train Llama 3.1 8B with QLoRA for GBA memory analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic training
  python train_gba_analyzer.py training_data/session.jsonl

  # Custom training parameters
  python train_gba_analyzer.py training_data/session.jsonl \\
    --epochs 5 --learning-rate 1e-4 --batch-size 2

  # Specify output directory
  python train_gba_analyzer.py training_data/session.jsonl \\
    --output-dir ./models/gba-memory-expert
        """
    )
    
    parser.add_argument("jsonl_file", help="Path to JSONL training data file")
    parser.add_argument("--model-name", default="meta-llama/Llama-3.1-8B",
                       help="Hugging Face model name (default: meta-llama/Llama-3.1-8B)")
    parser.add_argument("--output-dir", default="./models/gba-analyzer",
                       help="Output directory for trained model (default: ./models/gba-analyzer)")
    parser.add_argument("--epochs", type=int, default=3,
                       help="Number of training epochs (default: 3)")
    parser.add_argument("--learning-rate", type=float, default=2e-4,
                       help="Learning rate (default: 2e-4)")
    parser.add_argument("--batch-size", type=int, default=1,
                       help="Per-device training batch size (default: 1)")
    parser.add_argument("--gradient-accumulation", type=int, default=8,
                       help="Gradient accumulation steps (default: 8)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Validate input file
    if not Path(args.jsonl_file).exists():
        logger.error(f"Training file not found: {args.jsonl_file}")
        sys.exit(1)
        
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize trainer
    trainer = GBAMemoryAnalysisTrainer(
        model_name=args.model_name,
        output_dir=args.output_dir
    )
    
    try:
        # Start training
        trainer.train(
            jsonl_file=args.jsonl_file,
            num_epochs=args.epochs,
            learning_rate=args.learning_rate,
            batch_size=args.batch_size,
            gradient_accumulation_steps=args.gradient_accumulation
        )
        
        # Print usage example
        print(f"\n{'='*60}")
        print("TRAINING COMPLETE!")
        print(f"{'='*60}")
        print(f"Model saved to: {args.output_dir}")
        print("\nExample queries you can now ask the trained model:")
        print("1. Which addresses are associated with player location and movement?")
        print("2. Which memory locations track enemy health during battle?")
        print("3. Which addresses are used for experience points?")
        print(f"\nTo test the model, use the companion inference script.")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
