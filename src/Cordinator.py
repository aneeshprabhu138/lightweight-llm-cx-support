import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from datetime import datetime

from google import genai
from google.genai import types


@dataclass
class Memory:
    messages: List[Dict] = field(default_factory=list)
    max_history: int = 20

    def add(self, role: str, content: str) -> None:
        self.messages.append(
            {
                "role": role,
                "content": content,
                "time": datetime.now().isoformat(),
            }
        )
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history :]

    def get_context(self) -> str:
        out = ""
        for m in self.messages[-5:]:
            out += f"{m['role']}: {m['content']}\n"
        return out


class LLMIntentAgent:
    def __init__(self, client: genai.Client) -> None:
        self.client = client

    def classify(self, message: str) -> Tuple[str, str]:
        prompt = f"""
        Analyze the user message below and classify its intent into one of the following categories:
        'refund', 'cancellation', 'billing', 'general_help', 'general'.
        Also, assign an urgency level: 'low', 'medium', 'high'.
        Format your response as a single JSON object with keys 'intent' and 'urgency'.
        Message: "{message}"
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema={
                        "type": "object",
                        "properties": {
                            "intent": {"type": "string"},
                            "urgency": {"type": "string"},
                        },
                        "required": ["intent", "urgency"],
                    },
                ),
            )
            result = json.loads(response.text)
            return result["intent"], result["urgency"]
        except Exception as e:
            print(f"API Error during intent classification: {e}")
            return "error", "low"


class LLMReplyAgent:
    def __init__(self, client: genai.Client) -> None:
        self.client = client

    def create_reply(
        self, message: str, intent: str, urgency: str, context: str
    ) -> str:
        prompt = f"""
        You are a helpful and polite customer support agent.
        The user's current intent is classified as '{intent}' with '{urgency}' urgency.
        Here is the recent conversation history:
        ---
        {context}
        ---
        Based only on the above context and the most recent user message, write a concise, professional reply.
        If you need more information (like an order ID or email), politely ask for it.
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            print(f"API Error during reply generation: {e}")
            return "Sorry, I am having trouble connecting to my services right now."


class LLMCoordinator:
    def __init__(self, client: genai.Client) -> None:
        self.intent_agent = LLMIntentAgent(client)
        self.reply_agent = LLMReplyAgent(client)
        self.memory = Memory()

    def ask(self, message: str) -> Dict:
        self.memory.add("user", message)
        intent, urgency = self.intent_agent.classify(message)
        context = self.memory.get_context()
        reply = self.reply_agent.create_reply(message, intent, urgency, context)
        final_output = {"intent": intent, "urgency": urgency, "reply": reply}
        self.memory.add("agent", reply)
        return final_output


def build_llm_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    return genai.Client(api_key=api_key)
