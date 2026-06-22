import os
import re
import requests
from typing import List, Dict
from pydantic import BaseModel, Field

from backend.groq_guardrails import load_groq_settings, call_with_groq_limits
from backend.nim_guardrails import load_nim_settings, call_with_nim_limits

CLINICAL_DISCLAIMER = "[Disclaimer: This assistant is for educational and auditing purposes only. It is not a substitute for professional clinical advice or judgment.]"
LAYPERSON_DISCLAIMER = "[Disclaimer: This assistant is for educational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult your doctor for medical concerns.]"

CLINICAL_SYSTEM_PROMPT = f"""You are an expert clinical reasoning assistant. The user is a healthcare professional (doctor, nurse, auditor).
Your task is to answer questions about the patient's clinical reasoning report in a highly technical, precise, and professional manner.
Use standard medical terminology, be direct, and focus on clinical coherence and diagnostic evidence.

You MUST begin your response with the following disclaimer text (on its own line, followed by a double line break):
{CLINICAL_DISCLAIMER}

Use the provided PATIENT REPORT CONTEXT to answer the questions. If the question cannot be answered from the context, clarify that and answer based on general medical guidelines, noting it is general knowledge.
"""

LAYPERSON_SYSTEM_PROMPT = f"""You are a warm, supportive, and empathetic patient advocate. The user is a patient or their family member.
Your task is to explain the patient's clinical reasoning report in plain, everyday language.
- Avoid medical jargon. If you must use a medical term, define it immediately in simple terms.
- Use clear everyday analogies (for example, comparing the heart's electrical system to home wiring, or a kidney filter to a coffee filter).
- Focus on reassurance, clarity, and safety.

You MUST begin your response with the following disclaimer text (on its own line, followed by a double line break):
{LAYPERSON_DISCLAIMER}

Use the provided PATIENT REPORT CONTEXT to answer the questions. Keep explanations simple, reassuring, and easy to understand.
"""


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Content of the message")


class ChatRequest(BaseModel):
    note_id: str = Field(..., description="ID of the clinical note to retrieve context from")
    messages: List[ChatMessage] = Field(..., description="List of messages in the session")
    mode: str = Field("clinical", description="Mode: clinical or layperson")


def call_llm(messages: List[Dict[str, str]]) -> str:
    # 1. Try NVIDIA NIM first
    nim_settings = load_nim_settings()
    if nim_settings.api_key:
        def _call_nim():
            headers = {
                "Authorization": f"Bearer {nim_settings.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": nim_settings.model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 1024
            }
            url = f"{nim_settings.base_url.rstrip('/')}/chat/completions"
            response = requests.post(url, json=payload, headers=headers, timeout=nim_settings.timeout_seconds)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            raise RuntimeError(f"NVIDIA NIM completions request failed (status {response.status_code}): {response.text}")
        
        return call_with_nim_limits(_call_nim, nim_settings)

    # 2. Try Groq fallback
    groq_settings = load_groq_settings()
    if groq_settings.api_key:
        def _call_groq():
            headers = {
                "Authorization": f"Bearer {groq_settings.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": groq_settings.model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 1024
            }
            url = "https://api.groq.com/openai/v1/chat/completions"
            response = requests.post(url, json=payload, headers=headers, timeout=groq_settings.timeout_seconds)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            raise RuntimeError(f"Groq completions request failed (status {response.status_code}): {response.text}")
            
        return call_with_groq_limits(_call_groq, groq_settings)

    raise RuntimeError("No LLM API Key is configured. Please configure GROQ_API_KEY or NVIDIA_NIM_API_KEY in .env.")


def formulate_report_context(report: dict) -> str:
    timeline = report.get("timeline", {})
    events_summary = []
    for section in timeline.get("sections", []):
        for event in section.get("events", []):
            events_summary.append(
                f"- [{section['name'].upper()}] {event['text']} ({event['label']}, Status: {event['status']})"
            )
            
    contradictions = []
    for flag in report.get("contradiction_flags", []):
        contradictions.append(
            f"- [{flag['type']}] {flag['entity']}: {flag['description']}"
        )
        
    differentials = []
    for diff in report.get("differentials", []):
        differentials.append(
            f"- {diff['name']} (Rank {diff['rank']}, Score: {diff.get('score', 0)}) - Rationale: {diff.get('rationale', '')}"
        )
        
    context_str = "PATIENT REPORT CONTEXT:\n"
    context_str += "Clinical Timeline Events:\n" + ("\n".join(events_summary) if events_summary else "No events.") + "\n\n"
    context_str += "Detected Contradictions:\n" + ("\n".join(contradictions) if contradictions else "None.") + "\n\n"
    context_str += "Differential Diagnoses & Hypotheses:\n" + ("\n".join(differentials) if differentials else "None.")
    return context_str


PROMPT_INJECTION_PATTERNS = [
    r"(?i)\bignore\b.*\binstruction",
    r"(?i)\bforget\b.*\binstruction",
    r"(?i)\bsystem\b.*\bprompt",
    r"(?i)\bnew\b.*\bprompt",
    r"(?i)\bdisregard\b.*\binstruction",
    r"(?i)\byou\b.*\bmust\b.*\bnow",
    r"(?i)\bact\b.*\bas\b.*\ba\b",
    r"(?i)\boverride\b.*\binstruction",
]


def check_prompt_injection(text: str) -> bool:
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def generate_chat_response(request: ChatRequest, report_json: dict) -> str:
    context_str = formulate_report_context(report_json)
    system_instruction = CLINICAL_SYSTEM_PROMPT if request.mode == "clinical" else LAYPERSON_SYSTEM_PROMPT
    disclaimer = CLINICAL_DISCLAIMER if request.mode == "clinical" else LAYPERSON_DISCLAIMER
    
    # Prep LLM messages payload
    llm_messages = [
        {"role": "system", "content": f"{system_instruction}\n\n{context_str}"}
    ]
    
    # Filter and add conversational history
    for msg in request.messages:
        # Ignore initial system prompts from frontend if any to prevent tampering
        if msg.role in {"user", "assistant"}:
            # Check for prompt injection in user queries
            if msg.role == "user" and check_prompt_injection(msg.content):
                return (
                    f"{disclaimer}\n\n[Security Alert: Your message contains patterns that violate "
                    f"our safety policy. Please focus your queries specifically on the patient report context.]"
                )
            llm_messages.append({"role": msg.role, "content": msg.content})
            
    # Call the active LLM
    raw_response = call_llm(llm_messages)
    
    # Enforce disclaimer presence in the response (fallback check)
    if disclaimer not in raw_response:
        raw_response = f"{disclaimer}\n\n{raw_response}"
        
    return raw_response
