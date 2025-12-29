from typing import Any, Dict, List, Optional, Union, AsyncGenerator, Generator
from sentinel.engine import GuardrailsEngine
from sentinel.streaming import StreamSanitizer

try:
    from openai import OpenAI, AsyncOpenAI
    from openai.types.chat import ChatCompletion, ChatCompletionChunk
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

if OPENAI_AVAILABLE:
    class SentinelOpenAI:
        """
        Wrapper for the Sync OpenAI Client to automatically apply guardrails.
        """
        def __init__(self, engine: GuardrailsEngine, **client_kwargs):
            self.engine = engine
            self._client = OpenAI(**client_kwargs)
            self.chat = self.ChatWrapper(self._client, self.engine)

        class ChatWrapper:
            def __init__(self, client: OpenAI, engine: GuardrailsEngine):
                self.completions = self.CompletionsWrapper(client, engine)

            class CompletionsWrapper:
                def __init__(self, client: OpenAI, engine: GuardrailsEngine):
                    self._client = client
                    self._engine = engine
                
                def create(self, **kwargs) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
                    # 1. Scan Input Messages
                    messages = kwargs.get("messages", [])
                    for msg in messages:
                        if "content" in msg and isinstance(msg["content"], str):
                            result = self._engine.validate(msg["content"])
                            if not result.valid and result.action == "blocked":
                                raise ValueError(f"Sentinel Blocked Input: {result.reason}")
                            msg["content"] = result.sanitized_text

                    # 2. Call Original API
                    response = self._client.chat.completions.create(**kwargs)

                    # 3. Handle Response
                    if kwargs.get("stream", False):
                        return self._stream_wrapper(response)
                    else:
                        return self._handle_sync_response(response)

                def _handle_sync_response(self, response: ChatCompletion) -> ChatCompletion:
                    content = response.choices[0].message.content
                    if content:
                        result = self._engine.validate_output(content)
                        if not result.valid and result.action == "blocked":
                            raise ValueError(f"Sentinel Blocked Output: {result.reason}")
                        
                        if result.sanitized_text != content:
                            response.choices[0].message.content = result.sanitized_text
                    return response

                def _stream_wrapper(self, stream) -> Generator[ChatCompletionChunk, None, None]:
                    sanitizer = StreamSanitizer(self._engine)
                    last_chunk = None
                    
                    for chunk in stream:
                        last_chunk = chunk
                        delta = chunk.choices[0].delta.content
                        if not delta:
                            yield chunk
                            continue
                        
                        # Process tokens through sanitizer
                        for safe_text in sanitizer.process(delta):
                            chunk.choices[0].delta.content = safe_text
                            yield chunk
                            
                    # Flush remaining buffer
                    if last_chunk:
                        for safe_text in sanitizer.flush():
                            last_chunk.choices[0].delta.content = safe_text
                            yield last_chunk

    class SentinelAsyncOpenAI:
        """
        Wrapper for the Async OpenAI Client to automatically apply guardrails.
        """
        def __init__(self, engine: GuardrailsEngine, **client_kwargs):
            self.engine = engine
            self._client = AsyncOpenAI(**client_kwargs)
            self.chat = self.ChatWrapper(self._client, self.engine)

        class ChatWrapper:
            def __init__(self, client: AsyncOpenAI, engine: GuardrailsEngine):
                self.completions = self.CompletionsWrapper(client, engine)

            class CompletionsWrapper:
                def __init__(self, client: AsyncOpenAI, engine: GuardrailsEngine):
                    self._client = client
                    self._engine = engine
                
                async def create(self, **kwargs) -> Union[ChatCompletion, AsyncGenerator[ChatCompletionChunk, None]]:
                    # 1. Scan Input Messages (Async)
                    messages = kwargs.get("messages", [])
                    for msg in messages:
                        if "content" in msg and isinstance(msg["content"], str):
                            result = await self._engine.validate_async(msg["content"])
                            if not result.valid and result.action == "blocked":
                                raise ValueError(f"Sentinel Blocked Input: {result.reason}")
                            msg["content"] = result.sanitized_text

                    # 2. Call Original API
                    response = await self._client.chat.completions.create(**kwargs)

                    # 3. Handle Response
                    if kwargs.get("stream", False):
                        return self._stream_wrapper(response)
                    else:
                        return self._handle_sync_response(response)

                def _handle_sync_response(self, response: ChatCompletion) -> ChatCompletion:
                    # Note: Output validation is CPU bound, so sync check is fine even in async flow
                    # Or we could await a run_in_executor if strict async needed. 
                    # For simplicity, we use the engine's sync check here as we have the full text.
                    content = response.choices[0].message.content
                    if content:
                        result = self._engine.validate_output(content)
                        if not result.valid and result.action == "blocked":
                            raise ValueError(f"Sentinel Blocked Output: {result.reason}")
                        
                        if result.sanitized_text != content:
                            response.choices[0].message.content = result.sanitized_text
                    return response

                async def _stream_wrapper(self, stream) -> AsyncGenerator[ChatCompletionChunk, None]:
                    sanitizer = StreamSanitizer(self._engine)
                    last_chunk = None
                    
                    async for chunk in stream:
                        last_chunk = chunk
                        delta = chunk.choices[0].delta.content
                        if not delta:
                            yield chunk
                            continue
                        
                        # Process tokens through sanitizer
                        for safe_text in sanitizer.process(delta):
                            chunk.choices[0].delta.content = safe_text
                            yield chunk
                            
                    # Flush remaining buffer
                    if last_chunk:
                        for safe_text in sanitizer.flush():
                            last_chunk.choices[0].delta.content = safe_text
                            yield last_chunk

else:
    class SentinelOpenAI:
        def __init__(self, *args, **kwargs):
             raise ImportError("openai not installed. Run `pip install openai`")
    class SentinelAsyncOpenAI:
         def __init__(self, *args, **kwargs):
             raise ImportError("openai not installed. Run `pip install openai`")
