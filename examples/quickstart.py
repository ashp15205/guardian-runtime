"""Guardian quickstart — use Gemini (free) or OpenAI."""

import os

from guardian import Guardian, scan_pii


def main() -> None:
    # Always works without an API key
    result = scan_pii("My Aadhaar is 2345 6789 0123")
    print(f"Scanner: blocked={result.blocked} type={result.type}")

    # --- Option A: Google Gemini (free tier) ---
    # export GEMINI_API_KEY=your_key  # https://aistudio.google.com/apikey
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        guardian = Guardian.from_policy("policies/gemini.yaml")
        response = guardian.complete(
            messages=[{"role": "user", "content": "Say hello in one word."}],
        )
        if response.blocked:
            print("Blocked:", response.violations)
        else:
            print(f"Gemini ({response.model}):", response.content)
        return

    # --- Option B: OpenAI (paid) ---
    # export OPENAI_API_KEY=sk-...
    if os.environ.get("OPENAI_API_KEY"):
        guardian = Guardian.from_policy("policies/minimal.yaml")
        response = guardian.complete(
            messages=[{"role": "user", "content": "Say hello in one word."}],
        )
        if response.blocked:
            print("Blocked:", response.violations)
        else:
            print(f"OpenAI ({response.model}):", response.content)
        return

    print("Set GEMINI_API_KEY (free) or OPENAI_API_KEY to run a live LLM test.")


if __name__ == "__main__":
    main()
