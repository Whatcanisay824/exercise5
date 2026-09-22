from pathlib import Path
from ollama import chat
import json
import re
from datetime import datetime, timezone

MODEL = "qwen2.5:7b"

KNOWLEDGE_DIR = Path("knowledge")

question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""

# SELECT: use Python keyword rules instead of an AI call.
FILE_KEYWORDS = {
    "classroom_projectors.txt": [
        "projector", "display", "hdmi", "usb-c", "classroom", "teaching room"
    ],
    "email_setup.txt": [
        "email", "webmail", "mail", "smtp", "imap", "outlook"
    ],
    "password_changes.txt": [
        "password", "changed", "change", "credential", "credentials",
        "authentication", "login"
    ],
    "printing.txt": [
        "print", "printer", "printing", "queue", "credit"
    ],
    "service_status.txt": [
        "status", "operational", "outage", "service", "eduroam",
        "wi-fi", "wifi", "campus"
    ],
    "vpn.txt": [
        "vpn", "remote", "off-campus", "outside campus"
    ],
    "wifi_setup.txt": [
        "wi-fi", "wifi", "eduroam", "wireless", "network",
        "windows", "macos", "android", "ios", "connect", "campus"
    ],
}


def ask_qwen(messages, model=MODEL):
    response = chat(model=model, messages=messages)
    return response.message.content


def select_context(question):
    """Select relevant knowledge files using keyword matching."""
    q = question.lower()
    selected = []

    for file in sorted(KNOWLEDGE_DIR.glob("*.txt")):
        keywords = FILE_KEYWORDS.get(file.name, [])
        if any(keyword.lower() in q for keyword in keywords):
            selected.append(file)

    if not selected:
        fallback = KNOWLEDGE_DIR / "service_status.txt"
        if fallback.exists():
            selected = [fallback]

    return selected


selected_files = select_context(question)

print("Selected files:")
for file in selected_files:
    print(" -", file)

context = ""
for file in selected_files:
    context += f"\n\n--- {file.name} ---\n"
    context += file.read_text(encoding="utf-8")

print("Raw context characters:", len(context))


# COMPRESS: ask Qwen to keep only relevant facts.
def compress_context(context, question):
    prompt = f"""You are compressing a university IT knowledge base.

Student question:
{question}

Relevant knowledge base text:
{context}

Task:
Extract only the facts that are relevant to diagnosing this question.
Do not invent facts. Keep exact service names, conditions, and steps.
Return concise bullet points only.
"""
    return ask_qwen([
        {
            "role": "system",
            "content": (
                "You compress context for a university IT support assistant. "
                "Return only relevant compressed facts."
            )
        },
        {"role": "user", "content": prompt},
    ])


compressed_context = compress_context(context, question)

print("Compressed context characters:", len(compressed_context))
print("Compressed context:")
print(compressed_context)


def parse_json_object(text):
    """Extract a JSON object from the model output."""
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    # Fix invalid single backslashes that break JSON parsing
    text = text.replace("\\", "\\\\")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

    return {"raw_response": text}


def answer_with_compressed_context(compressed_context, question):
    prompt = f"""Use the compressed context to answer the student's IT problem.

Student question:
{question}

Compressed context:
{compressed_context}

Return ONLY valid JSON in this exact structure:
{{
  "diagnosis": "short diagnosis",
  "likely_cause": "why this happens",
  "immediate_steps": ["step 1", "step 2", "step 3"],
  "why_phone_works": "explanation",
  "escalation": "what to report if it still fails",
  "files_used": ["password_changes.txt", "wifi_setup.txt"]
}}

Rules for files_used:
- Only list the knowledge base text files you used (e.g., password_changes.txt, service_status.txt).
- Do NOT list Windows system paths.
- Use forward slashes (/) instead of backslashes (\\) if any path is mentioned.

Do not wrap the JSON in markdown. Do not add any text outside the JSON.
"""
    raw = ask_qwen([
        {
            "role": "system",
            "content": "You are a university IT support assistant. Output only valid JSON."
        },
        {"role": "user", "content": prompt},
    ])
    return raw


raw_response = answer_with_compressed_context(compressed_context, question)

print("Raw model response:")
print(raw_response)

diagnostic = parse_json_object(raw_response)


# WRITE: save structured state to state.json.
state = {
    "problem": question,
    "selected_files": [str(file) for file in selected_files],
    "compressed_context": compressed_context,
    "diagnostic_context": diagnostic,
    "created_at": datetime.now(timezone.utc).isoformat(),
}

with open("state.json", "w", encoding="utf-8") as file:
    json.dump(state, file, indent=2, ensure_ascii=False)

print("Wrote state.json")
print(json.dumps(state, indent=2, ensure_ascii=False))


# ISOLATE: split state into task-specific artifacts.
diagnostic_context = {
    "problem": state["problem"],
    "device": "Windows laptop",
    "wifi_status": "operational",
    "selected_files": state["selected_files"],
    "diagnosis": state["diagnostic_context"].get("diagnosis"),
    "likely_cause": state["diagnostic_context"].get("likely_cause"),
    "immediate_steps": state["diagnostic_context"].get("immediate_steps", []),
    "why_phone_works": state["diagnostic_context"].get("why_phone_works"),
    "escalation": state["diagnostic_context"].get("escalation"),
    "files_used": state["diagnostic_context"].get("files_used", []),
}

report_context = {
    "total_wifi_cases": 37,
    "resolved_cases": 29,
    "unresolved_cases": 8,
}

state["isolated"] = {
    "diagnostic_context": diagnostic_context,
    "report_context": report_context,
}

with open("state.json", "w", encoding="utf-8") as file:
    json.dump(state, file, indent=2, ensure_ascii=False)

print("Isolated state saved to state.json")
print("Next call should use only state['isolated']['diagnostic_context']")
print(
    "Diagnostic context characters:",
    len(json.dumps(diagnostic_context, ensure_ascii=False))
)