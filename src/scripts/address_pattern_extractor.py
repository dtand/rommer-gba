#!/usr/bin/env python3
"""
Memory Address Pattern Extractor
Analyzes the model's responses to extract useful memory address patterns.
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import logging
import json
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_model():
    """Load the trained model and tokenizer."""
    model_path = "./models/gba-analyzer-llama-1b"
    base_model_name = "meta-llama/Llama-3.2-1B"
    
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )
    
    model = PeftModel.from_pretrained(base_model, model_path)
    model = model.merge_and_unload()
    
    return model, tokenizer

def ask_focused_questions(model, tokenizer):
    """Ask very specific questions about memory address patterns."""
    
    questions = [
        "List the memory addresses that change when a player moves in the overworld.",
        "What memory addresses decrease when an enemy takes damage in battle?", 
        "Which memory addresses increase when a player gains experience points?",
        "What memory addresses change when navigating through menus?",
        "List memory addresses associated with player health changes.",
        "What memory addresses indicate battle start and end states?",
        "Which memory addresses change when items are used?",
        "List addresses that change when buttons are pressed for movement."
    ]
    
    print("🔍 Focused Memory Address Analysis")
    print("=" * 60)
    
    all_findings = {}
    
    for i, question in enumerate(questions, 1):
        print(f"\n📋 Question {i}: {question}")
        
        try:
            # Simple direct prompt
            prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
            
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=200,
                    temperature=0.3,  # Lower temperature for more focused responses
                    top_p=0.8,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    repetition_penalty=1.2
                )
            
            generated_text = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
            response = generated_text.strip()
            
            # Clean up response
            if 'assistant' in response:
                response = response.split('assistant')[0].strip()
            
            print(f"🤖 Response: {response[:200]}...")
            
            # Extract memory addresses
            addresses = re.findall(r'03[0-9A-Fa-f]{6}', response)
            unique_addresses = list(set(addresses))
            
            if unique_addresses:
                print(f"🎯 Found addresses: {', '.join(unique_addresses)}")
                all_findings[question] = {
                    "addresses": unique_addresses,
                    "full_response": response
                }
            else:
                print("⚠️ No specific addresses found")
                all_findings[question] = {
                    "addresses": [],
                    "full_response": response
                }
                
        except Exception as e:
            print(f"❌ Error: {e}")
            
        print("-" * 50)
    
    return all_findings

def summarize_findings(findings):
    """Summarize the address findings by category."""
    
    print("\n📊 MEMORY ADDRESS PATTERN SUMMARY")
    print("=" * 60)
    
    # Collect all unique addresses
    all_addresses = set()
    address_contexts = {}
    
    for question, data in findings.items():
        for addr in data['addresses']:
            all_addresses.add(addr)
            if addr not in address_contexts:
                address_contexts[addr] = []
            address_contexts[addr].append(question)
    
    print(f"🎯 Total unique addresses found: {len(all_addresses)}")
    print()
    
    # Group by address ranges
    address_ranges = {}
    for addr in all_addresses:
        range_key = addr[:6]  # First 6 characters (e.g., "030001")
        if range_key not in address_ranges:
            address_ranges[range_key] = []
        address_ranges[range_key].append(addr)
    
    print("📍 Addresses by Memory Range:")
    for range_key, addresses in sorted(address_ranges.items()):
        print(f"  {range_key}xxxx: {len(addresses)} addresses")
        for addr in sorted(addresses):
            contexts = address_contexts[addr]
            print(f"    • {addr} - Associated with: {', '.join(contexts[:2])}{'...' if len(contexts) > 2 else ''}")
    
    print()
    
    # Most frequently mentioned addresses
    addr_frequency = {}
    for addr in all_addresses:
        addr_frequency[addr] = len(address_contexts[addr])
    
    top_addresses = sorted(addr_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
    
    print("🔥 Most Frequently Mentioned Addresses:")
    for addr, freq in top_addresses:
        contexts = address_contexts[addr]
        print(f"  {addr} ({freq} contexts): {', '.join(contexts)}")
    
    return {
        "total_addresses": len(all_addresses),
        "address_ranges": address_ranges,
        "top_addresses": top_addresses,
        "address_contexts": address_contexts
    }

def interactive_address_finder(model, tokenizer):
    """Interactive tool to find specific addresses."""
    print("\n🔍 Interactive Address Finder")
    print("=" * 40)
    print("Ask specific questions about memory addresses.")
    print("Examples:")
    print("- 'What address controls player X coordinate?'")
    print("- 'Which address shows current health?'")
    print("- 'What addresses change during menu navigation?'")
    print("\nType 'quit' to exit.\n")
    
    while True:
        try:
            question = input("Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
                
            if not question:
                continue
            
            prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
            
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=150,
                    temperature=0.3,
                    top_p=0.8,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    repetition_penalty=1.2
                )
            
            generated_text = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
            response = generated_text.strip()
            
            if 'assistant' in response:
                response = response.split('assistant')[0].strip()
            
            print(f"\n🤖 Response: {response}")
            
            # Extract addresses
            addresses = re.findall(r'03[0-9A-Fa-f]{6}', response)
            unique_addresses = list(set(addresses))
            
            if unique_addresses:
                print(f"🎯 Addresses found: {', '.join(unique_addresses)}")
            else:
                print("⚠️ No specific addresses identified")
            
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main function."""
    print("🎮 Memory Address Pattern Extractor")
    print("Extracting specific memory address patterns from your trained model")
    print()
    
    try:
        model, tokenizer = load_model()
        print("✅ Model loaded successfully!")
        
        # Ask focused questions
        findings = ask_focused_questions(model, tokenizer)
        
        # Summarize findings
        summary = summarize_findings(findings)
        
        # Save results
        results = {
            "findings": findings,
            "summary": summary
        }
        
        with open("address_patterns.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: address_patterns.json")
        
        # Interactive session
        choice = input("\nWould you like to ask custom questions about specific addresses? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            interactive_address_finder(model, tokenizer)
        
        print("\n🎉 Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
