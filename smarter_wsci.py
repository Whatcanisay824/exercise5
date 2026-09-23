from pathlib import Path
from ollama import chat
import json


question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""


service_status = {
    "wifi": "operational"
}

state = {
    "problem": question,
    "wifi_status": "operational",
    "wifi_check": True
}

with open("state.json", "w") as file:
    json.dump(
        state,
        file,
        indent=2
    )

with open("state.json", "r") as file:
    state = json.load(file)

print(state)


def select_context(question):
    question_lower = question.lower()
    selected = []

    if "password" in question_lower:
        selected.append("knowledge/password_changes.txt")

    if "wi-fi" in question_lower or "wifi" in question_lower:
        selected.append("knowledge/wifi_setup.txt")

    if "windows" in question_lower:
        selected.append("knowledge/wifi_setup.txt")

    if "phone" in question_lower or "works" in question_lower:
        selected.append("knowledge/service_status.txt")

    selected = list(set(selected))
    selected.sort()

    return selected


selected_files = select_context(question)
print("Selected files:", selected_files)


context = ""

for file_name in selected_files:
    file_path = Path(file_name)
    context += file_path.read_text()
    context += "\n\n"


def compress_context(context, question):
    prompt = f"""
You are helping a university IT support assistant.

Question:
{question}

Here is some reference information:
{context}

Please extract only the information that is useful for answering the question.
Write a short summary. Do not add new facts.
"""

    response = chat(
        model="qwen2.5:7b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.message.content


compressed_context = compress_context(context, question)


print("Compressed context characters:", len(compressed_context))
print("Compressed context:")
print(compressed_context)


response = chat(
    model="qwen2.5:7b",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful university IT support assistant."
        },
        {
            "role": "user",
            "content": f"""
Use the following information to answer the student's question.

Information:
{compressed_context}

Student question:
{question}

Please answer in a clear and structured way.
"""
        }
    ]
)


print(response.message.content)


state["answer"] = response.message.content
state["compressed_context"] = compressed_context
state["selected_files"] = selected_files

with open("state.json", "w") as file:
    json.dump(
        state,
        file,
        indent=2
    )


with open("state.json", "r") as file:
    saved_state = json.load(file)

final_context = f"""
Problem: {saved_state["problem"]}
Wi-Fi status: {saved_state["wifi_status"]}
Selected files: {saved_state["selected_files"]}
Compressed context: {saved_state["compressed_context"]}
"""

final_response = chat(
    model="qwen2.5:7b",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful university IT support assistant."
        },
        {
            "role": "user",
            "content": f"""
Use this saved state to give a short final answer.

{final_context}

Student question:
{question}
"""
        }
    ]
)

print("Final answer:")
print(final_response.message.content)