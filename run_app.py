#!/usr/bin/env python3
"""
HCDC Class Record - Ready-to-Use Launcher
Just run: python run_app.py
"""

import os
import sys
import threading
import webbrowser

# Setup data directory in user's home
HOME_DIR = os.path.expanduser('~')
DATA_DIR = os.path.join(HOME_DIR, '.hcdc_class_record')
os.makedirs(DATA_DIR, exist_ok=True)

# Set database path before importing app_instance
os.environ['HCDC_DATABASE_PATH'] = os.path.join(DATA_DIR, 'class_record.db')

# Now import after setting the path
from app_instance import app, init_db

# Initialize the database
print("📁 Initializing database...")
init_db()
print("✅ Database initialized!")

print("🚀 Starting HCDC Class Record...")
print(f"📊 Data will be stored in: {DATA_DIR}")

def run_server():
    """Run Flask server"""
    app.run(host='127.0.0.1', port=5000, debug=False)

if __name__ == '__main__':
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Open browser automatically
    print("🌐 Opening browser to: http://127.0.0.1:5000")
    webbrowser.open('http://127.0.0.1:5000')

    # Keep the script running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n❌ Shutting down...")
