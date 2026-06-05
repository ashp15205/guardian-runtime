# Use Case 1: Terminal Chatbots & CLI Tools

If you are building a command-line interface (CLI) coding assistant, local chatbot, or terminal script that interacts with an LLM, GuardianRuntime Runtime is the perfect drop-in security layer.

## The Problem
When developers build terminal chatbots, they typically send raw `input()` directly to the OpenAI or Anthropic SDKs. If the user accidentally pastes an environment variable containing an AWS key, or pastes a massive block of unoptimized text, it gets sent directly to the LLM. This leads to leaked credentials and high API costs.

## How GuardianRuntime Solves This
GuardianRuntime acts as an invisible wrapper around your LLM calls. It runs entirely locally on your machine, processing the input *before* the network request is made.

### Step 1: Zero-Config Protection
For terminal applications, GuardianRuntime works out of the box with zero configuration. It defaults to a strict $10/day budget and intercepts AWS keys or secrets instantly.

(Optional) If you want to use the Interactive "Warn and Ask" mode, you can still provide a `policy.yaml`:
```yaml
version: "1.0"
interactive_mode: warn_ask  # Pauses and asks [y/N] on violations
```

### Step 2: The Implementation
Instead of using the standard LLM provider SDK, you simply import GuardianRuntime. Because GuardianRuntime natively wraps `openai`, `anthropic`, and `google-genai`, you don't need to change how you manage API keys.

```python
import os
import sys
from guardian_runtime import GuardianRuntime, GuardianRuntimeBlockedError

# Ensure the developer has their API key set
if not os.environ.get("GEMINI_API_KEY"):
    print("Please set GEMINI_API_KEY")
    sys.exit(1)

# Initialize GuardianRuntime with zero-config (or pass policy="policy.yaml")
guardian_runtime = GuardianRuntime()
chat_history = []

print("Chatbot started. Type 'quit' to exit.")

while True:
    user_input = input("You: ").strip()
    if user_input.lower() == 'quit':
        break

    chat_history.append({"role": "user", "content": user_input})

    # GuardianRuntime intercepts the request here
    try:
        response = guardian_runtime.complete(messages=chat_history)
        print(f"Bot: {response.content}")
        chat_history.append({"role": "assistant", "content": response.content})
    except GuardianRuntimeBlockedError as e:
        # Fails fast and safely handles the block
        print(f"Bot: Message blocked by security policies. {e.response.violations[0].type}")
        chat_history.pop() # Remove the malicious prompt from history
```

## Technical Flow
1. **Input Generation**: User types `My AWS key is AKIA...`.
2. **Local Scan**: `guardian_runtime.complete()` parses the text using its regex engine. It detects the secret.
3. **Instant Rejection**: GuardianRuntime throws a `GuardianRuntimeBlockedError` locally, preventing the prompt from reaching the network.

## Session Analytics Tracking
At the end of your terminal session, you can run `guardian_runtime analytics` in another tab to see exactly how many tokens the chatbot consumed and how much the session cost you.
