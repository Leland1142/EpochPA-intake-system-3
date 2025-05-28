import subprocess
import time
import webbrowser

FASTAPI_URL = "http://127.0.0.1:8000/docs"      # Swagger UI for FastAPI
STREAMLIT_URL = "http://localhost:8501"         # Streamlit default

if __name__ == "__main__":
    # Start FastAPI backend
    fastapi_proc = subprocess.Popen([
        "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"
    ])
    time.sleep(2)  # Give FastAPI a moment to start

    # Open FastAPI docs in browser
    webbrowser.open(FASTAPI_URL)

    # Start Streamlit frontend
    streamlit_proc = subprocess.Popen([
        "streamlit", "run", "streamlit_app.py"
    ])
    time.sleep(3)  # Wait for Streamlit server to start

    # Open Streamlit app in browser
    webbrowser.open(STREAMLIT_URL)

    try:
        fastapi_proc.wait()
        streamlit_proc.wait()
    except KeyboardInterrupt:
        print("Shutting down both processes...")
        fastapi_proc.terminate()
        streamlit_proc.terminate()
