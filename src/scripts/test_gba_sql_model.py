#!/usr/bin/env python3

"""
Test the trained GBA SQL model with natural language queries
"""

import argparse
import sqlite3
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

class GBASQLInference:
    """Inference class for the trained GBA SQL model."""
    
    def __init__(self, model_path: str, base_model: str = "meta-llama/Llama-3.2-1B"):
        self.model_path = model_path
        self.base_model = base_model
        self.tokenizer = None
        self.model = None
        self.device = None  # Will be set in load_model()
        self.db_path = "gba_training.db"
        
    def load_model(self):
        """Load the fine-tuned model."""
        print(f"Loading model from: {self.model_path}")
        
        # Determine device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load base model
        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            torch_dtype=torch.float16,
            device_map="auto" if torch.cuda.is_available() else None
        )
        
        # Load fine-tuned weights
        self.model = PeftModel.from_pretrained(base_model, self.model_path)
        self.model.eval()
        
        # Ensure model is on correct device
        if not torch.cuda.is_available():
            self.model = self.model.to(self.device)
        
        print("✅ Model loaded successfully!")
    
    def generate_sql(self, question: str, max_length: int = 200) -> str:
        """Generate SQL from natural language question."""
        
        # Format as conversation
        messages = [
            {
                "role": "system",
                "content": """You are an expert SQL assistant specialized in Game Boy Advance memory analysis. 

Database Schema:

Tables:
- sessions: Game sessions
  * session_uuid (TEXT): Unique session identifier
  * created_at (TIMESTAMP): Session creation time

- frame_sets: Individual game frames
  * id (INTEGER): Primary key
  * session_uuid (TEXT): References sessions
  * frame_set_id (INTEGER): Frame number in session
  * timestamp (INTEGER): Frame timestamp
  * buttons (TEXT): Controller input for this frame
  * frames_in_set (TEXT): Frame data
  * created_at (TIMESTAMP): Record creation time

- memory_changes: Memory address value changes
  * id (INTEGER): Primary key
  * session_uuid (TEXT): References sessions
  * frame_set_id (INTEGER): References frame_sets.id
  * region (TEXT): Memory region
  * frame (INTEGER): Frame number when change occurred
  * address (TEXT): Memory address (hex format)
  * prev_val (TEXT): Previous value
  * curr_val (TEXT): Current value
  * freq (INTEGER): Change frequency
  * created_at (TIMESTAMP): Record creation time

- annotations: Human annotations of game events
  * id (INTEGER): Primary key
  * session_uuid (TEXT): References sessions
  * frame_set_id (INTEGER): References frame_sets.id
  * context (TEXT): Game context (battle, menu, dialog, etc.)
  * scene (TEXT): Specific scene identifier
  * tags (TEXT): Comma-separated tags
  * description (TEXT): Human description of what's happening
  * action_type (TEXT): Type of action
  * intent (TEXT): Player intent
  * outcome (TEXT): Result of action
  * created_at (TIMESTAMP): Record creation time

Convert natural language queries into accurate SQL statements for this database."""
            },
            {
                "role": "user",
                "content": question
            }
        ]
        
        # Format conversation for Llama
        conversation = "<|begin_of_text|>"
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "user":
                conversation += f"<|start_header_id|>user<|end_header_id|>\n\n{content}<|eot_id|>"
            elif role == "system":
                conversation += f"<|start_header_id|>system<|end_header_id|>\n\n{content}<|eot_id|>"
                
        conversation += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        
        # Tokenize
        inputs = self.tokenizer(conversation, return_tensors="pt")
        
        # Move inputs to the same device as model
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=100,  # Reduced from 200
                temperature=0.1,
                do_sample=True,
                top_p=0.9,  # Add nucleus sampling
                repetition_penalty=1.2,  # Penalize repetition
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.convert_tokens_to_ids("<|eot_id|>"),
                early_stopping=True  # Stop when EOS is generated
            )
        
        # Decode only the new tokens
        generated = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        
        # Clean up the output - handle multiple common issues
        generated = generated.strip()
        
        # Remove end tokens
        if "<|eot_id|>" in generated:
            generated = generated.split("<|eot_id|>")[0]
        
        # Remove repeated "assistant" tokens and clean up
        lines = generated.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines and lines that are just "assistant"
            if line and line.lower() != "assistant":
                # Remove "assistant" from the beginning or end of lines
                line = line.replace("assistant", "").strip()
                if line:
                    cleaned_lines.append(line)
        
        # Take the first non-empty line as the SQL query
        if cleaned_lines:
            sql = cleaned_lines[0]
            # Additional cleanup
            sql = sql.strip('"\'`')  # Remove quotes/backticks
            return sql
        
        return generated.strip()
    
    def test_sql_validity(self, sql: str) -> tuple[bool, str]:
        """Test if generated SQL is valid and can execute."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            result_count = len(cursor.fetchall())
            conn.close()
            return True, f"✅ Valid SQL - Returns {result_count} rows"
        except Exception as e:
            return False, f"❌ SQL Error: {str(e)}"
    
    def interactive_mode(self):
        """Run interactive query mode."""
        print("=== GBA SQL Model Interactive Mode ===")
        print("Type your questions in natural language, or 'quit' to exit.\n")
        
        while True:
            question = input("🤔 Question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not question:
                continue
            
            print(f"\n🧠 Thinking...")
            sql = self.generate_sql(question)
            print(f"📝 Generated SQL:\n{sql}\n")
            
            # Test validity
            is_valid, message = self.test_sql_validity(sql)
            print(message)
            
            if is_valid:
                # Show sample results
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute(sql)
                    results = cursor.fetchmany(3)
                    
                    if results:
                        print(f"\n📊 Sample results (first 3):")
                        for i, row in enumerate(results, 1):
                            print(f"   {i}. {row}")
                    else:
                        print("   No results returned")
                    
                    conn.close()
                except Exception as e:
                    print(f"   Error executing: {e}")
            
            print("-" * 60)

def main():
    parser = argparse.ArgumentParser(description="Test GBA SQL model")
    parser.add_argument("model_path", help="Path to trained model")
    parser.add_argument("--base-model", default="meta-llama/Llama-3.2-1B", 
                       help="Base model used for training")
    parser.add_argument("--question", help="Single question to test")
    
    args = parser.parse_args()
    
    # Initialize inference
    inference = GBASQLInference(args.model_path, args.base_model)
    inference.load_model()
    
    if args.question:
        # Single question mode
        print(f"Question: {args.question}")
        sql = inference.generate_sql(args.question)
        print(f"Generated SQL: {sql}")
        
        is_valid, message = inference.test_sql_validity(sql)
        print(message)
    else:
        # Interactive mode
        inference.interactive_mode()

if __name__ == "__main__":
    main()
