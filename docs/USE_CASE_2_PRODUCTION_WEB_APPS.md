# Use Case 2: Production Web Apps (FastAPI, Flask, Django)

When deploying a consumer-facing AI application to a cloud server (AWS, Heroku, Vercel), security and latency are paramount. GuardianRuntime Runtime is designed to be the primary gateway between your production web server and your LLM provider.

## The Problem
If you deploy an AI feature on the web without an input guardrail, malicious actors can perform Prompt Injections (DAN attacks) to hijack your bot, or try to trick it into leaking system prompts. Additionally, routing traffic through a third-party API firewall (like Cloudflare AI Gateway) adds 200ms+ of network latency to every single chat message.

## How GuardianRuntime Solves This
GuardianRuntime is a **Local-First SDK**. When you install it on your FastAPI server, the firewall runs entirely inside your Python process memory. It adds ~2ms of processing time and requires zero network hops to validate a prompt.

### Step 1: Create a Production Policy
In production, you **must not** use interactive mode. Your server has no physical keyboard attached to it, so if a warning prompt appears, the server thread will hang forever waiting for `[y/N]`. We use `interactive_mode: off` to ensure strict, silent blocking.

```yaml
# policies/production.yaml
version: "1.0"
name: "production-app"

interactive_mode: off  # Strict silent blocking for headless servers

agents:
  default:
    llm:
      provider: openai
      default_model: gpt-4o-mini
    input_guard:
      pii_detection: true
      jailbreak_detection: true
      pii_action: block
    optimizer:
      enabled: true
      # Max token limits prevent users from pasting books and bankrupting you
    cost:
      max_input_tokens: 4000
```

### Step 2: FastAPI Integration
Integrating GuardianRuntime into an API route is virtually identical to using the standard OpenAI SDK, but with automatic governance.

```python
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from guardian_runtime import GuardianRuntime

app = FastAPI()

# GuardianRuntime is instantiated once at startup
guardian_runtime = GuardianRuntime.from_policy("policies/production.yaml")

class ChatRequest(BaseModel):
    message: str

@app.post("/api/v1/chat")
async def chat_endpoint(request: ChatRequest):
    # GuardianRuntime runs the InputGuard (PII/Jailbreak) and Optimizer
    response = guardian_runtime.complete(
        messages=[{"role": "user", "content": request.message}]
    )

    # 1. Handle Security Violations
    if response.blocked:
        violation_types = [v.type for v in response.violations]
        raise HTTPException(
            status_code=400, 
            detail=f"Request blocked due to security policies: {violation_types}"
        )

    # 2. Return the safe response to the frontend
    return {
        "reply": response.content,
        "metrics": {
            "tokens_used": response.input_tokens + response.output_tokens,
            "cost_usd": response.estimated_cost_usd
        }
    }
```

## Technical Flow
1. **Web Request**: A user hits the `/api/v1/chat` endpoint with a jailbreak attempt (`Ignore all previous instructions...`).
2. **Memory Scan**: `guardian_runtime.complete()` passes the prompt through the `InputGuard`. The jailbreak regex matches the malicious string.
3. **Instant Rejection**: Because `interactive_mode` is `off`, GuardianRuntime immediately aborts. It does NOT call the OpenAI API.
4. **API Response**: The FastAPI server returns a `400 Bad Request` to the frontend in <5 milliseconds. $0.00 API cost incurred.

## Production Advantages
- **Zero Latency**: No round-trips to external security APIs.
- **Fail-Safe**: If GuardianRuntime crashes, standard Python error handling applies. You don't have to worry about a third-party security service going down and taking your app with it.
- **Data Privacy**: Your user's prompts never touch a third-party security server; they go straight from your RAM to the LLM.
