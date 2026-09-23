from pathlib import Path
from ollama import chat


question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""

selected_files = [
    "knowledge/password_changes.txt",
    "knowledge/wifi_setup.txt",
    "knowledge/service_status.txt"
]


context = ""

for file_name in selected_files:
    file_path = Path(file_name)
    context += file_path.read_text()
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