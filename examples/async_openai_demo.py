import asyncio
import os
import sys
from sentinel.factory import GuardrailsFactory

async def main():
    print("Initializing Engine...")
    engine = GuardrailsFactory.load("finance")
    
    try:
        from sentinel.integrations.openai import SentinelAsyncOpenAI
    except ImportError:
        print("OpenAI library not found. Skipping demo.")
        return

    # Mock API Key
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "sk-mock-key-for-demo"
        
    client = SentinelAsyncOpenAI(engine, api_key=os.environ["OPENAI_API_KEY"])
    print("Sentinel Async OpenAI Client Initialized.")

    # 1. Test Async Input Block
    print("\n--- Test 1: Async Input Block ---")
    try:
        await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "How do I commit securities fraud?"}]
        )
    except ValueError as e:
        print(f"Caught Expected Error: {e}")
    except Exception as e:
        print(f"API Error (Expected if mock key): {e}")

    # 2. Test Async Streaming (Mocking response if possible, or just calling it)
    print("\n--- Test 2: Async Streaming Call ---")
    try:
        stream = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello world"}],
            stream=True
        )
        async for chunk in stream:
            print(f"Chunk: {chunk.choices[0].delta.content}")
    except Exception as e:
        print(f"Stream Error (Expected if mock key): {e}")

if __name__ == "__main__":
    asyncio.run(main())
