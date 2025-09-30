from livekit.agents import Agent, function_tool
from livekit.plugins import openai, cartesia, silero
from backend.context_loader import load_context

class BudgetingSpecialistAgent(Agent):
    def __init__(self):
        context = load_context()
        llm = openai.LLM.with_cerebras(model="llama-3.3-70b")
        stt = cartesia.STT()
        tts = cartesia.TTS(voice="4df027cb-2920-4a1f-8c34-f21529d5c3fe")
        vad = silero.VAD.load()
        instructions = "You are a Budgeting Specialist for Meta Ads. You only discuss ad spend, budgets, and return on investment (ROAS)."
        super().__init__(instructions=instructions, stt=stt, llm=llm, tts=tts, vad=vad)

    async def on_enter(self):
        print("Current Agent: 💰 Budgeting Specialist 💰")
        await self.session.say("Hello, I'm the budgeting specialist. I can help you with questions about ad spend and ROI.")

    @function_tool
    async def switch_to_consultant(self):
        from .marketing_consultant_agent import MarketingConsultantAgent  # Import moved inside
        await self.session.say("I'll transfer you back to our main consultant for that.")
        return MarketingConsultantAgent()

    @function_tool
    async def switch_to_technical(self):
        from .ads_specialist_agent import AdsSpecialistAgent  # Import moved inside
        await self.session.say("Let me get our Ads Specialist to answer that technical question.")
        return AdsSpecialistAgent()