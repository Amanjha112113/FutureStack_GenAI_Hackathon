import sys
import os
import json
from pathlib import Path
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import rtc, api, agents

# -------------------------------------------------------------------------
# SETUP & IMPORTS (Path, Environment, etc.)
# -------------------------------------------------------------------------
load_dotenv()
backend_dir = Path(__file__).parent
project_root = backend_dir.parent
sys.path.append(str(project_root))

from backend.agents.marketing_consultant_agent import MarketingConsultantAgent
from backend.analysis.scoring import analyze_lead_potential
from backend.context_loader import load_context

# Read LiveKit credentials from environment variables
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
    raise EnvironmentError("LiveKit API Key/Secret must be set.")

# -------------------------------------------------------------------------
# 1. DEFINE THE FASTAPI WEB SERVER (for generating tokens)
# -------------------------------------------------------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, 
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/token")
async def get_token(room_name: str, identity: str):
    try:
        token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
            .with_identity(identity) \
            .with_grants(api.VideoGrants(room_join=True, room=room_name)) \
            .to_jwt()
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------------
# 2. DEFINE THE AI AGENT WORKER (your previous main.py logic)
# -------------------------------------------------------------------------
async def agent_entrypoint(ctx: agents.JobContext):
    print("Agent session starting...")
    session = agents.AgentSession()

    async def _async_on_transcript(transcript):
        is_user = transcript.participant is not None
        name = "Agent"
        if is_user and transcript.participant.identity: name = transcript.participant.identity
        payload = {"type": "transcript", "name": name, "text": transcript.text, "is_user": is_user}
        await ctx.room.local_participant.publish_data(json.dumps(payload))

    def on_transcript(transcript):
        asyncio.create_task(_async_on_transcript(transcript))

    session.on("transcript_finalized", on_transcript)

    async def _async_on_user_disconnected(p: rtc.RemoteParticipant):
        print("User disconnected, analyzing conversation...")
        await asyncio.sleep(1)
        llm = agents.llm.LLM.with_cerebras(model="llama-3.3-70b")
        await analyze_lead_potential(session.chat_history(), llm)
        await session.close()

    def on_user_disconnected(p: rtc.RemoteParticipant):
        asyncio.create_task(_async_on_user_disconnected(p))

    ctx.room.on("participant_disconnected", on_user_disconnected)
    
    await session.start(
        agent=MarketingConsultantAgent(),
        room=ctx.room,
        room_input_options=agents.RoomInputOptions(close_on_disconnect=False)
    )
    print("Agent session started successfully.")

# -------------------------------------------------------------------------
# 3. CREATE A STARTUP EVENT TO LAUNCH THE AGENT WORKER
# -------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    # This function will be called when the FastAPI server starts
    # It creates the LiveKit worker and runs it in the background
    print("FastAPI server started. Launching agent worker...")
    worker = agents.Worker(
        entrypoint_fnc=agent_entrypoint,
        worker_type=agents.JobType.ROOM
    )
    asyncio.create_task(worker.run())
    print("Agent worker is running in the background.")
