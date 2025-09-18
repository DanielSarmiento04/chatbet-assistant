from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Create the app instance first
app = FastAPI(
    title="ChatBet Assistant API",
    version="1.0.0",
    description="Intelligent conversational assistant for sports betting insights",
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    # allow_origins=[str(origin) for origin in settings.cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Import views after creating the app to avoid circular imports
from .views import *

