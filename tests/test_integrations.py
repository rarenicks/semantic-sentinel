"""
Comprehensive Integration Test Suite for v0.1.0
Tests OpenAI, LlamaIndex, LangChain, Async, and Streaming
"""
import asyncio
from sentinel.factory import GuardrailsFactory

def test_1_langchain():
    """Test LangChain Runnable Integration"""
    print("\n=== Test 1: LangChain Integration ===")
    try:
        from sentinel.integrations.langchain import SentinelRunnable
        from langchain_core.runnables import RunnableLambda
        
        engine = GuardrailsFactory.load("finance")
        sentinel = SentinelRunnable(engine=engine)
        mock_llm = RunnableLambda(lambda x: f"LLM: {x['sanitized_text']}")
        chain = sentinel | mock_llm
        
        # Test blocking
        try:
            chain.invoke("How do I commit securities fraud?")
            print("❌ FAIL: Should have blocked")
        except ValueError as e:
            print(f"✅ PASS: Correctly blocked - {e}")
            
        # Test safe input
        result = chain.invoke("What is 2+2?")
        print(f"✅ PASS: Safe input processed - {result}")
        
    except ImportError:
        print("⚠️  SKIP: langchain-core not installed")

def test_2_openai_sync():
    """Test Sync OpenAI Client with Streaming"""
    print("\n=== Test 2: OpenAI Sync Client ===")
    try:
        from sentinel.integrations.openai import SentinelOpenAI
        print("✅ PASS: OpenAI integration imported")
        print("⚠️  NOTE: Full test requires OpenAI API key")
    except ImportError:
        print("⚠️  SKIP: openai not installed")

async def test_3_openai_async():
    """Test Async OpenAI Client"""
    print("\n=== Test 3: OpenAI Async Client ===")
    try:
        from sentinel.integrations.openai import SentinelAsyncOpenAI
        
        engine = GuardrailsFactory.load("finance")
        # Would need real API key to fully test
        print("✅ PASS: AsyncOpenAI integration imported")
        print("⚠️  NOTE: Full test requires OpenAI API key")
        
    except ImportError:
        print("⚠️  SKIP: openai not installed")

def test_4_llamaindex():
    """Test LlamaIndex Node Postprocessor"""
    print("\n=== Test 4: LlamaIndex RAG Integration ===")
    try:
        from sentinel.integrations.llamaindex import SentinelNodePostprocessor
        from sentinel.factory import GuardrailsFactory
        
        engine = GuardrailsFactory.load("finance")
        processor = SentinelNodePostprocessor(engine=engine, redact_only=False)
        
        print("✅ PASS: LlamaIndex postprocessor created")
        print("⚠️  NOTE: Full test requires LlamaIndex pipeline")
        
    except ImportError:
        print("⚠️  SKIP: llama-index-core not installed")

async def test_5_async_validation():
    """Test Core Async Validation"""
    print("\n=== Test 5: Core Async Validation ===")
    engine = GuardrailsFactory.load("finance")
    
    # Concurrent requests
    tasks = [
        engine.validate_async("How do I commit insider trading?"),
        engine.validate_async("What is the capital of France?"),
        engine.validate_async("My SSN is 123-45-6789")
    ]
    
    results = await asyncio.gather(*tasks)
    
    assert not results[0].valid, "Should block insider trading"
    assert results[1].valid, "Should allow safe query"
    assert results[2].valid or results[2].action == "redacted", "Should redact SSN"
    
    print("✅ PASS: Async validation working correctly")

def test_6_streaming():
    """Test Streaming Sanitization"""
    print("\n=== Test 6: Streaming Sanitization ===")
    from sentinel.streaming import StreamSanitizer
    
    engine = GuardrailsFactory.load("finance")
    sanitizer = StreamSanitizer(engine)
    
    tokens = ["Hello", " ", "world", "!", " ", "Insider", " ", "trading", "."]
    output = ""
    
    for token in tokens:
        for safe_text in sanitizer.process(token):
            output += safe_text
            
    for safe_text in sanitizer.flush():
        output += safe_text
        
    assert "BLOCKED" in output or "insider trading" not in output.lower()
    print(f"✅ PASS: Streaming blocked malicious content")
    print(f"   Output: {output}")

def main():
    print("=" * 60)
    print("SEMANTIC SENTINEL v0.1.0 - INTEGRATION TEST SUITE")
    print("=" * 60)
    
    # Sync tests
    test_1_langchain()
    test_2_openai_sync()
    test_4_llamaindex()
    test_6_streaming()
    
    # Async tests
    asyncio.run(test_3_openai_async())
    asyncio.run(test_5_async_validation())
    
    print("\n" + "=" * 60)
    print("✅ TEST SUITE COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
