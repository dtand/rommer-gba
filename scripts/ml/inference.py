#!/usr/bin/env python3
"""
Simple GBA Memory Analysis Model Inference Script

A clean, straightforward script to load a trained model and run interactive inference.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig
)
from peft import PeftModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GBAInference:
    """Simple inference wrapper for trained GBA memory analysis models."""
    
    def __init__(self, model_path: str, base_model: str = "meta-llama/Llama-3.2-1B"):
        self.model_path = model_path
        self.base_model = base_model
        self.model = None
        self.tokenizer = None
        
    def load_model(self):
        """Load the trained model and tokenizer."""
        logger.info(f"Loading model from: {self.model_path if self.model_path else 'base model only'}")
        
        # Check if path exists (skip for base-only mode)
        if self.model_path and not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model path not found: {self.model_path}")
        
        # 4-bit quantization for memory efficiency
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )
        
        # Load tokenizer (try model path first, then fall back to base model)
        try:
            if self.model_path:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_path,
                    trust_remote_code=True,
                    padding_side="left"  # For inference
                )
            else:
                raise Exception("Using base model tokenizer")
        except:
            # Fallback to base model tokenizer
            logger.info("Loading tokenizer from base model")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.base_model,
                trust_remote_code=True,
                padding_side="left"
            )
        
        # Add pad token if needed
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        # Load base model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.float16
        )
        
        # Load LoRA weights if they exist and not in base-only mode
        if self.model_path:  # Only try to load LoRA if model_path is not empty
            adapter_path = os.path.join(self.model_path, "adapter_model.safetensors")
            if os.path.exists(adapter_path):
                try:
                    logger.info("Loading LoRA adapter weights")
                    self.model = PeftModel.from_pretrained(self.model, self.model_path)
                    logger.info("LoRA adapter loaded successfully")
                except Exception as e:
                    logger.warning(f"Failed to load LoRA adapter: {e}")
                    logger.info("Continuing with base model only")
            else:
                logger.warning("No LoRA adapter found, using base model only")
        else:
            logger.info("Using base model only (no LoRA adapter)")
            
        # Set to eval mode
        self.model.eval()
        logger.info("Model loaded successfully!")
        
    def format_prompt(self, user_input: str) -> str:
        """Format user input for the model."""
        # Use a simpler format that doesn't trigger training patterns
        if "Analyze these GBA memory changes:" in user_input:
            # This is actual memory data to analyze
            enhanced_input = user_input + "\n\nResponse:"
        else:
            # This is a general question - use simple format
            enhanced_input = f"Question: {user_input}\n\nAnswer:"
            
        return enhanced_input
        
    def generate(self, prompt: str, max_length: int = 1024, temperature: float = 0.7) -> str:
        """Generate response from the model."""
        # Format prompt
        formatted_prompt = self.format_prompt(prompt)
        
        # Tokenize
        inputs = self.tokenizer(
            formatted_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024
        ).to(self.model.device)
        
        # Generate with very conservative settings for base model
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=min(max_length, 128),  # Even smaller for stability
                temperature=max(0.1, min(temperature, 0.5)),  # Lower max temperature
                do_sample=temperature > 0.1,
                top_p=0.8,  # More focused
                top_k=40,   # More focused
                repetition_penalty=1.05,  # Very light repetition penalty
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                use_cache=True
            )
        
        # Decode response with safer settings
        response = self.tokenizer.decode(
            outputs[0], 
            skip_special_tokens=True,  # Skip special tokens to avoid garbage
            clean_up_tokenization_spaces=True
        )
        
        # Extract only the assistant's response
        # Look for the answer after the prompt
        if "Answer:" in response:
            parts = response.split("Answer:")
            if len(parts) > 1:
                assistant_response = parts[-1].strip()
            else:
                assistant_response = response.strip()
        elif "Response:" in response:
            parts = response.split("Response:")
            if len(parts) > 1:
                assistant_response = parts[-1].strip()
            else:
                assistant_response = response.strip()
        else:
            # Fallback: use the whole response
            assistant_response = response.strip()
        
        # Clean up the response - remove any leftover prompt text
        prompt_text = self.tokenizer.decode(inputs['input_ids'][0], skip_special_tokens=True)
        if prompt_text in assistant_response:
            assistant_response = assistant_response.replace(prompt_text, "").strip()
        
        # Remove common artifacts
        assistant_response = assistant_response.replace("Question:", "")
        assistant_response = assistant_response.replace("Answer:", "")
        assistant_response = assistant_response.replace("Response:", "")
        
        # Clean up the response
        assistant_response = assistant_response.replace("<|end_of_text|>", "")
        assistant_response = assistant_response.replace("<|eot_id|>", "")
        
        # Remove any remaining special tokens or malformed content
        import re
        assistant_response = re.sub(r'<\|[^|]*\|>', '', assistant_response)
        assistant_response = re.sub(r'<[^>]*>', '', assistant_response)
        
        # Check if response was truncated
        generated_tokens = len(outputs[0]) - len(inputs['input_ids'][0])
        if generated_tokens >= min(max_length, 128) - 5:  # Close to limit
            assistant_response += "\n\n[Response may be truncated - try increasing --max-length]"
            
        return assistant_response.strip()


def interactive_mode(inference):
    """Run interactive prompting session."""
    print("\n🎮 GBA Memory Analysis Model - Interactive Mode")
    print("=" * 50)
    print("Enter your prompts below. Type 'quit' or 'exit' to stop.")
    print("For GBA memory analysis, try prompts like:")
    print("  'Analyze these GBA memory changes: [your JSON data here]'")
    print("  'What do these memory changes represent?'")
    print("  'Describe this game event: [your data]'")
    print("Note: The model will provide concise descriptions without repeating addresses.")
    print("-" * 50)
    
    while True:
        try:
            # Get user input
            user_input = input("\n💬 You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
                
            if not user_input:
                continue
                
            # Generate response
            print("\n🤖 Assistant: ", end="", flush=True)
            response = inference.generate(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def single_prompt_mode(inference, prompt: str):
    """Run a single prompt and exit."""
    print(f"\n💬 Prompt: {prompt}")
    print("-" * 50)
    response = inference.generate(prompt)
    print(f"🤖 Response: {response}")


def main():
    parser = argparse.ArgumentParser(description="GBA Memory Analysis Model Inference")
    parser.add_argument("model_path", help="Path to trained model directory")
    parser.add_argument("--base-model", default="meta-llama/Llama-3.2-1B",
                       help="Base model name (default: meta-llama/Llama-3.2-1B)")
    parser.add_argument("--prompt", help="Single prompt to run (non-interactive)")
    parser.add_argument("--max-length", type=int, default=1024,
                       help="Maximum response length (default: 1024)")
    parser.add_argument("--temperature", type=float, default=0.3,
                       help="Generation temperature (default: 0.3 for more focused responses)")
    parser.add_argument("--base-only", action="store_true",
                       help="Use only the base model without LoRA adapter")
    
    args = parser.parse_args()
    
    # If base-only mode, skip model path validation
    if not args.base_only and not os.path.exists(args.model_path):
        logger.error(f"Model path not found: {args.model_path}")
        sys.exit(1)
        
    try:
        # Initialize inference
        if args.base_only:
            # Use base model directly
            inference = GBAInference("", args.base_model)  # Empty path for base-only
            inference.model_path = ""  # Override to skip LoRA loading
        else:
            inference = GBAInference(args.model_path, args.base_model)
        
        inference.load_model()
        
        # Run inference
        if args.prompt:
            # Single prompt mode
            single_prompt_mode(inference, args.prompt)
        else:
            # Interactive mode
            interactive_mode(inference)
            
    except Exception as e:
        logger.error(f"❌ Inference failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
