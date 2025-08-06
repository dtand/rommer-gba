#!/usr/bin/env python3
"""
Memory Address Pattern Analyzer
Uses the trained model to identify patterns between memory addresses and game mechanics.
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_model():
    """Load the trained model and tokenizer."""
    model_path = "./models/gba-analyzer-ewram-description"
    base_model_name = "meta-llama/Llama-3.2-1B"
    
    logger.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    logger.info("Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )
    
    logger.info("Loading LoRA adapter...")
    model = PeftModel.from_pretrained(base_model, model_path)
    model = model.merge_and_unload()
    
    return model, tokenizer

def analyze_memory_patterns(model, tokenizer):
    """Ask the model to analyze memory address patterns."""
    
    pattern_questions = [
        {
            "category": "Player Movement",
            "question": "Which memory addresses are most likely associated with player coordinates in the overworld? Look for addresses that change when the player moves around the map.",
            "context": "Player movement should show consistent changes in specific memory addresses when directional buttons are pressed."
        },
        {
            "category": "Enemy Health",
            "question": "Which memory addresses are most likely associated with enemy health during battle? Look for addresses that decrease when enemies take damage.",
            "context": "Enemy health addresses should show decreasing values when enemies are attacked."
        },
        {
            "category": "Player Stats",
            "question": "Which memory address is most likely associated with player experience points? Look for addresses that increase after battles or completing actions.",
            "context": "Experience points should increase after successful battles or quest completion."
        },
        {
            "category": "Button Mapping",
            "question": "Which buttons are used to navigate the player around the overworld? Look for button patterns associated with movement.",
            "context": "Movement buttons should correlate with coordinate changes in overworld scenarios."
        },
        {
            "category": "Battle State",
            "question": "Which memory addresses indicate when a battle is starting or ending? Look for addresses that change state during battle transitions.",
            "context": "Battle state addresses should show distinct patterns when transitioning between overworld and battle modes."
        },
        {
            "category": "Menu Navigation",
            "question": "Which memory addresses are associated with menu navigation and selection? Look for addresses that change when navigating menus.",
            "context": "Menu addresses should change when different menu options are selected or highlighted."
        }
    ]
    
    print("🔍 Memory Address Pattern Analysis")
    print("=" * 60)
    print("Asking the trained model to identify patterns between memory addresses and game mechanics...")
    print()
    
    results = []
    
    for i, item in enumerate(pattern_questions, 1):
        print(f"📋 Analysis {i}: {item['category']}")
        print(f"Question: {item['question']}")
        print()
        
        try:
            # Format the prompt with context
            prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are a GBA memory analysis expert. Based on the training data you've seen, analyze patterns between memory addresses and game mechanics.\n\nContext: {item['context']}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{item['question']}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
            
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
            
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            print("🤖 Analyzing patterns...")
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=300,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    repetition_penalty=1.1
                )
            
            generated_text = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
            
            # Clean up the response
            response = generated_text.strip()
            if 'assistant' in response:
                response = response.split('assistant')[0].strip()
            
            print(f"📊 Pattern Analysis:\n{response}")
            
            # Extract potential memory addresses mentioned
            import re
            addresses = re.findall(r'03[0-9A-Fa-f]{6}', response)
            unique_addresses = list(set(addresses))
            
            results.append({
                "category": item['category'],
                "question": item['question'],
                "response": response,
                "mentioned_addresses": unique_addresses
            })
            
            if unique_addresses:
                print(f"\n🎯 Memory Addresses Mentioned: {', '.join(unique_addresses)}")
            else:
                print("\n⚠️ No specific memory addresses identified in response")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                "category": item['category'],
                "error": str(e)
            })
        
        print("\n" + "-" * 60)
    
    return results

def interactive_address_query(model, tokenizer):
    """Interactive session for querying specific memory address patterns."""
    print("\n🔍 Interactive Memory Address Query")
    print("=" * 50)
    print("Ask questions about memory address patterns based on your training data.")
    print("Examples:")
    print("- 'What addresses change when the player moves left?'")
    print("- 'Which addresses are related to item inventory?'")
    print("- 'What memory ranges control battle mechanics?'")
    print("\nType 'quit' to exit.\n")
    
    while True:
        try:
            user_question = input("Your question: ").strip()
            
            if user_question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
                
            if not user_question:
                continue
            
            # Format the prompt
            prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are a GBA memory analysis expert. Based on the training data you've seen, help identify patterns between memory addresses and game mechanics.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user_question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
            
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
            
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            print("\n🤖 Analyzing...")
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=250,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    repetition_penalty=1.1
                )
            
            generated_text = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
            
            # Clean up the response
            response = generated_text.strip()
            if 'assistant' in response:
                response = response.split('assistant')[0].strip()
            
            print(f"\n📊 Analysis:\n{response}")
            
            # Extract memory addresses
            import re
            addresses = re.findall(r'03[0-9A-Fa-f]{6}', response)
            unique_addresses = list(set(addresses))
            
            if unique_addresses:
                print(f"\n🎯 Mentioned Addresses: {', '.join(unique_addresses)}")
            
            print("\n" + "=" * 50)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again.\n")

def main():
    """Main function."""
    print("🎮 GBA Memory Address Pattern Analyzer")
    print("Using your trained model to identify memory address patterns")
    print()
    
    try:
        model, tokenizer = load_model()
        print("✅ Model loaded successfully!")
        
        # Run pattern analysis
        results = analyze_memory_patterns(model, tokenizer)
        
        # Save results
        with open("memory_pattern_analysis.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Analysis results saved to: memory_pattern_analysis.json")
        
        # Offer interactive session
        choice = input("\nWould you like to ask custom questions about memory patterns? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            interactive_address_query(model, tokenizer)
        
        print("\n🎉 Pattern analysis complete!")
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")

if __name__ == "__main__":
    main()
