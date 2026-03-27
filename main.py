import os
import sys
import threading
import webbrowser
import time
import uvicorn

HOST = "127.0.0.1"
PORT = 8000


def open_browser():
    time.sleep(1.5)
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":

    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

    threading.Thread(target=open_browser, daemon=True).start()
    from app.server import app  # noqa: E402
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
