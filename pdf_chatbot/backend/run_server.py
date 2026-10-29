import sys
from pathlib import Path

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

import uvicorn

if __name__ == "__main__":
    print("Starting uvicorn server on http://127.0.0.1:8000 ...", flush=True)
    try:
        from app.main import app
        print("FastAPI app imported successfully! Launching server...", flush=True)
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except Exception as e:
        print("Server startup error:", e, flush=True)
        import traceback
        traceback.print_exc()
