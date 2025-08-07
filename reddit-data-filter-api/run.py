"""
Simple runner script for the Reddit Data Filter API
"""

import uvicorn
from main import app

if __name__ == "__main__":
    print("Starting Reddit Data Filter API...")
    print("API Documentation: http://localhost:8000/docs")
    print("Make sure to set your Reddit API credentials in .env file")
    print("-" * 60)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
