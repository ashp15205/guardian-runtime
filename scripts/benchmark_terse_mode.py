import os
import sys

try:
    import google.generativeai as genai
except ImportError:
    print("Please install the Gemini SDK: pip install google-generativeai")
    sys.exit(1)

PROMPTS = [
    "Write a Python script to parse a CSV file and output JSON.",
    "Explain the difference between threading and multiprocessing in Python.",
    "How do I set up a basic React component with hooks?",
    "Refactor this code to be more efficient: `for i in range(len(lst)): print(lst[i])`",
    "What is the best way to handle errors in an Express.js app?",
    "Write a bash script to find all files larger than 100MB and delete them.",
    "Explain how a JWT works and how to securely store it.",
    "Write a SQL query to find the top 5 customers who spent the most money.",
    "How does Garbage Collection work in Go?",
    "Create a Dockerfile for a Node.js web application."
]

PROMPTS = PROMPTS[:3]

TERSE_SYSTEM_PROMPT = (
    "You are a highly efficient technical assistant. Be concise and direct. "
    "Provide brief, clear reasoning alongside the required code. "
    "Do not use conversational filler, pleasantries, or repetitive summaries. "
    "Maintain 100% technical accuracy while minimizing unnecessary wordiness."
)

def run_benchmark():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Please set the GEMINI_API_KEY environment variable to run the benchmark.")
        return

    genai.configure(api_key=api_key)

    print(f"Starting Terse Mode Benchmark across {len(PROMPTS)} developer prompts using gemini-3.1-flash-lite...\n")
    normal_tokens = 0
    terse_tokens = 0

    # Model 1: Normal Agent
    normal_model = genai.GenerativeModel('gemini-3.1-flash-lite')
    
    # Model 2: Guardian Terse Mode Agent
    terse_model = genai.GenerativeModel(
        'gemini-3.1-flash-lite',
        system_instruction=TERSE_SYSTEM_PROMPT
    )

    for i, prompt in enumerate(PROMPTS):
        print(f"Prompt {i+1}/{len(PROMPTS)}: {prompt[:40]}...")
        
        try:
            # 1. Normal Call
            res_normal = normal_model.generate_content(prompt)
            normal_count = res_normal.usage_metadata.candidates_token_count
            normal_tokens += normal_count
            print("\n[NORMAL AGENT OUTPUT]------------------------------------")
            print(res_normal.text.strip())
            print("---------------------------------------------------------")

            # 2. Terse Call
            res_terse = terse_model.generate_content(prompt)
            terse_count = res_terse.usage_metadata.candidates_token_count
            terse_tokens += terse_count
            print("\n[GUARDIAN TERSE MODE OUTPUT]-----------------------------")
            print(res_terse.text.strip())
            print("---------------------------------------------------------")

            reduction = ((normal_count - terse_count) / normal_count) * 100 if normal_count > 0 else 0
            print(f"\n=> Tokens Used: Normal ({normal_count}) vs Terse ({terse_count}) | SAVED: {reduction:.1f}%\n")
        except Exception as e:
            print(f"  -> Error calling API: {e}")

    print("====================================")
    print("        BENCHMARK RESULTS           ")
    print("====================================")
    print(f"Total Normal Output Tokens: {normal_tokens}")
    print(f"Total Terse Output Tokens:  {terse_tokens}")
    
    if normal_tokens > 0:
        savings = ((normal_tokens - terse_tokens) / normal_tokens) * 100
        print(f"\n=> 🚀 FINAL TOKEN REDUCTION: {savings:.2f}%")
        print("====================================")

if __name__ == "__main__":
    run_benchmark()
