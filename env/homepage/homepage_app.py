"""
Homepage UI - Flask Backend
Serves various homepage layouts/templates with theme selection
"""

from flask import Flask, render_template, send_from_directory
import os
import sys
import socket
import subprocess
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def _parse_args(argv):
    """Parse CLI args for theme selection and optional port override."""
    num_to_theme = {
        '1': '1-2column-splitscreen-dark',
        '2': '2-blocks-cards-light',
        '3': '3-modern-retro-dark',
        '4': '4-interactive-dark',
        '5': '5-magazine-light',
        '6': '6-classic-scroll-F-shape-dark',
    }
    name_aliases = {
        '2column': '1-2column-splitscreen-dark',
        'splitscreen': '1-2column-splitscreen-dark',
        'blocks': '2-blocks-cards-light',
        'cards': '2-blocks-cards-light',
        'modern-retro': '3-modern-retro-dark',
        'modernretro': '3-modern-retro-dark',
        'retro': '3-modern-retro-dark',
        'interactive': '4-interactive-dark',
        'magazine': '5-magazine-light',
        'classic': '6-classic-scroll-F-shape-dark',
        'scroll': '6-classic-scroll-F-shape-dark',
        'all': 'all',
    }
    selected_theme = '6-classic-scroll-F-shape-dark'
    port_override = None
    run_all = False
    for raw in argv[1:]:
        arg = raw.lstrip('-').lower()
        if raw.startswith('--port='):
            try:
                port_override = int(raw.split('=', 1)[1])
            except Exception:
                pass
            continue
        if arg in num_to_theme:
            selected_theme = num_to_theme[arg]
        elif arg in name_aliases:
            if name_aliases[arg] == 'all':
                run_all = True
            else:
                selected_theme = name_aliases[arg]
    return selected_theme, port_override, run_all


# Determine theme and port from command line arguments
THEME, PORT_OVERRIDE, RUN_ALL = _parse_args(sys.argv)

print(f"Using theme: {THEME}")

# Initialize Flask with theme-specific paths
# Homepage themes have flat structure (all files in same folder)
theme_path = os.path.join(SCRIPT_DIR, 'themes', THEME)
app = Flask(__name__,
            template_folder=theme_path,
            static_folder=theme_path)


@app.route('/')
def index():
    """Main homepage"""
    return render_template('index.html')


@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files from the theme folder"""
    return send_from_directory(theme_path, filename)


def find_free_port(start_port=5100, max_attempts=100):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find a free port in range {start_port}-{start_port + max_attempts}")


if __name__ == '__main__':
    # If -all provided, spawn five servers (1-5) on successive ports
    if RUN_ALL:
        base_port = PORT_OVERRIDE if PORT_OVERRIDE else find_free_port()
        theme_nums = ['1', '2', '3', '4', '5', '6']
        procs = []
        print("\n" + "="*60)
        print("Starting multiple Homepage UI servers...")
        for i, num in enumerate(theme_nums):
            port = base_port + i
            cmd = [sys.executable, __file__, num, f"--port={port}"]
            try:
                p = subprocess.Popen(cmd)
                procs.append((num, port, p.pid))
            except Exception as e:
                print(f"Failed to start server {num} on port {port}: {e}")
        for num, port, pid in procs:
            print(f"Server {num} running at http://localhost:{port} (PID {pid})")
        print("="*60 + "\n")
        # Keep parent alive to avoid abrupt exit; wait for children
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass
    else:
        # Determine port
        port = PORT_OVERRIDE if PORT_OVERRIDE else find_free_port()
        
        # Run the Flask app
        print("\n" + "="*60)
        print("Homepage UI is starting...")
        print(f"Theme: {THEME}")
        print(f"Open your browser and go to: http://localhost:{port}")
        print("="*60 + "\n")
        
        # Use use_reloader=False to avoid issues with port binding in debug mode
        app.run(debug=True, port=port, use_reloader=False)
