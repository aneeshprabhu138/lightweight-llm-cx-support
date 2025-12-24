import json

from src.coordinator import LLMCoordinator, build_llm_client


def main() -> None:
    llm_client = build_llm_client()
    agent_llm = LLMCoordinator(llm_client)

    messages = [
        "I want to cancel my subscription.",
        "My invoice amount is wrong.",
        "Hello, I need help.",
    ]

    for msg in messages:
        print("USER:", msg)
        out = agent_llm.ask(msg)
        print(json.dumps(out, indent=2))
        print("-" * 50)


if __name__ == "__main__":
    main()
