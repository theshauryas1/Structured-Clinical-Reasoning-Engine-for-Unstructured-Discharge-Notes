from backend.agents.chat_agent import call_llm, formulate_report_context, LAYPERSON_DISCLAIMER

EXPLAIN_SYSTEM_PROMPT = f"""You are a patient advocate. Your job is to translate a highly technical clinical reasoning report into a simple, patient-friendly summary.
Explain the findings, timeline, and flagged contradictions in clear layperson terms.
- Use simple analogies to explain medical terms or diagnoses.
- Format the output in structured markdown sections:
  1. Patient-Friendly Summary
  2. Simplified Timeline of Events (explain what happened at Admission, Course, and Discharge)
  3. Explanations of any warnings or inconsistencies (contradictions) flagged by our auditors
  4. Diagnosis Breakdowns with clear analogies

You MUST begin your response with the following disclaimer text (on its own line, followed by a double line break):
{LAYPERSON_DISCLAIMER}
"""


def generate_plain_language_explanation(report_json: dict) -> str:
    context_str = formulate_report_context(report_json)
    messages = [
        {"role": "system", "content": EXPLAIN_SYSTEM_PROMPT},
        {"role": "user", "content": f"Please translate and summarize the following patient report context:\n\n{context_str}"}
    ]
    raw_response = call_llm(messages)

    # Enforce disclaimer presence
    if LAYPERSON_DISCLAIMER not in raw_response:
        raw_response = f"{LAYPERSON_DISCLAIMER}\n\n{raw_response}"

    return raw_response
