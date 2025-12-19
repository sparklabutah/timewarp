#!/usr/bin/env python3
"""Debug script to examine trace file structure."""
import json
import zipfile
from pathlib import Path

trace_zip = 'my_agent_task_trace.zip'

print("=== Examining trace.zip file ===\n")

# List contents
with zipfile.ZipFile(trace_zip, 'r') as z:
    files = z.namelist()
    print(f"Files in zip ({len(files)} total):")
    for i, f in enumerate(files[:20]):
        print(f"  {i+1}. {f}")
    if len(files) > 20:
        print(f"  ... and {len(files) - 20} more files")

print("\n=== Examining trace.trace file ===\n")

# Extract and examine trace.trace
with zipfile.ZipFile(trace_zip, 'r') as z:
    trace_content = z.read('trace.trace').decode('utf-8')
    
    lines = trace_content.strip().split('\n')
    print(f"Total lines in trace.trace: {len(lines)}")
    
    print("\n--- First 5 lines (first 500 chars each) ---")
    for i, line in enumerate(lines[:5]):
        if line.strip():
            try:
                data = json.loads(line)
                print(f"\nLine {i+1}:")
                print(f"  Type: {data.get('type', 'N/A')}")
                print(f"  Method: {data.get('method', 'N/A')}")
                if 'metadata' in data:
                    print(f"  Metadata keys: {list(data['metadata'].keys())}")
                print(f"  Raw (first 500 chars): {line[:500]}")
            except json.JSONDecodeError:
                print(f"\nLine {i+1}: (Not valid JSON)")
                print(f"  Content: {line[:200]}")
    
    print("\n--- Searching for action events ---")
    action_count = 0
    for i, line in enumerate(lines):
        if line.strip():
            try:
                data = json.loads(line)
                if data.get('type') == 'action':
                    action_count += 1
                    print(f"\nAction {action_count} (line {i+1}):")
                    print(f"  {json.dumps(data, indent=2)[:500]}")
                    if action_count >= 3:
                        break
            except:
                pass
    
    if action_count == 0:
        print("No action events found with type='action'")
        print("\n--- Checking all event types ---")
        event_types = {}
        for line in lines:
            if line.strip():
                try:
                    data = json.loads(line)
                    event_type = data.get('type', 'unknown')
                    event_types[event_type] = event_types.get(event_type, 0) + 1
                except:
                    pass
        
        print(f"Event type counts:")
        for event_type, count in sorted(event_types.items()):
            print(f"  {event_type}: {count}")

print("\n=== Done ===")

