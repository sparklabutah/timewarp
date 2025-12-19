"""
Capture user interactions by listening to browser events.
This approach uses Chrome DevTools Protocol to capture actual user clicks and typing.
"""

from playwright.sync_api import sync_playwright
import json
from datetime import datetime

def run():
    actions_log = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        
        # Start tracing
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        
        page = context.new_page()
        
        # Enable CDP session to capture user events
        cdp = page.context.new_cdp_session(page)
        
        # Listen for mouse clicks
        def on_mouse_click(event):
            actions_log.append({
                'type': 'click',
                'timestamp': datetime.now().isoformat(),
                'x': event.get('x'),
                'y': event.get('y'),
                'button': event.get('button')
            })
            print(f"[CLICK] x={event.get('x')}, y={event.get('y')}")
        
        # Listen for keyboard input
        def on_keyboard(event):
            actions_log.append({
                'type': 'keyboard',
                'timestamp': datetime.now().isoformat(),
                'key': event.get('key'),
                'text': event.get('text')
            })
            print(f"[TYPE] key={event.get('key')}")
        
        # Enable input events
        cdp.send('Input.enable')
        
        # Subscribe to events
        page.on('console', lambda msg: print(f"[CONSOLE] {msg.text}"))
        
        print("\n" + "="*70)
        print("RECORDING WITH EVENT LISTENERS")
        print("="*70)
        print("\n1. Browser opened - navigate and interact")
        print("2. Your actions will be logged in real-time")
        print("3. Press ENTER in this terminal when done\n")
        print("="*70 + "\n")
        
        page.goto("http://127.0.0.1:5001/")
        
        # Wait for user to finish
        input("Press ENTER when done...")
        
        # Save trace
        context.tracing.stop(path="my_agent_task_trace.zip")
        
        # Save actions log
        with open("actions_log.json", "w") as f:
            json.dump(actions_log, f, indent=2)
        
        print(f"\n✓ Trace saved to: my_agent_task_trace.zip")
        print(f"✓ Actions log saved to: actions_log.json")
        print(f"✓ Captured {len(actions_log)} user actions\n")
        
        browser.close()

if __name__ == "__main__":
    run()

