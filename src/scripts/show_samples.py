import json
import sys

def show_samples(filename, count=3):
    with open(filename, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= count:
                break
            
            data = json.loads(line)
            print(f"=== SAMPLE {i+1} ===")
            print("PROMPT:")
            print(data['prompt'])
            print("\nCOMPLETION:")
            print(data['completion'])
            print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else 'corrected_windowed.jsonl'
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    show_samples(filename, count)
