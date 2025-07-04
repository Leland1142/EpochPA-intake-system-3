from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

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

# --- Friendly Homepage ---
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>EpochPA | Prior Authorization Made Simple</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; background: #f7f8fa; color: #222;}
            .container { max-width: 600px; margin: 60px auto; padding: 40px 30px; background: #fff; border-radius: 16px; box-shadow: 0 6px 24px rgba(0,0,0,0.07);}
            h1 { color: #2535a7; font-size: 2.4em; margin-bottom: 0.4em;}
            p { font-size: 1.18em; color: #444; }
            a.button {
                display: inline-block;
                margin-top: 30px;
                padding: 13px 30px;
                background: #2535a7;
                color: #fff;
                border-radius: 8px;
                text-decoration: none;
                font-weight: bold;
                transition: background 0.2s;
            }
            a.button:hover { background: #18226b;}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to EpochPA</h1>
            <p>Your simple, modern solution for medical Prior Authorization.<br>
            Providers, patients, and reps — streamline every step and get faster approvals, less paperwork, and full transparency.</p>
            <a href="/docs" class="button">View API Docs</a>
        </div>
    </body>
    </html>
    """

# mount under /intake
app.include_router(auth_router, prefix="/intake")
app.include_router(pa_router, prefix="/intake")
