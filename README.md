# Lightweight LLM-Powered Customer Support Coordinator

A **lightweight** customer-support orchestration module that uses Google Gemini to:  
- Classify user intent and urgency  
- Maintain short-term conversation memory  
- Generate contextual, professional replies  

Designed as a small, production-friendly building block for support tools and internal dashboards.

---

## Features

- Intent classification into categories: `refund`, `cancellation`, `billing`, `general_help`, `general` with urgency labels `low`, `medium`, `high` using Gemini.[file:1]
- Simple in-memory conversation history with configurable max history and automatic truncation.[file:1]
- Context-aware reply generation using the latest few turns of conversation.[file:1]
- Single coordinator class (`LLMCoordinator`) that exposes a clean `.ask(message)` interface returning JSON with `intent`, `urgency`, and `reply`.[file:1]
- Minimal dependencies: Python, `google-genai`, `python-dotenv` (optional).

---

## Project structure

src/coordinator.py # Core classes: Memory, LLMIntentAgent, LLMReplyAgent, LLMCoordinator
examples/sample_run.py # Simple CLI-style usage example
requirements.txt # Python dependencies


---

## Setup

### 1. Clone the repository

git clone https://github.com/<your-username>/lightweight-llm-cx-support.git
cd lightweight-llm-cx-support


### 2. Create virtual environment and install dependencies

python -m venv .venv
source .venv/bin/activate # Windows: .venv\Scripts\activate
pip install -r requirements.txt


`requirements.txt` (example):

google-genai>=0.2.0
python-dotenv>=1.0.0.


---

## Configuration

Create a `.env` file in the project root:

GEMINI_API_KEY=your_api_key_here

The code reads `GEMINI_API_KEY` from the environment and throws a clear error if it is missing.[file:1]

src/coordinator.py (snippet)
import os
from google import genai

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
raise ValueError("GEMINI_API_KEY environment variable not set.")
llm_client = genai.Client(api_key=api_key)


---

## Usage

### Example: run demo conversations

`examples/sample_run.py`:

import json
from src.coordinator import LLMCoordinator, llm_client

if name == "main":
agent_llm = LLMCoordinator(llm_client)


messages = [
    "I want to cancel my subscription.",
    "My invoice amount is wrong.",
    "Hello, I need help."
]

for msg in messages:
    print("USER:", msg)
    out = agent_llm.ask(msg)
    print(json.dumps(out, indent=2))
    print("-" * 50)

Run:

python -m examples.sample_run


Expected JSON output structure for each turn:

{
"intent": "cancellation",
"urgency": "high",
"reply": "Thank you for reaching out. I can help cancel your subscription..."
}




---

## How it works (design notes)

- **Memory**  
  - Stores a list of `{role, content, time}` messages and keeps only the last `max_history` entries.[file:1]  
  - `get_context()` returns a compact string of the last 5 turns to keep prompts efficient.[file:1]

- **LLMIntentAgent**  
  - Builds a strict prompt asking Gemini to output JSON with `intent` and `urgency` only.[file:1]  
  - Uses `response_mime_type="application/json"` and a JSON schema to reduce parsing errors.[file:1]  
  - Falls back to `"error"` / `"low"` on API errors so the coordinator can still respond.[file:1]

- **LLMReplyAgent**  
  - Conditions Gemini with role: “helpful and polite customer support agent” and passes intent, urgency, and conversation context.[file:1]  
  - Encourages concise, professional replies and asks for missing details (e.g., order ID) when needed.[file:1]

- **LLMCoordinator**  
  - Public method `ask(message)`:
    1. Adds user message to memory.  
    2. Calls `LLMIntentAgent.classify(message)` for `intent`, `urgency`.[file:1]  
    3. Gets recent context from memory.  
    4. Calls `LLMReplyAgent.create_reply(...)` to generate a reply.[file:1]  
    5. Stores the agent reply back into memory and returns a JSON dict.[file:1]

---

## Possible extensions

- Add tests around `Memory` and mocking LLM calls.  
- Add a small FastAPI/Flask layer to expose `/ask` over HTTP.  
- Store memory in Redis or a database for multi-session support.

---






