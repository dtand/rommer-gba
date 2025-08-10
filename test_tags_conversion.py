#!/usr/bin/env python3
"""
Test script to verify that the tags field conversion and web app integration work correctly.
"""

import json
import os
import requests
import time

def test_annotation_api():
    """Test the annotation API with the new array format."""
    
    # Test data with tags as array
    test_annotation = {
        "frames": [1],
        "annotation": {
            "context": "test_context",
            "scene": "test_scene", 
            "tags": ["test_tag1", "test_tag2", "test_tag3"],
            "description": "Test description",
            "complete": False
        }
    }
    
    try:
        # Start the web app in the background if it's not running
        print("Testing annotation API with array tags...")
        
        # Test the API endpoint
        response = requests.post(
            'http://localhost:5000/api/annotate/da43e02d-1f45-453e-9c65-57b900e38578',
            json=test_annotation,
            timeout=5
        )
        
        if response.status_code == 200:
            print("✓ API successfully accepted array tags")
            
            # Verify the file was written correctly
            annotation_file = "c:/Users/Danimal/Projects/rommer-gba/data/da43e02d-1f45-453e-9c65-57b900e38578/1/annotations.json"
            if os.path.exists(annotation_file):
                with open(annotation_file, 'r') as f:
                    saved_data = json.load(f)
                
                if isinstance(saved_data.get('tags'), list):
                    print("✓ Tags were saved as array:", saved_data['tags'])
                else:
                    print("✗ Tags were not saved as array:", saved_data.get('tags'))
            else:
                print("✗ Annotation file not found")
        else:
            print(f"✗ API returned status {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("ℹ Web app not running - this is expected during offline testing")
        print("To test, run: python run_web_app.py")
    except Exception as e:
        print(f"✗ Error testing API: {e}")

def verify_conversion_sample():
    """Verify a few converted files to ensure the conversion worked."""
    print("\nVerifying converted annotation files...")
    
    base_dir = "c:/Users/Danimal/Projects/rommer-gba/data/da43e02d-1f45-453e-9c65-57b900e38578"
    
    # Check a few files
    test_dirs = [1, 10, 50, 100, 161]
    
    for dir_num in test_dirs:
        annotation_file = os.path.join(base_dir, str(dir_num), "annotations.json")
        if os.path.exists(annotation_file):
            try:
                with open(annotation_file, 'r') as f:
                    data = json.load(f)
                
                tags = data.get('tags')
                if isinstance(tags, list):
                    print(f"✓ Directory {dir_num}: tags are array with {len(tags)} items")
                elif isinstance(tags, str):
                    print(f"✗ Directory {dir_num}: tags are still string: {tags}")
                else:
                    print(f"? Directory {dir_num}: tags field missing or unknown type")
                    
            except Exception as e:
                print(f"✗ Directory {dir_num}: Error reading file: {e}")
        else:
            print(f"- Directory {dir_num}: No annotation file")

if __name__ == "__main__":
    verify_conversion_sample()
    test_annotation_api()
