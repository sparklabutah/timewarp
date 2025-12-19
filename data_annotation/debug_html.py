#!/usr/bin/env python3
"""Debug script to examine HTML in trace snapshots."""
import json
import zipfile
from pathlib import Path

trace_zip = 'my_agent_task_trace.zip'

print("=== Examining HTML snapshots in trace ===\n")

# Extract and examine trace.trace
with zipfile.ZipFile(trace_zip, 'r') as z:
    trace_content = z.read('trace.trace').decode('utf-8')
    
    lines = trace_content.strip().split('\n')
    
    print("--- Looking for frame-snapshot events ---\n")
    snapshot_count = 0
    for i, line in enumerate(lines):
        if line.strip():
            try:
                data = json.loads(line)
                if data.get('type') == 'frame-snapshot':
                    snapshot_count += 1
                    snapshot = data.get('snapshot', {})
                    snapshot_name = snapshot.get('snapshotName', '')
                    frame_url = snapshot.get('frameUrl', '')
                    html_data = snapshot.get('html', [])
                    
                    print(f"\nSnapshot {snapshot_count}: {snapshot_name}")
                    print(f"  Frame URL: {frame_url}")
                    print(f"  HTML data type: {type(html_data)}")
                    print(f"  HTML data length: {len(str(html_data))}")
                    
                    if html_data:
                        # Show first part of HTML array
                        html_str = str(html_data)
                        print(f"  HTML preview (first 500 chars): {html_str[:500]}")
                        
                        # Try to see if it's a real page or blank
                        if 'about:blank' in frame_url or (isinstance(html_data, list) and len(html_data) < 5):
                            print(f"  ⚠️  This looks like a blank page")
                        else:
                            print(f"  ✓ This looks like a real page")
                    
                    if snapshot_count >= 5:
                        break
            except Exception as e:
                pass
    
    print(f"\n\nTotal frame-snapshot events found: {snapshot_count}")
    
    # Also check for after snapshots
    print("\n--- Looking for 'after' events with afterSnapshot ---\n")
    after_count = 0
    for i, line in enumerate(lines):
        if line.strip():
            try:
                data = json.loads(line)
                if data.get('type') == 'after':
                    after_snapshot = data.get('afterSnapshot', '')
                    if after_snapshot:
                        after_count += 1
                        print(f"After event {after_count}: {after_snapshot}")
                        if after_count >= 5:
                            break
            except:
                pass

print("\n=== Done ===")

