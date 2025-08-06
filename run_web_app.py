#!/usr/bin/env python3
"""
Direct launcher for the GBA Memory Analysis Web App
"""

import os
import sys
from pathlib import Path

# Set up paths
project_root = Path(__file__).parent
web_app_dir = project_root / "src" / "web_app"
db_path = project_root / "gba_training.db"

# Check database
if not db_path.exists():
    print(f"❌ Database not found: {db_path}")
    sys.exit(1)

# Add web app to Python path
sys.path.insert(0, str(web_app_dir))
os.chdir(web_app_dir)

# Import and run
from app import app

if __name__ == "__main__":
    print("🧠 GBA Memory Analysis Web App Starting...")
    print("📍 Main App: http://localhost:5000")
    print("🔍 Memory Analysis: http://localhost:5000/memory/")
    print("Press Ctrl+C to stop\n")
    
    app.run(host='localhost', port=5000, debug=False)
