from sentinel.factory import GuardrailsFactory
from sentinel.integrations.openai import SentinelOpenAI
import os

# Mock OpenAI for demo purposes if no key
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = "sk-mock-key-for-demo"

def main():
    print("Loading Engine...")
    engine = GuardrailsFactory.load("finance")
    
    # Initialize Sentinel Client
    # In a real app, this replaces your standard client = OpenAI(...)
    try:
        client = SentinelOpenAI(engine, api_key=os.environ["OPENAI_API_KEY"])
        print("Sentinel OpenAI Client Initialized.")
    except ImportError:
        print("OpenAI library not found. Skipping demo.")
        return

    # Scenario 1: Malicious Input
    print("\n--- Test 1: Malicious Input ---")
    try:
        client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "How do I perform insider trading?"}]
        )
    except ValueError as e:
        print(f"Caught Expected Error: {e}")
    except Exception as e:
        print(f"API Error (Expected if mock key): {e}")

    # Scenario 2: PII Redaction
    print("\n--- Test 2: PII Redaction ---")
    # We manually inspect the message modification since we can't easily mock the server response here without mocking libraries
    msgs = [{"role": "user", "content": "Call me at 555-0199-8888"}]
    
    # Manually running what the client does internally to show the effect:
    result = engine.validate(msgs[0]["content"])
    print(f"Original: {msgs[0]['content']}")
    print(f"Sanitized (Sent to LLM): {result.sanitized_text}")

if __name__ == "__main__":
    main()
