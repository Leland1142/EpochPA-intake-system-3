from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from auth import router as auth_router
from pa import router as pa_router

app = FastAPI(title="EpochPA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Custom homepage pointing to Streamlit ---
@app.get("/", response_class=HTMLResponse)
async def homepage():
    return """
    <html>
        <head>
            <title>EpochPA Portal</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 80px; }
                .logo { max-width: 220px; margin-bottom: 35px; }
                .btn {
                    display: inline-block;
                    background: #2574a9;
                    color: #fff;
                    padding: 18px 42px;
                    border-radius: 8px;
                    font-size: 1.3rem;
                    font-weight: bold;
                    text-decoration: none;
                    margin-top: 18px;
                    box-shadow: 0 2px 8px rgba(37,116,169,0.08);
                    transition: background 0.2s;
                }
                .btn:hover { background: #205a85; }
            </style>
        </head>
        <body>
            <!-- Insert your logo file path here, e.g. /static/epochpa_logo.png -->
            <!-- <img class="logo" src="/static/epochpa_logo.png" alt="EpochPA Logo"/> -->
            <h1>Welcome to EpochPA</h1>
            <p style="font-size:1.1rem;color:#444;">Click below to access your provider dashboard and submit prior authorization requests.</p>
            <a href="https://epochpa-intake-system-3-sdk3jwsvemc7olkziw83ie.streamlit.app/" class="btn">Go to Provider Portal</a>
        </body>
    </html>
    """

# Mount all API endpoints under /intake
app.include_router(auth_router, prefix="/intake")
app.include_router(pa_router, prefix="/intake")
