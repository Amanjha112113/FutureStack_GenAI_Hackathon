import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api

# Read LiveKit credentials from environment variables
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
    raise EnvironmentError("LiveKit API Key and Secret must be set in environment variables.")

app = FastAPI()

# Allow requests from all origins (for simplicity in a hackathon)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/token")
async def get_token(room_name: str, identity: str):
    """
    Generates a LiveKit access token.
    """
    try:
        token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
            .with_identity(identity) \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
            )).to_jwt()
        
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))