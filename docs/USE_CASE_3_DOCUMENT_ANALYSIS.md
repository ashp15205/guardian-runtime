# Use Case 3: Document Analysis ("Chat with PDF")

A major trend in generative AI is Retrieval-Augmented Generation (RAG) and document analysis—allowing users to upload PDFs, DOCX files, or spreadsheets and ask questions about them.

## The Problem
PDFs are binary files heavily bloated with layout metadata, font configurations, and hidden formatting. When developers use basic text extractors (like `PyPDF2`) or pass raw documents directly to an LLM, the token counts are astronomical. This leads to massive API bills and slow response times due to bloated context windows.

## How GuardianRuntime Solves This
GuardianRuntime includes a built-in `DocumentConverter` powered by Microsoft's `MarkItDown` engine. It intercepts heavy binary files and automatically compresses them into clean, token-efficient Markdown *before* they are sent to the LLM.

### The Implementation
You can use the GuardianRuntime SDK to handle the file conversion and the LLM interaction in just a few lines of code.

```python
import os
from guardian_runtime import GuardianRuntime, convert_document

guardian_runtime = GuardianRuntime.from_policy("policies/production.yaml")

def analyze_document(file_path: str):
    if not os.path.exists(file_path):
        return "File not found."

    print(f"Processing {file_path}...")
    
    # 1. Convert the binary document to clean Markdown
    result = convert_document(file_path)
    print(f"Compressed {result.original_size_bytes} bytes down to {result.markdown_tokens} tokens.")

    # 2. Inject the clean markdown into the System Prompt
    chat_history = [
        {
            "role": "system",
            "content": f"You are a helpful analyst. Base your answers ONLY on this document:\n\n{result.markdown}"
        }
    ]

    # 3. Ask the LLM to summarize it
    chat_history.append({"role": "user", "content": "Please write a 3-bullet point summary of this document."})
    
    # GuardianRuntime ensures the prompt is safe and optimized before sending
    response = guardian_runtime.complete(messages=chat_history)

    if response.blocked:
        return "Analysis blocked due to security violations in the document."
    
    return response.content
```

## Technical Flow
1. **Ingestion**: The developer passes a 250KB PDF to `convert_document()`.
2. **Extraction & Compression**: GuardianRuntime's engine strips the binary bloat and extracts purely the semantic structure (headers, tables, paragraphs), outputting lightweight Markdown.
3. **Execution**: The Markdown is injected into the LLM prompt.
4. **Governance**: `guardian_runtime.complete()` ensures that the extracted text doesn't secretly contain PII (if PII blocking is enabled in the policy) before it's passed to the AI.

## Benchmark Example
In internal testing of an IEEE Academic Paper (PDF):
- **Original Size**: 247,159 bytes
- **GuardianRuntime Output**: 634 tokens
- **Result**: The LLM receives purely the semantic content of the paper, saving significant token budget while retaining perfect context.

## Supported Formats
GuardianRuntime's document pipeline automatically supports:
- PDF (`.pdf`)
- Word (`.docx`)
- Excel (`.xlsx`, `.csv`)
- PowerPoint (`.pptx`)
- HTML (`.html`)
