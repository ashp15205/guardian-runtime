import os
from google import genai
client = genai.Client()
for m in client.models.list():
    if "gemini" in m.name:
        print(m.name)
