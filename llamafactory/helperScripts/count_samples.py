#!/usr/bin/env python3
"""
Script to count the number of samples in a ShareGPT format JSON file.
ShareGPT format is a JSON array where each element is a sample with:
- "conversations": array of conversation turns
- "system": optional system message
"""

import json
import sys
import os

def count_samples(file_path):
    """Count the number of samples in a ShareGPT format JSON file."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"Error: Expected JSON array, got {type(data).__name__}.", file=sys.stderr)
            return None
        
        num_samples = len(data)
        print(f"Number of samples: {num_samples}")
        return num_samples
    
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    # Default file path
    default_file = "testsharegptTrace.json"
    
    # Allow file path as command line argument
    file_path = sys.argv[1] if len(sys.argv) > 1 else default_file
    
    count_samples(file_path)
