import sys
import json
from pathlib import Path
import asyncio
from dotenv import load_dotenv
from livekit import rtc, agents
from livekit.agents import JobContext, WorkerOptions, AgentSession, RoomInputOptions
from livekit.plugins import openai

# -------------------------------------------------------------------------
# ADD PROJECT ROOT TO PYTHON PATH
# -------------------------------------------------------------------------
backend_dir = Path(__file__).parent
project_root = backend_dir.parent
sys.path.append(str(project_root))

# -------------------------------------------------------------------------
# Import our refactored components
# -------------------------------------------------------------------------
from backend.agents.marketing_consultant_agent import MarketingConsultantAgent
from backend.analysis.scoring import analyze_lead_potential
from backend.context_loader import load_context

# -------------------------------------------------------------------------
# LOAD API KEYS
# -------------------------------------------------------------------------
load_dotenv()

# -------------------------------------------------------------------------
# DEFINE THE SESSION ENTRYPOINT
# -------------------------------------------------------------------------
async def multi_agent_entrypoint(ctx: JobContext):
    print("A user has connected. Starting agent session.")
    session = AgentSession()
    
    # ... (The rest of this function is unchanged)
    async def _async_on_transcript(transcript):
        is_user = transcript.participant is not None
        name = "Agent"
        if is_user and transcript.participant.identity:
            name = transcript.participant.identity
        payload = {"type": "transcript", "name": name, "text": transcript.text, "is_user": is_user}
        await ctx.room.local_participant.publish_data(json.dumps(payload))

    def on_transcript(transcript):
        asyncio.create_task(_async_on_transcript(transcript))

    session.on("transcript_finalized", on_transcript)

    async def _async_on_user_disconnected(participant: rtc.RemoteParticipant):
        print(f"User {participant.identity} disconnected. Analyzing conversation...")
        await asyncio.sleep(1)
        llm = openai.LLM.with_cerebras(model="llama-3.3-70b")
        await analyze_lead_potential(session.chat_history(), llm)
        await session.close()

    def on_user_disconnected(participant: rtc.RemoteParticipant):
        asyncio.create_task(_async_on_user_disconnected(participant))

    ctx.room.on("participant_disconnected", on_user_disconnected)
    
    await session.start(
        agent=MarketingConsultantAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(close_on_disconnect=False)
    )
    print("Agent session started.")

# -------------------------------------------------------------------------
# RUN THE APPLICATION
# -------------------------------------------------------------------------
if __name__ == "__main__":
    print("Starting AI Marketing Consultant worker...")
    # This creates a standard worker that listens for jobs from your LiveKit server
    agents.cli.run_app(WorkerOptions(entrypoint_fnc=multi_agent_entrypoint))