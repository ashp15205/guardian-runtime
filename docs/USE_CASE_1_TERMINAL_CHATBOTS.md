# Use Case 1: Terminal Chatbots & CLI Tools

If you are building a command-line interface (CLI) coding assistant, local chatbot, or terminal script that interacts with an LLM, GuardianRuntime Runtime is the perfect drop-in security layer.

## The Problem
When developers build terminal chatbots, they typically send raw `input()` directly to the OpenAI or Anthropic SDKs. If the user accidentally pastes an environment variable containing an AWS key, or pastes a massive block of unoptimized text, it gets sent directly to the LLM. This leads to leaked credentials and high API costs.

## How GuardianRuntime Solves This
GuardianRuntime acts as an invisible wrapper around your LLM calls. It runs entirely locally on your machine, processing the input *before* the network request is made.

### Step 1: Create a Development Policy
For terminal applications, GuardianRuntime includes a special **Interactive Mode** (`warn_ask`). This mode provides an incredible Developer Experience (DX) by pausing the terminal to warn the user if a violation is found, rather than crashing the script.

```yaml
# policies/dev.yaml
version: "1.0"
name: "dev-chatbot"

interactive_mode: warn_ask  # Pauses and asks [y/N] on violations

agents:
  default:
    llm:
      provider: gemini
      default_model: gemini-2.5-flash
    input_guard:
      pii_detection: true
      jailbreak_detection: true
      pii_action: block
```

### Step 2: The Implementation
Instead of using the standard LLM provider SDK, you simply import GuardianRuntime. Because GuardianRuntime natively wraps `openai`, `anthropic`, and `google-genai`, you don't need to change how you manage API keys.

```python
import os
import sys
from guardian_runtime import GuardianRuntime

# Ensure the developer has their API key set
if not os.environ.get("GEMINI_API_KEY"):
    print("Please set GEMINI_API_KEY")
    sys.exit(1)

# Initialize GuardianRuntime with the dev policy
guardian_runtime = GuardianRuntime.from_policy("policies/dev.yaml")
chat_history = []

print("Chatbot started. Type 'quit' to exit.")

while True:
    user_input = input("You: ").strip()
    if user_input.lower() == 'quit':
        break

    chat_history.append({"role": "user", "content": user_input})

    # GuardianRuntime intercepts the request here
    response = guardian_runtime.complete(messages=chat_history)

    if response.blocked:
        # If the user typed 'n' at the warn prompt, it gets blocked
        print("Bot: Message blocked by security policies.")
        chat_history.pop() # Remove the malicious prompt from history
    else:
        print(f"Bot: {response.content}")
        chat_history.append({"role": "assistant", "content": response.content})
```

## Technical Flow
1. **Input Generation**: User types `My Aadhaar is 0000 0000 0000`.
2. **Local Scan**: `guardian_runtime.complete()` parses the text using its regex engine. It detects `PIIType.AADHAAR`.
3. **Interactive Prompt**: Because `interactive_mode: warn_ask` is set, GuardianRuntime temporarily halts execution. It prints to `sys.stderr`:
   > `🚨 Do you still want to send this prompt to Gemini? [y/N]`
4. **Resolution**: If the user presses `n`, GuardianRuntime returns a `GuardianRuntimeResponse` with `blocked=True` instantly, spending $0.00.

## FinOps Tracking
At the end of your terminal session, you can run `guardian_runtime status` in another tab to see exactly how many tokens the chatbot consumed and how much GuardianRuntime's whitespace normalization saved you.
