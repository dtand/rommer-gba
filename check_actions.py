import json

with open('training_data/98cc9f85-0567-4392-8b0e-636a8d65b3a2-full.jsonl', 'r') as f:
    lines = f.readlines()

action_count = 0
total_count = 0
sample_with_action = None

for line in lines[:200]:
    sample = json.loads(line)
    total_count += 1
    
    if sample['outputs']['action_type']:
        action_count += 1
        if not sample_with_action:
            sample_with_action = sample

print(f"Found {action_count} samples with action_type out of {total_count} samples checked")

if sample_with_action:
    print("\nSample with action data:")
    print(json.dumps(sample_with_action['outputs'], indent=2))
else:
    print("No samples with action_type found in first 200 samples")
