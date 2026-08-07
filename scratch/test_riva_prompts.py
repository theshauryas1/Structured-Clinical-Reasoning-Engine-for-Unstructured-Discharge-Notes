import sys, os, requests
sys.path.insert(0, os.path.abspath("."))
from dotenv import load_dotenv
load_dotenv(override=True)
from backend.nim_guardrails import load_nim_settings

nim_settings = load_nim_settings()

def execute_prompt(sys_p, user_p):
    url = f"{nim_settings.base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": "nvidia/riva-translate-4b-instruct-v2",
        "messages": [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": user_p}
        ],
        "temperature": 0.0,
        "max_tokens": 512
    }
    headers = {"Authorization": f"Bearer {nim_settings.api_key}", "Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=15)
    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"].strip()
    return f"ERROR: {r.status_code} {r.text}"

print("=== TESTING EXACT LANGUAGE PAIR TAGS ===")
prompts = [
    ("en-de", "The patient was admitted with acute chest pain."),
    ("de-en", "Der Patient wurde wegen akuter Brustschmerzen eingewiesen."),
    ("en-es-es", "The laboratory results are within normal limits."),
    ("fr-en", "Le patient presente une amelioration clinique significative."),
    ("en-fr", "The patient shows significant clinical improvement."),
    ("en-es", "The patient shows significant clinical improvement."),
]

for sys_p, text in prompts:
    res = execute_prompt(sys_p, text)
    print(f"\n[TAG]: '{sys_p}'\n[INPUT]: {text}\n[RESULT]: {res}")
