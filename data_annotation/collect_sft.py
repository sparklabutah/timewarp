"""
This script uses Playwright's codegen to record user interactions.
It will generate a trace file with actual user actions.

Usage:
    python data_annotation/collect_sft.py [url] [trace_output] [exit_msg_output]

Arguments:
    url: Target URL (default: http://127.0.0.1:5001/)
    trace_output: Path to save trace file (default: my_agent_task_trace.zip)
    exit_msg_output: Path to save exit message (default: exit_message.txt)

This will:
1. Open a browser with Playwright Inspector
2. Navigate to the target URL
3. Record ALL your manual interactions (clicks, typing, etc.)
4. Save a trace file when you close the browser

IMPORTANT: Close the browser window (not the Inspector) when you're done.
"""

from playwright.sync_api import sync_playwright
import sys
import os

def run(url="http://127.0.0.1:5001/", trace_output="my_agent_task_trace.zip", exit_msg_output="exit_message.txt"):
    # Create output directory if it doesn't exist
    trace_dir = os.path.dirname(trace_output)
    if trace_dir and not os.path.exists(trace_dir):
        os.makedirs(trace_dir, exist_ok=True)
    
    exit_msg_dir = os.path.dirname(exit_msg_output)
    if exit_msg_dir and not os.path.exists(exit_msg_dir):
        os.makedirs(exit_msg_dir, exist_ok=True)
    
    with sync_playwright() as p:
        # Launch browser with tracing enabled from the start
        browser = p.chromium.launch(headless=False)
        
        # Create context with recording enabled
        context = browser.new_context(
            record_video_dir=None,  # We don't need video
            record_har_path=None    # We don't need HAR
        )
        
        # Start tracing IMMEDIATELY
        context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True
        )
        
        page = context.new_page()
        
        print("\n" + "="*70)
        print("RECORDING USER ACTIONS")
        print("="*70)
        print(f"\nTarget URL: {url}")
        print(f"Trace output: {trace_output}")
        print(f"Exit message output: {exit_msg_output}")
        print("\n1. Browser window opened")
        print("2. Navigate and perform your actions in the browser")
        print("3. When done, CLOSE THE BROWSER WINDOW (click X)")
        print("4. Trace will be saved automatically\n")
        print("="*70 + "\n")
        
        # Navigate to target
        page.goto(url)
        
        # Keep the script running until user closes the browser
        print("Waiting for you to close the browser window...")
        try:
            # Wait for the page to be closed
            while not page.is_closed():
                page.wait_for_timeout(500)  # Check every 500ms
        except:
            pass
        
        # Prompt for exit message (the answer to the task)
        print("\n" + "="*70)
        print("TASK COMPLETION")
        print("="*70)
        exit_message = input("\nEnter your final answer/result for this task:\n> ")
        
        # Save exit message to a file
        with open(exit_msg_output, "w", encoding="utf-8") as f:
            f.write(exit_message)
        
        # Stop tracing and save
        print("\nSaving trace...")
        context.tracing.stop(path=trace_output)
        print(f"✓ Trace saved to: {trace_output}")
        print(f"✓ Exit message saved to: {exit_msg_output}\n")
        
        browser.close()

if __name__ == "__main__":
    # Parse command-line arguments
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5001/"
    trace_output = sys.argv[2] if len(sys.argv) > 2 else "my_agent_task_trace.zip"
    exit_msg_output = sys.argv[3] if len(sys.argv) > 3 else "exit_message.txt"
    
    run(url, trace_output, exit_msg_output)
