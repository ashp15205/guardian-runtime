# Use Case 2: Production Web Apps (FastAPI, Flask, Django)

When deploying a consumer-facing AI application to a cloud server (AWS, Heroku, Vercel), security and latency are paramount. GuardianRuntime Runtime is designed to be the primary gateway between your production web server and your LLM provider.

## The Problem
If you deploy an AI feature on the web without an input guardrail, malicious actors can perform Prompt Injections (DAN attacks) to hijack your bot, or try to trick it into leaking system prompts. Additionally, routing traffic through a third-party API firewall (like Cloudflare AI Gateway) adds 200ms+ of network latency to every single chat message.

## How GuardianRuntime Solves This
GuardianRuntime is a **Local-First SDK**. When you install it on your FastAPI server, the firewall runs entirely inside your Python process memory. It adds ~2ms of processing time and requires zero network hops to validate a prompt.

### Step 1: Zero-Config Production
In production, you **must not** use interactive mode, as it will hang the server. GuardianRuntime defaults to strict, silent blocking out of the box (`interactive_mode: off`), making it perfectly safe for production deployment without any YAML file.

(Optional) If you want to customize budget limits, provide a `policy.yaml`:
```yaml
version: "1.0"
agents:
  default:
    cost:
      max_input_tokens: 4000  # Prevent users from pasting books and bankrupting you
      daily_budget: 100.00
```

### Step 2: FastAPI Integration
Integrating GuardianRuntime into an API route is virtually identical to using the standard OpenAI SDK, but with automatic governance.

```python
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from guardian_runtime import GuardianRuntime, GuardianRuntimeBlockedError

app = FastAPI()

# GuardianRuntime is instantiated once at startup (zero-config)
guardian_runtime = GuardianRuntime()

class ChatRequest(BaseModel):
    message: str

@app.post("/api/v1/chat")
async def chat_endpoint(request: ChatRequest):
    # GuardianRuntime runs the InputGuard (PII/Jailbreak), Optimizer, and Budget Check
    try:
        response = guardian_runtime.complete(
            messages=[{"role": "user", "content": request.message}]
        )
        
        # Return the safe response to the frontend
        return {
            "reply": response.content,
            "metrics": {
                "tokens_used": response.input_tokens + response.output_tokens,
                "cost_usd": response.estimated_cost_usd
            }
        }
    except GuardianRuntimeBlockedError as e:
        violation_types = [v.type for v in e.response.violations]
        raise HTTPException(
            status_code=400, 
            detail=f"Request blocked due to security policies: {violation_types}"
        )
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
