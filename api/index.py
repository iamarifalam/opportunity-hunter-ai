"""
Vercel Serverless Function entrypoint for Opportunity Hunter AI.
Exposes the ASGI FastAPI app.
"""

import sys
import os

# Ensure the root directory is on the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hunter_ai.api.app import app
