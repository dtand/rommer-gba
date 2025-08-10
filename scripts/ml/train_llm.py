#!/usr/bin/env python3
"""
Simple GBA Memory Analysis Model Training Script

A clean, straightforward script to train Llama 3.2 1B on GBA memory analysis data.
Uses the standard messages format and QLoRA for efficient training.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict

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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleGBATrainer:
    """Simple trainer for GBA memory analysis using Llama 3.2 1B with QLoRA."""
    
    def __init__(self, model_name: str = "meta-llama/Llama-3.2-1B"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        
    def setup_model(self):
        """Setup model and tokenizer with quantization."""
        logger.info(f"Loading model: {self.model_name}")
        
        # 4-bit quantization config
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            padding_side="right"
        )
        
        # Add pad token if needed
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
        
        # Prepare for training
        self.model = prepare_model_for_kbit_training(self.model)
        
        # LoRA config for 1B model
        lora_config = LoraConfig(
            r=8,
            lora_alpha=16,
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
        
        # Log trainable parameters
        trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.model.parameters())
        logger.info(f"Trainable parameters: {trainable:,} ({100 * trainable / total:.2f}%)")
        
    def load_data(self, jsonl_file: str) -> List[Dict]:
        """Load training data from JSONL file."""
        logger.info(f"Loading data from: {jsonl_file}")
        
        data = []
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line.strip())
                    data.append(entry)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                    
        logger.info(f"Loaded {len(data)} training samples")
        return data
        
    def format_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to Llama chat format."""
        conversation = "<|begin_of_text|>"
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "user":
                conversation += f"<|start_header_id|>user<|end_header_id|>\n\n{content}<|eot_id|>"
            elif role == "assistant":
                conversation += f"<|start_header_id|>assistant<|end_header_id|>\n\n{content}<|eot_id|>"
                
        return conversation
        
    def prepare_dataset(self, data: List[Dict]) -> Dataset:
        """Prepare dataset for training."""
        logger.info("Preparing dataset...")
        
        # Format conversations
        formatted_data = []
        for entry in data:
            conversation = self.format_conversation(entry["messages"])
            formatted_data.append({"text": conversation})
            
        # Create dataset
        dataset = Dataset.from_list(formatted_data)
        
        # Tokenization function
        def tokenize_function(examples):
            tokenized = self.tokenizer(
                examples["text"],
                truncation=True,
                padding=False,
                max_length=1024,  # Keep sequences manageable for 1B model
                return_tensors=None
            )
            # For causal LM, labels are the same as input_ids
            tokenized["labels"] = tokenized["input_ids"].copy()
            return tokenized
        
        # Apply tokenization
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names,
            desc="Tokenizing"
        )
        
        logger.info(f"Prepared {len(tokenized_dataset)} tokenized samples")
        return tokenized_dataset
        
    def train(self, dataset: Dataset, output_dir: str, **kwargs):
        """Train the model."""
        logger.info("Starting training...")
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=kwargs.get('epochs', 3),
            per_device_train_batch_size=kwargs.get('batch_size', 1),
            gradient_accumulation_steps=kwargs.get('gradient_accumulation', 8),
            warmup_steps=kwargs.get('warmup_steps', 50),
            learning_rate=kwargs.get('learning_rate', 2e-4),
            fp16=True,
            logging_steps=10,
            save_steps=500,
            save_total_limit=2,
            remove_unused_columns=False,
            dataloader_pin_memory=False,
            gradient_checkpointing=True,
            optim="paged_adamw_8bit",
            report_to="none",
            run_name="gba-simple-training"
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False  # Causal LM, not masked LM
        )
        
        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer
        )
        
        # Train
        trainer.train()
        
        # Save model
        logger.info(f"Saving model to: {output_dir}")
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        logger.info("Training complete!")


def main():
    parser = argparse.ArgumentParser(description="Simple GBA Memory Analysis Training")
    parser.add_argument("jsonl_file", help="Path to JSONL training file")
    parser.add_argument("--output-dir", default="./models/gba-simple", 
                       help="Output directory (default: ./models/gba-simple)")
    parser.add_argument("--model", default="meta-llama/Llama-3.2-1B",
                       help="Base model (default: meta-llama/Llama-3.2-1B)")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs (default: 3)")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size (default: 1)")
    parser.add_argument("--learning-rate", type=float, default=2e-4, help="Learning rate (default: 2e-4)")
    parser.add_argument("--gradient-accumulation", type=int, default=8, 
                       help="Gradient accumulation steps (default: 8)")
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.jsonl_file):
        logger.error(f"Training file not found: {args.jsonl_file}")
        sys.exit(1)
        
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize trainer
    trainer = SimpleGBATrainer(args.model)
    
    try:
        # Setup
        trainer.setup_model()
        
        # Load and prepare data
        data = trainer.load_data(args.jsonl_file)
        dataset = trainer.prepare_dataset(data)
        
        # Train
        trainer.train(
            dataset=dataset,
            output_dir=args.output_dir,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            gradient_accumulation=args.gradient_accumulation
        )
        
        logger.info(f"✅ Training successful! Model saved to: {args.output_dir}")
        
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
