from livekit.agents import Agent, function_tool
from livekit.plugins import openai, cartesia, silero
from backend.context_loader import load_context

class MarketingConsultantAgent(Agent):
    def __init__(self):
        context = load_context()
        llm = openai.LLM.with_cerebras(model="llama-3.3-70b")
        stt = cartesia.STT()
        tts = cartesia.TTS()
        vad = silero.VAD.load()
        instructions = "You are a friendly and helpful marketing consultant for Meta Ads. Your goal is to understand a client's business needs. All text you return will be spoken aloud."
        super().__init__(instructions=instructions, stt=stt, llm=llm, tts=tts, vad=vad)

    async def on_enter(self):
        print("Current Agent: 📈 Marketing Consultant 📈")
        await self.session.say("Hi, thanks for your interest in our Meta Ads services. To start, could you tell me a little about your business goals?")

    @function_tool
    async def switch_to_ads_specialist(self):
        """Use this function for deep technical questions about ad setup, targeting, or the Meta Pixel."""
        from .ads_specialist_agent import AdsSpecialistAgent  # Import moved inside
        await self.session.say("That's a great technical question. Let me connect you with our Meta Ads Specialist.")
        return AdsSpecialistAgent()

    @function_tool
    async def switch_to_budgeting(self):
        """Use this function for questions about ad spend, budgets, cost, or return on investment."""
        from .budgeting_specialist_agent import BudgetingSpecialistAgent  # Import moved inside
        await self.session.say("I can transfer you to our budgeting specialist for that. One moment.")
        return BudgetingSpecialistAgent()