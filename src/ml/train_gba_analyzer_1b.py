#!/usr/bin/env python3
"""
GBA Memory Analysis Model Training Script (Llama 3.2 1B Optimized)

This script trains a Llama 3.2 1B model using QLoRA to understand relationships 
between GBA memory changes and game semantics. Optimized for RTX 2070 Super.

Estimated training time: 1-3 hours (vs 120+ hours for 8B model)
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gba_training_1b.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class GBAMemoryAnalysisTrainer:
    """Trainer for GBA memory analysis using Llama 3.2 1B with QLoRA."""
    
    def __init__(self, model_name: str = "meta-llama/Llama-3.2-1B", max_length: int = 1024):
        self.model_name = model_name
        self.max_length = max_length
        self.model = None
        self.tokenizer = None
        
    def setup_model_and_tokenizer(self):
        """Initialize the model and tokenizer with QLoRA configuration."""
        logger.info("Setting up model and tokenizer...")
        
        # Configure 4-bit quantization (lighter for 1B model)
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16  # float16 is fine for 1B
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
            torch_dtype=torch.float16
        )
        
        # Prepare model for k-bit training
        self.model = prepare_model_for_kbit_training(self.model)
        
        # Configure LoRA (smaller config for 1B model)
        lora_config = LoraConfig(
            r=8,  # Reduced from 16 for 1B model
            lora_alpha=16,  # Reduced from 32
            target_modules=[
                "q_proj", "v_proj", "k_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"
            ],
            lora_dropout=0.1,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )
        
        # Apply LoRA
        self.model = get_peft_model(self.model, lora_config)
        
        logger.info("Model and tokenizer setup complete")
        
        # Print trainable parameters
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        all_params = sum(p.numel() for p in self.model.parameters())
        logger.info(f"Trainable parameters: {trainable_params:,}")
        logger.info(f"Total parameters: {all_params:,}")
        logger.info(f"Trainable %: {100 * trainable_params / all_params:.2f}%")

    def load_training_data(self, jsonl_path: str) -> List[Dict]:
        """Load training data from JSONL file."""
        logger.info(f"Loading training data from {jsonl_path}")
        
        data = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line.strip())
                    data.append(entry)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                    continue
                    
        logger.info(f"Loaded {len(data)} training samples")
        return data
    
    def format_training_example(self, example: Dict) -> str:
        """Format a training example into a conversational prompt."""
        inputs = example.get('inputs', {})
        outputs = example.get('outputs', {})
        
        # Extract memory changes
        memory_changes = inputs.get('memory_changes', [])
        buttons = inputs.get('buttons', [])
        
        # Format memory changes
        memory_text = []
        for change in memory_changes[:5]:  # Limit to 5 changes to save tokens
            addr = change.get('address', 'Unknown')
            prev_val = change.get('prev_val', 'Unknown')
            curr_val = change.get('curr_val', 'Unknown')
            memory_text.append(f"Address {addr}: {prev_val} → {curr_val}")
        
        memory_str = "\n".join(memory_text) if memory_text else "No memory changes detected"
        buttons_str = ", ".join(buttons) if buttons else "No buttons pressed"
        
        # Create conversation format
        user_prompt = f"""Analyze these GBA memory changes and button inputs:

Memory Changes:
{memory_str}

Buttons: {buttons_str}

What is happening in the game? Provide context, scene, description, action type, intent, and outcome."""

        assistant_response = f"""Context: {outputs.get('context', 'unknown')}
Scene: {outputs.get('scene', 'unknown')}
Description: {outputs.get('description', 'No description available')}
Action Type: {outputs.get('action_type', 'unknown')}
Intent: {outputs.get('intent', 'unknown')}
Outcome: {outputs.get('outcome', 'unknown')}"""

        # Format as conversation (Llama format)
        conversation = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{assistant_response}<|eot_id|>"
        
        return conversation

    def prepare_dataset(self, data: List[Dict]) -> Dataset:
        """Prepare the dataset for training."""
        logger.info("Preparing dataset...")
        
        # Format all examples
        formatted_examples = []
        for example in data:
            formatted_text = self.format_training_example(example)
            formatted_examples.append({"text": formatted_text})
        
        logger.info(f"Prepared {len(formatted_examples)} formatted samples")
        
        # Create dataset
        dataset = Dataset.from_list(formatted_examples)
        
        # Tokenize
        def tokenize_function(examples):
            tokenized = self.tokenizer(
                examples["text"],
                truncation=True,
                padding=False,
                max_length=self.max_length,
                return_overflowing_tokens=False,
            )
            tokenized["labels"] = tokenized["input_ids"].copy()
            return tokenized
        
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names,
        )
        
        logger.info(f"Tokenized dataset created with {len(tokenized_dataset)} samples")
        return tokenized_dataset

    def train(self, dataset: Dataset, output_dir: str, epochs: int = 3, 
              learning_rate: float = 2e-4, batch_size: int = 2, 
              gradient_accumulation_steps: int = 4):
        """Train the model."""
        
        # Training arguments optimized for 1B model
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            warmup_steps=50,  # Reduced warmup
            max_steps=-1,
            learning_rate=learning_rate,
            fp16=True,  # Use fp16 instead of bf16 for better compatibility
            logging_steps=10,
            optim="paged_adamw_8bit",
            save_strategy="steps",
            save_steps=100,  # Save more frequently
            eval_strategy="no",
            do_eval=False,
            report_to=None,
            run_name=f"gba-memory-analysis-1b-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            push_to_hub=False,
            hub_private_repo=True,
            remove_unused_columns=False,
            dataloader_pin_memory=False,
            gradient_checkpointing=True,
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
            train_dataset=dataset,
            data_collator=data_collator,
        )
        
        # Start training
        logger.info("Beginning training...")
        trainer.train()
        
        # Save final model
        logger.info("Saving final model...")
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        logger.info(f"Training complete! Model saved to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Train GBA Memory Analysis Model (Llama 3.2 1B)")
    parser.add_argument("jsonl_file", help="Path to JSONL training data file")
    parser.add_argument("--model-name", default="meta-llama/Llama-3.2-1B", 
                       help="Model name (default: meta-llama/Llama-3.2-1B)")
    parser.add_argument("--output-dir", default="./models/gba-analyzer-1b", 
                       help="Output directory for trained model")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--learning-rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size")
    parser.add_argument("--gradient-accumulation", type=int, default=4, 
                       help="Gradient accumulation steps")
    parser.add_argument("--max-length", type=int, default=1024, 
                       help="Maximum sequence length (reduced for 1B model)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if JSONL file exists
    if not os.path.exists(args.jsonl_file):
        logger.error(f"Training data file not found: {args.jsonl_file}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize trainer
    trainer = GBAMemoryAnalysisTrainer(
        model_name=args.model_name,
        max_length=args.max_length
    )
    
    try:
        # Setup model
        trainer.setup_model_and_tokenizer()
        
        # Load and prepare data
        training_data = trainer.load_training_data(args.jsonl_file)
        dataset = trainer.prepare_dataset(training_data)
        
        # Train model
        trainer.train(
            dataset=dataset,
            output_dir=args.output_dir,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            batch_size=args.batch_size,
            gradient_accumulation_steps=args.gradient_accumulation
        )
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
