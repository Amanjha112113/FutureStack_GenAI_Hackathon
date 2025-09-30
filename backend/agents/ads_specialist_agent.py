from livekit.agents import Agent, function_tool
from livekit.plugins import openai, cartesia, silero
from backend.context_loader import load_context

class AdsSpecialistAgent(Agent):
    def __init__(self):
        context = load_context()
        llm = openai.LLM.with_cerebras(model="llama-3.3-70b")
        stt = cartesia.STT()
        tts = cartesia.TTS(voice="bf0a246a-8642-498a-9950-80c35e9276b5")
        vad = silero.VAD.load()
        instructions = "You are a Meta Ads Specialist. Your expertise is in the technical setup of ad campaigns, including targeting and the Meta Pixel. Be precise and clear."
        super().__init__(instructions=instructions, stt=stt, llm=llm, tts=tts, vad=vad)

    async def on_enter(self):
        print("Current Agent: 💻 Ads Specialist 💻")
        await self.session.say("Hi, I'm the Ads Specialist. I can help with technical questions about campaign setup.")

    @function_tool
    async def switch_to_consultant(self):
        from .marketing_consultant_agent import MarketingConsultantAgent  # Import moved inside
        await self.session.say("Let me transfer you back to our main consultant for that.")
        return MarketingConsultantAgent()

    @function_tool
    async def switch_to_budgeting(self):
        from .budgeting_specialist_agent import BudgetingSpecialistAgent  # Import moved inside
        await self.session.say("I'll transfer you to our budgeting specialist to discuss costs.")
        return BudgetingSpecialistAgent()