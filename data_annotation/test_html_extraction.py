#!/usr/bin/env python3
"""Test HTML extraction from trace."""
from trace_parser import TraceParser

trace_path = 'my_agent_task_trace.zip'

print("=== Testing HTML Extraction ===\n")

with TraceParser(trace_path) as parser:
    actions = parser.parse()
    
    print(f"Found {len(actions)} actions")
    print(f"Found {len(parser.snapshots)} snapshots")
    print(f"Snapshot order: {parser.snapshot_order}")
    print(f"Snapshot keys: {list(parser.snapshots.keys())}")
    
    print("\n=== Testing get_html_snapshot ===")
    for i in range(len(actions) + 1):
        html = parser.get_html_snapshot(i)
        if html:
            print(f"\nSnapshot {i}:")
            print(f"  Length: {len(html)} chars")
            print(f"  Preview: {html[:200]}...")
        else:
            print(f"\nSnapshot {i}: None")

