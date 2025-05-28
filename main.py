from fastapi import FastAPI
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

# mount under /intake
app.include_router(auth_router, prefix="/intake")
app.include_router(pa_router, prefix="/intake")
