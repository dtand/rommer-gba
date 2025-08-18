import os
import sys
import json
import re
from argparse import ArgumentParser

def normalize_string(s):
    # Only normalize if not already lowercase and underscores
    if not re.fullmatch(r'[a-z_]+', s):
        return re.sub(r'\s+', '_', s.strip()).lower()
    return s

def main():
    parser = ArgumentParser(description="Normalize annotation strings in a session directory.")
    parser.add_argument('session_id', help='Session ID to process')
    args = parser.parse_args()

    base_dir = os.path.join('data', args.session_id)
    if not os.path.isdir(base_dir):
        print(f"Session directory not found: {base_dir}")
        sys.exit(1)

    for frame_dir in os.listdir(base_dir):
        frame_path = os.path.join(base_dir, frame_dir)
        if not os.path.isdir(frame_path):
            continue
        ann_path = os.path.join(frame_path, 'annotations.json')
        if not os.path.isfile(ann_path):
            continue
        with open(ann_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception:
                continue
        changed = False
        changes = []
        # Fields to check
        fields = ['context', 'scene', 'action', 'intent', 'outcome']
        for field in fields:
            val = data.get(field)
            if isinstance(val, str):
                norm = normalize_string(val)
                if norm != val:
                    changes.append(f"{field}: {val} => {norm}")
                    data[field] = norm
                    changed = True
        # Tags array
        if isinstance(data.get('tags'), list):
            for i, tag in enumerate(data['tags']):
                if isinstance(tag, str):
                    norm_tag = normalize_string(tag)
                    if norm_tag != tag:
                        changes.append(f"tag: {tag} => {norm_tag}")
                        data['tags'][i] = norm_tag
                        changed = True
        if changed:
            with open(ann_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"{frame_path}")
            for change in changes:
                print(f"  {change}")

if __name__ == '__main__':
    main()
