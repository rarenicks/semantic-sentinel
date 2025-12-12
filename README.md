# Secure GenAI Gateway

A robust, lightweight security proxy for Large Language Models (LLMs) built with **FastAPI**. This middleware sits between your client application and the LLM (e.g., Ollama, LocalAI), ensuring that all inputs are sanitized and validated before processing.

## Key Features

- **🛡️ PII Redaction**: Automatically detects and redacts sensitive information (Emails, Phone Numbers) from prompts before logging or forwarding.
- **🚫 Injection Blocking**: Identifies and blocks common prompt injection and jailbreak attempts (e.g., "Ignore previous instructions").
- **📝 Audit Logging**: Asynchronous, non-blocking logging of all requests, verdicts, and latency metrics to valid SQLite storage.
- **⚡ High Performance**: Built on FastAPI and `httpx` for minimal latency overhead.

## Quick Start

### Prerequisites
- Python 3.10+
- A running local LLM (e.g., [Ollama](https://ollama.com/) at `http://localhost:11434`)

### Installation

1. Clone the repository and set up a virtual environment:
   ```bash
   git clone https://github.com/rarenicks/secure-llm-gateway.git
   cd secure-llm-gateway
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   The project comes with a default `.env` configuration. Ensure `TARGET_LLM_URL` points to your local model instance.

### Running the Proxy

Start the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API is now available at `http://localhost:8000/v1/chat/completions`, mimicking the standard OpenAI API format.

## Verification

A verification script is included to test the security guardrails.

```bash
python verify_proxy.py
```

This will run three automated tests:
1.  **Safe Request**: Should pass through to the LLM.
2.  **PII Request**: Should be processed but redacted in logs/upstream.
3.  **Malicious Request**: Should be blocked immediately with a 400 error.

## Architecture

- **`main.py`**: Core application logic and proxy handling.
- **`guardrails_config.py`**: Configurable rules for PII and injection detection.
- **`logger.py`**: Structured audit logging system.

## License

MIT License
