#!/usr/bin/env python3
"""
Inference script for the trained GBA Memory Analysis model.

This script loads the fine-tuned Llama 3.1 8B model and allows you to query it
about memory address patterns and relationships in the GBA game.

Example queries:
- "Which addresses are associated with player location and movement?"
- "Which memory locations track enemy health during battle?"
- "Which addresses are used for experience points?"
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig
)
from peft import PeftModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GBAMemoryAnalyzer:
    """Inference class for the trained GBA memory analysis model."""
    
    def __init__(self, model_path: str, base_model: str = "meta-llama/Llama-3.1-8B"):
        self.model_path = model_path
        self.base_model = base_model
        self.tokenizer = None
        self.model = None
        
    def load_model(self):
        """Load the fine-tuned model and tokenizer."""
        logger.info("Loading trained GBA memory analysis model...")
        
        # Configure quantization for inference
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=True
        )
        
        # Load base model
        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.bfloat16
        )
        
        # Load LoRA adapter
        self.model = PeftModel.from_pretrained(
            base_model,
            self.model_path,
            torch_dtype=torch.bfloat16
        )
        
        logger.info("Model loaded successfully!")
        
    def generate_analysis_prompt(self, query: str) -> str:
        """Generate a proper prompt for memory analysis queries."""
        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a GBA (Game Boy Advance) memory analysis expert. You have been trained on memory patterns from a specific GBA game. Based on your training, you can identify which memory addresses are likely associated with different game mechanics and states.

<|eot_id|><|start_header_id|>user<|end_header_id|>

{query}

Based on your training on this GBA game's memory patterns, which memory addresses would you recommend investigating?<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        
    def analyze(self, query: str, max_length: int = 512, temperature: float = 0.7) -> str:
        """Analyze a memory-related query and return recommendations."""
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
            
        # Generate prompt
        prompt = self.generate_analysis_prompt(query)
        
        # Tokenize input
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        ).to(self.model.device)
        
        # Generate response
        with torch.no_grad():
            outputs = self.model.generate(
                inputs.input_ids,
                max_new_tokens=max_length,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                top_k=50,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
            
        # Decode response
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the assistant's response
        assistant_start = response.find("<|start_header_id|>assistant<|end_header_id|>")
        if assistant_start != -1:
            assistant_response = response[assistant_start + len("<|start_header_id|>assistant<|end_header_id|>"):].strip()
            return assistant_response
        else:
            return response[len(prompt):].strip()


def main():
    """Main inference script."""
    parser = argparse.ArgumentParser(
        description="Query the trained GBA memory analysis model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python inference_gba_analyzer.py ./models/gba-analyzer

  # Single query
  python inference_gba_analyzer.py ./models/gba-analyzer \\
    --query "Which addresses track player health?"

  # Batch queries from file
  python inference_gba_analyzer.py ./models/gba-analyzer \\
    --queries-file queries.txt
        """
    )
    
    parser.add_argument("model_path", help="Path to the trained model directory")
    parser.add_argument("--base-model", default="meta-llama/Llama-3.1-8B",
                       help="Base model name (default: meta-llama/Llama-3.1-8B)")
    parser.add_argument("--query", "-q", help="Single query to analyze")
    parser.add_argument("--queries-file", help="File containing queries (one per line)")
    parser.add_argument("--max-length", type=int, default=512,
                       help="Maximum response length (default: 512)")
    parser.add_argument("--temperature", type=float, default=0.7,
                       help="Generation temperature (default: 0.7)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Validate model path
    if not Path(args.model_path).exists():
        logger.error(f"Model path not found: {args.model_path}")
        sys.exit(1)
        
    # Initialize analyzer
    analyzer = GBAMemoryAnalyzer(args.model_path, args.base_model)
    
    try:
        # Load the model
        analyzer.load_model()
        
        if args.query:
            # Single query mode
            print(f"\nQuery: {args.query}")
            print("="*60)
            response = analyzer.analyze(args.query, args.max_length, args.temperature)
            print(response)
            
        elif args.queries_file:
            # Batch query mode
            if not Path(args.queries_file).exists():
                logger.error(f"Queries file not found: {args.queries_file}")
                sys.exit(1)
                
            with open(args.queries_file, 'r') as f:
                queries = [line.strip() for line in f if line.strip()]
                
            for i, query in enumerate(queries, 1):
                print(f"\nQuery {i}: {query}")
                print("="*60)
                response = analyzer.analyze(query, args.max_length, args.temperature)
                print(response)
                print()
                
        else:
            # Interactive mode
            print("\n" + "="*60)
            print("GBA Memory Analysis - Interactive Mode")
            print("="*60)
            print("Ask questions about memory addresses and game mechanics.")
            print("Type 'quit' or 'exit' to stop.\n")
            
            example_queries = [
                "Which addresses are associated with player location and movement around the overworld?",
                "Which memory locations can give me information about the enemy party leader's current health during battle?",
                "Which memory locations are likely used to grant the player medal experience points?",
                "What addresses track the player's inventory items?",
                "Which memory locations control battle animations and effects?"
            ]
            
            print("Example queries you can try:")
            for i, example in enumerate(example_queries, 1):
                print(f"{i}. {example}")
            print()
            
            while True:
                try:
                    query = input("Enter your query: ").strip()
                    
                    if query.lower() in ['quit', 'exit', 'q']:
                        break
                        
                    if not query:
                        continue
                        
                    print("\nAnalyzing...")
                    response = analyzer.analyze(query, args.max_length, args.temperature)
                    print(f"\nResponse:\n{response}\n")
                    print("-" * 60)
                    
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                except Exception as e:
                    logger.error(f"Error processing query: {e}")
                    
    except Exception as e:
        logger.error(f"Failed to load or run model: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
