# Changelog

## [0.1.0] - 2025-12-29

### Added
- **Async Support**: Full async/await support with `validate_async()` for non-blocking operations
  - CPU-bound tasks (semantic encoding, Presidio) offloaded to executors
  - Achieved ~150 req/s throughput in concurrent scenarios
- **Streaming Sanitization**: `StreamSanitizer` class for real-time content filtering
  - Sentence-boundary buffering maintains semantic context
  - Works seamlessly with streaming LLM responses
- **LangChain Integration**: Native `SentinelRunnable` for pipeline compatibility
  - Drop-in Runnable for LangChain chains: `chain = prompt | sentinel | llm`
  - Follows LangChain conventions (raises `ValueError` on blocked content)
- **OpenAI Integration**: Native wrappers for OpenAI SDK with automatic guardrails
  - `SentinelOpenAI` (sync) and `SentinelAsyncOpenAI` (async)
  - Supports streaming responses with real-time sanitization
  - Drop-in replacement for `openai.OpenAI`/`openai.AsyncOpenAI`
- **LlamaIndex Integration**: `SentinelNodePostprocessor` for RAG pipelines
  - Sanitizes retrieved documents before LLM processing
  - Configurable to either redact or drop blocked nodes
- **Utility Functions**: Added `download_spacy_model()` helper for easier setup
- **Presidio Async Wrapper**: `scan_and_redact_async()` for non-blocking PII scanning
- **Optional Dependencies**: 
  - Individual packages: `openai`, `llamaindex`, `langchain`
  - All integrations: `pip install semantic-sentinel[integrations]`
- **Examples**: Comprehensive demos for async, streaming, LangChain, and OpenAI integration
- **Tests**: End-to-end integration test suite (`tests/test_integrations.py`)

### Changed
- Updated `README.md` with installation instructions and async usage examples
- Enhanced `__init__.py` to export new utilities and integrations

## [0.0.1] - 2025-12-28
### Added
- Initial release of Semantic Sentinel Framework.
- Core Engine with Regex, Semantic Blocking, and PII Redaction.
- Plugin Support (LangKit).
- Configuration-driven architecture (YAML profiles).
