# Forward Deployed Engineer (FDE) Assessment

## Overview

This project implements a practical assessment for a **Forward Deployed Engineer / AI Integration Engineer** role.

The assessment covers:

* MCP server development
* Authentication and authorization
* LLM streaming and PII redaction
* Rate limiting and model fallback
* Async processing
* JSON-RPC communication
* Automated testing


Each task is implemented independently with a focus on correctness, security, reliability, and testability.

---

## Assessment Tasks

### Task 1 — Enterprise Claims MCP Server

Build an MCP server exposing:

* `get_claim_record`
* `update_claim_status`

Requirements:

* Python MCP SDK
* Pydantic validation
* Claim ID format: `CLM-XXXXX`
* Valid claim statuses
* STDIO transport
* JSON-RPC messages only on `stdout`
* Logs on `stderr`

### Task 2 — MCP Security Gateway

Build an HTTP/JSON-RPC gateway providing:

* Bearer-token authentication
* `claims_admin` and `claims_viewer` roles
* `tools/list` forwarding
* Role-based authorization
* Protection for `claims_admin_*` tools
* `-32001 Unauthorized Tool Call`
* No downstream call for unauthorized requests

### Task 3 — LLM Streaming Guardrail

Build a streaming gateway that detects and redacts:

* Email addresses
* SSNs
* Credit card numbers

Sensitive information must be replaced with:

```text
[REDACTED]
```

The implementation must handle PII split across chunks without buffering the complete response.

### Task 4 — Rate Limiting & Model Fallback

Implement:

* Tenant-level token rate limiting
* `50,000` tokens/minute
* Sliding-window behavior
* SQLite persistence
* `3000 ms` primary model timeout
* Fallback on HTTP `429`
* Fallback on timeout
* Sanitized errors
* Concurrent request safety

---

# Project Structure

```text
fde-assessment/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── task1-mcp-server/
│   ├── __init__.py
│   ├── server.py
│   ├── models.py
│   └── tests.py
│
├── task2-mcp-gateway/
│   ├── __init__.py
│   ├── gateway.py
│   ├── auth.py
│   ├── policy.py
│   └── tests.py
│
├── task3-llm-guardrail/
│   ├── __init__.py
│   ├── gateway.py
│   ├── pii_patterns.py
│   ├── stream_redactor.py
│   └── tests.py
│
└── task4-model-router/
    ├── __init__.py
    ├── router.py
    ├── rate_limiter.py
    ├── usage_store.py
    └── tests.py
```

### Folder Responsibilities

| Folder                | Purpose                                        |
| --------------------- | ---------------------------------------------- |
| `task1-mcp-server`    | MCP server and claim operations                |
| `task2-mcp-gateway`   | Authentication, authorization, and MCP proxy   |
| `task3-llm-guardrail` | Streaming PII detection and redaction          |
| `task4-model-router`  | Rate limiting, persistence, and model fallback |

---

# Technology Stack

* Python
* Official Python MCP SDK
* FastAPI
* Pydantic
* HTTPX
* Pytest
* pytest-asyncio
* SQLite

---

# Installation

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Run Tests

Run all tests:

```bash
python -m pytest -v
```

Run individual tasks:

```bash
python -m pytest task1-mcp-server/tests.py -v
python -m pytest task2-mcp-gateway/tests.py -v
python -m pytest task3-llm-guardrail/tests.py -v
python -m pytest task4-model-router/tests.py -v
```

---

# Engineering Focus

The implementation emphasizes:

* Clean and maintainable architecture
* Strict validation
* Secure authorization
* Bounded streaming state
* Tenant isolation
* Concurrency safety
* Model fallback and resilience
* Automated testing
* Sanitized client-facing errors

No API keys, credentials, stack traces, or internal implementation details should be exposed to clients or committed to the repository.

---

# Submission Checklist

* [ ] All tasks implemented
* [ ] Tests passing
* [ ] `requirements.txt` included
* [ ] No secrets committed
* [ ] No generated database files committed
* [ ] MCP `stdout` contains protocol messages only
* [ ] Unauthorized requests are blocked
* [ ] PII is redacted
* [ ] Rate limiting works per tenant
* [ ] Fallback behavior works correctly
* [ ] Errors are sanitized
"# MCP-LLM-Gateway-FDE-Assessment" 
