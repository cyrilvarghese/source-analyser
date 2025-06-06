#!/usr/bin/env python3
"""
Server startup script for the Medical Case Generation System
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main startup function"""
    print("🏥 Medical Case Generation System")
    print("=" * 50)
    
    # Import and run the FastAPI app
    print("🚀 Starting FastAPI server...")
    print("📊 Dashboard will be available at:")
    print("   • Case Creator: http://localhost:8001/case-creator.html")
    print("   • Case Library: http://localhost:8001/caselist.html") 
    print("   • API Docs: http://localhost:8001/docs")
    print("=" * 50)
    
    try:
        import uvicorn
        
        uvicorn.run(
            "app:app",  # Use import string to enable reload
            host="0.0.0.0",
            port=8001,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 