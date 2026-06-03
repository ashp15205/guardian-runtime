"""Guardian quickstart — Gemini (free), Anthropic, or OpenAI."""

import os

from guardian import Guardian, scan_pii


def main() -> None:
    result = scan_pii("My Aadhaar is 2345 6789 0123")
    print(f"Scanner: blocked={result.blocked} type={result.type}")

    providers = [
        ("GEMINI_API_KEY", "GOOGLE_API_KEY", "policies/gemini.yaml", "Gemini"),
        ("ANTHROPIC_API_KEY", None, "policies/anthropic.yaml", "Claude"),
        ("OPENAI_API_KEY", None, "policies/minimal.yaml", "OpenAI"),
    ]

    for primary, fallback, policy_path, label in providers:
        if os.environ.get(primary) or (fallback and os.environ.get(fallback)):
            guardian = Guardian.from_policy(policy_path)
            response = guardian.complete(
                messages=[{"role": "user", "content": "Say hello in one word."}],
            )
            if response.blocked:
                print(f"{label} blocked:", response.violations)
            else:
                print(f"{label} ({response.provider}/{response.model}):", response.content)
                if response.optimization:
                    print(f"  Token savings: {response.optimization['savings_pct']:.0%}")
            return

    print("Set one of: GEMINI_API_KEY (free), ANTHROPIC_API_KEY, OPENAI_API_KEY")


if __name__ == "__main__":
    main()
