# EpochPA Intake System

A Prior Authorization (PA) intake and workflow platform for healthcare providers.

## Features
- Provider, Rep, and Admin dashboards (Streamlit)
- FastAPI backend for PA request management
- Role-based authentication
- Integration (swap-in ready) for insurance verification APIs

## Setup Instructions

1. Clone the repo:
    ```
    git clone https://github.com/Leland1142/EpochPA-intake-system-3.git
    ```
2. Set up your Python environment:
    ```
    python -m venv env
    source env/bin/activate  # or `env\Scripts\activate` on Windows
    pip install -r requirements.txt
    ```

3. Start the system:
    ```
    python launch.py
    ```
4. Streamlit app: [http://localhost:8501](http://localhost:8501)  
   FastAPI docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## .env File Example

