from pathlib import Path
from ollama import chat


question = """pip install ollama
"""


context = ""

for file in Path("knowledge").glob("*.txt"):
    context += file.read_text()
    context += "\n\n"


response = chat(
    model="qwen2.5:7b",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful university IT support assistant."
        },
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion:\n{question}"
        }
    ]
)


print(
    "Context characters:",
    len(context)
)

print(response.message.content)