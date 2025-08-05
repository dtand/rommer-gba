#!/usr/bin/env python3
"""
Utility script to view training samples from JSONL files with pretty printing.
"""

import argparse
import json
import sys
from pathlib import Path


def view_samples(jsonl_file: str, sample_indices: list = None, max_samples: int = 5):
    """
    View training samples with pretty printing.
    
    Args:
        jsonl_file: Path to the JSONL training file
        sample_indices: Specific sample indices to view (0-based)
        max_samples: Maximum number of samples to show if no indices specified
    """
    if not Path(jsonl_file).exists():
        print(f"Error: File not found: {jsonl_file}")
        return
        
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    total_samples = len(lines)
    print(f"=== TRAINING FILE: {jsonl_file} ===")
    print(f"Total samples: {total_samples}")
    print()
    
    if sample_indices:
        # View specific samples
        for i, idx in enumerate(sample_indices):
            if 0 <= idx < total_samples:
                print(f"=== SAMPLE {idx} ===")
                sample = json.loads(lines[idx])
                print(json.dumps(sample, indent=2, ensure_ascii=False))
                if i < len(sample_indices) - 1:
                    print("\n" + "="*50 + "\n")
            else:
                print(f"Warning: Sample index {idx} out of range (0-{total_samples-1})")
    else:
        # View first max_samples
        for i in range(min(max_samples, total_samples)):
            print(f"=== SAMPLE {i} ===")
            sample = json.loads(lines[i])
            print(json.dumps(sample, indent=2, ensure_ascii=False))
            if i < min(max_samples, total_samples) - 1:
                print("\n" + "="*50 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="View training samples from JSONL files with pretty printing"
    )
    
    parser.add_argument("jsonl_file", help="Path to the JSONL training file")
    parser.add_argument("--samples", "-s", nargs='+', type=int,
                       help="Specific sample indices to view (0-based)")
    parser.add_argument("--max", "-m", type=int, default=5,
                       help="Maximum samples to show if no specific indices (default: 5)")
    
    args = parser.parse_args()
    
    view_samples(args.jsonl_file, args.samples, args.max)


if __name__ == "__main__":
    main()
