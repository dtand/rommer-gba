#!/usr/bin/env python3

"""
Test script to validate training data format and training setup
"""

import json
import sys

def validate_training_data(jsonl_file: str):
    """Validate that the training data format matches what train_llm.py expects."""
    
    print(f"Validating training data: {jsonl_file}")
    
    try:
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"📊 Total lines: {len(lines)}")
        
        # Check first few examples
        for i, line in enumerate(lines[:3]):
            try:
                data = json.loads(line.strip())
                
                # Validate structure
                assert "messages" in data, f"Line {i+1}: Missing 'messages' key"
                assert isinstance(data["messages"], list), f"Line {i+1}: 'messages' should be a list"
                assert len(data["messages"]) == 3, f"Line {i+1}: Expected 3 messages (system, user, assistant)"
                
                # Validate message roles
                roles = [msg["role"] for msg in data["messages"]]
                expected_roles = ["system", "user", "assistant"]
                assert roles == expected_roles, f"Line {i+1}: Expected roles {expected_roles}, got {roles}"
                
                # Check content exists
                for j, msg in enumerate(data["messages"]):
                    assert "content" in msg, f"Line {i+1}, message {j}: Missing 'content'"
                    assert len(msg["content"]) > 0, f"Line {i+1}, message {j}: Empty content"
                
                print(f"✅ Line {i+1}: Valid")
                
                # Show sample
                if i == 0:
                    print(f"\n📋 Sample conversation:")
                    for msg in data["messages"]:
                        content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                        print(f"   {msg['role'].upper()}: {content}")
                
            except json.JSONDecodeError as e:
                print(f"❌ Line {i+1}: Invalid JSON - {e}")
                return False
            except AssertionError as e:
                print(f"❌ Line {i+1}: Format error - {e}")
                return False
        
        print(f"\n✅ Training data format is valid!")
        print(f"🎯 Ready for training with src/ml/train_llm.py")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ File not found: {jsonl_file}")
        return False
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def show_training_command(jsonl_file: str):
    """Show the command to run training."""
    print(f"\n🚀 To start training:")
    print(f"   python src/ml/train_llm.py {jsonl_file} --output-dir ./models/gba-sql")
    print(f"\n📋 Optional parameters:")
    print(f"   --epochs 3              # Number of training epochs")
    print(f"   --batch-size 1          # Batch size (1 for low memory)")
    print(f"   --learning-rate 2e-4    # Learning rate")
    print(f"   --gradient-accumulation 8  # Gradient accumulation steps")
    print(f"\n💡 Example with custom settings:")
    print(f"   python src/ml/train_llm.py {jsonl_file} --output-dir ./models/gba-sql --epochs 5 --batch-size 2")

def main():
    jsonl_file = "gba_training_data.jsonl"
    
    if len(sys.argv) > 1:
        jsonl_file = sys.argv[1]
    
    print("=== Training Data Validation ===")
    
    if validate_training_data(jsonl_file):
        show_training_command(jsonl_file)
    else:
        print("\n❌ Please fix the training data format before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
