import json
from livekit.plugins import openai
import re

async def analyze_lead_potential(chat_history, llm: openai.LLM) -> str:
    """
    Analyzes the conversation history to score a lead's potential and extract their name.
    Saves the report to a file.
    """
    conversation_text = "".join(f"{entry.role}: {entry.text}\n" for entry in chat_history.entries)

    analysis_prompt = f"""
    You are a sales analyst. Your two tasks are to analyze the following conversation.
    1. First, find the user's name, which they provide at the beginning of the conversation.
    2. Second, classify the user's lead potential as a single word: High, Medium, or Low.

    - High potential: They have clear business goals, a defined budget, and are ready to start a campaign.
    - Medium potential: They have goals but are unsure about budget or strategy.
    - Low potential: They are just exploring options and have no immediate plans.

    Conversation:
    ---
    {conversation_text}
    ---
    
    Respond in the following JSON format: {{"name": "USER_NAME", "score": "SCORE"}}
    """

    result = await llm.chat(analysis_prompt)
    response_text = result.choices[0].message.content.strip()

    name = "Unknown"
    score = "Not Scored"
    
    try:
        # Use regex to find JSON in case the LLM adds extra text
        json_match = re.search(r'\{.*\}', response_text)
        if json_match:
            report_data = json.loads(json_match.group())
            name = report_data.get("name", "Unknown")
            score = report_data.get("score", "Not Scored")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Could not parse LLM response for scoring: {e}")


    print(f"👤 Name Extracted: {name}")
    print(f"📈 Lead Potential Score: {score}")

    # Save the report to a file
    report = {
        "name": name,
        "score": score,
        "conversation": conversation_text,
    }
    with open("lead_reports.jsonl", "a") as f:
        f.write(json.dumps(report) + "\n")

    print(f"✅ Report for {name} saved to lead_reports.jsonl")
    return score