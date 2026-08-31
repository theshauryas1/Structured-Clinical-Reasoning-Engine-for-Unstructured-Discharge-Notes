import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTES_DIR = ROOT / "tests" / "synthetic_notes"
EVAL_FILE = ROOT / "tests" / "eval" / "eval_cases_1000.json"

random.seed(42)

FIRST_NAMES_M = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles"]
FIRST_NAMES_F = ["Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"]

DIAGNOSIS_CONFIGS = [
    {
        "domain": "stroke",
        "expected_top": "Acute ischemic stroke",
        "admission_symptoms": ["left-sided weakness", "right-sided weakness", "facial droop", "aphasia"],
        "extra_symptoms": ["blurry vision", "dysarthria", "numbness", "headache"],
        "admission_vitals": ["BP 172/95, HR 78", "BP 164/88, HR 82", "BP 180/100, HR 76", "BP 158/90, HR 84"],
        "hospital_course": [
            "Patient was admitted to Neuro ICU and received standard stroke care protocol with antiplatelet therapy. Neurological status stabilized.",
            "Patient was admitted for acute stroke evaluation. Brain imaging confirmed acute ischemic infarction. Physical therapy initiated.",
            "Treated with permissive hypertension and secondary stroke prevention regimen. Deficits showed progressive daily improvement."
        ],
        "resolved_desc": "Acute ischemic stroke - motor strength improved, neurological deficits resolved. Discharged home in stable condition.",
        "status_rev_desc": "Acute ischemic stroke - discharge note documents sudden worsening weakness and neurological deterioration at rest.",
    },
    {
        "domain": "pneumonia",
        "expected_top": "Community-acquired pneumonia",
        "admission_symptoms": ["fever", "productive cough", "shortness of breath", "chest pain"],
        "extra_symptoms": ["chills", "pleuritic chest pain", "fatigue", "myalgias"],
        "admission_vitals": ["Temp 38.8, HR 98, BP 120/75", "Temp 39.1, HR 104, BP 128/80", "Temp 38.5, HR 92, BP 115/70"],
        "hospital_course": [
            "Patient was admitted with community-acquired pneumonia and treated with 5 days of IV ceftriaxone and azithromycin. Defervesced rapidly.",
            "Treated with empiric broad-spectrum antimicrobial therapy for lobar pneumonia. Oxygenation normalized and sputum cleared.",
            "Completed IV antibiotic regimen for community-acquired pneumonia with steady resolution of cough and fever."
        ],
        "resolved_desc": "Community-acquired pneumonia - resolved fever, resolved cough, resolved shortness of breath. Discharged on oral antibiotics.",
        "status_rev_desc": "Community-acquired pneumonia - discharge examination reveals worsening productive cough, fever spikes, and respiratory deterioration.",
    },
    {
        "domain": "aki",
        "expected_top": "Acute kidney injury",
        "admission_symptoms": ["acute kidney injury", "elevated creatinine", "dehydration"],
        "extra_symptoms": ["nausea", "fatigue", "decreased urine output", "malaise"],
        "admission_vitals": ["BP 108/65, HR 90", "BP 112/70, HR 85", "BP 122/78, HR 88"],
        "hospital_course": [
            "Patient was admitted with prerenal acute kidney injury. Received aggressive IV fluid resuscitation. Creatinine normalized to baseline.",
            "Treated with fluid hydration and withholding of nephrotoxic medications. Renal panel showed steady daily improvement.",
            "Renal function recovered following volume repletion, with normalization of blood urea nitrogen and serum creatinine."
        ],
        "resolved_desc": "Acute kidney injury - resolved, creatinine normalized to 1.0 mg/dL. Discharged home.",
        "status_rev_desc": "Acute kidney injury - discharge lab work shows worsening creatinine up to 3.6 mg/dL and acute deterioration.",
    },
    {
        "domain": "afib",
        "expected_top": "Atrial fibrillation",
        "admission_symptoms": ["atrial fibrillation", "palpitations", "irregular heart rate"],
        "extra_symptoms": ["dizziness", "mild chest discomfort", "fatigue", "lightheadedness"],
        "admission_vitals": ["HR 138, BP 130/85", "HR 145, BP 124/80", "HR 132, BP 138/88"],
        "hospital_course": [
            "Patient was admitted for rate control of acute atrial fibrillation. Managed with IV diltiazem followed by oral beta-blocker therapy. Normal sinus rhythm restored.",
            "Rate control achieved with metoprolol infusion. Anticoagulation started according to CHA2DS2-VASc score.",
            "Successfully treated with rate-controlling agents. Telemetry demonstrated sustained rate control and cessation of palpitations."
        ],
        "resolved_desc": "Atrial fibrillation - rate controlled on metoprolol, palpitations resolved. Discharged on oral anticoagulation.",
        "status_rev_desc": "Atrial fibrillation - discharge monitoring indicates worsening palpitations and rapid ventricular response at rest.",
    },
    {
        "domain": "respiratory_failure",
        "expected_top": "Acute hypoxemic respiratory failure",
        "admission_symptoms": ["acute respiratory failure", "hypoxia", "shortness of breath", "desaturation"],
        "extra_symptoms": ["tachypnea", "accessory muscle use", "fatigue", "wheezing"],
        "admission_vitals": ["SpO2 86% on RA, HR 102, BP 134/82", "SpO2 88% on RA, HR 96, BP 140/85", "SpO2 85% on RA, HR 108, BP 128/78"],
        "hospital_course": [
            "Admitted with acute respiratory failure requiring high-flow oxygen. Responded to medical therapy and successfully weaned to room air.",
            "Managed with supplemental oxygen and bronchodilator therapy. Hypoxia resolved and patient maintained >95% on room air.",
            "Treated for acute hypoxemic respiratory decompensation. Oxygenation parameters steadily normalized throughout hospital stay."
        ],
        "resolved_desc": "Acute respiratory failure - resolved hypoxia, resolved shortness of breath. Discharged on room air in stable condition.",
        "status_rev_desc": "Acute respiratory failure - discharge physical exam reveals worsening hypoxia and acute respiratory deterioration requiring high-flow oxygen.",
    },
    {
        "domain": "tka",
        "expected_top": "Post-operative recovery after total knee arthroplasty",
        "admission_symptoms": ["total knee arthroplasty", "post-op surgical pain", "knee swelling"],
        "extra_symptoms": ["limited range of motion", "mild localized erythema", "post-op stiffness"],
        "admission_vitals": ["BP 126/78, HR 74, Temp 36.8", "BP 132/80, HR 80, Temp 37.0", "BP 120/75, HR 76, Temp 36.9"],
        "hospital_course": [
            "Patient underwent elective total knee arthroplasty. Post-operative course uneventful. Met all physical therapy milestones.",
            "Post-surgical recovery following total knee arthroplasty. Pain well managed with multimodal analgesia. Surgical incision clean and intact.",
            "Completed post-operative rehabilitation protocol after total knee arthroplasty. Ambulated independently with assistive device."
        ],
        "resolved_desc": "Post-operative recovery after total knee arthroplasty - uncomplicated recovery, pain controlled, mobility improved. Discharged home.",
        "status_rev_desc": "Post-operative recovery after total knee arthroplasty - discharge note documents worsening pain and surgical site deterioration.",
    },
]

NEW_FINDING_OPTIONS = [
    ("New onset acute kidney injury - acute creatinine rise documented before discharge requiring follow-up.", "new_finding"),
    ("New onset atrial fibrillation - developed rapid irregular palpitations and tachycardia at discharge.", "new_finding"),
    ("New onset acute respiratory failure - acute hypoxia requiring 3L nasal cannula oxygen at discharge.", "new_finding"),
]


def generate_1000_cases():
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_FILE.parent.mkdir(parents=True, exist_ok=True)

    eval_cases = []
    total_target = 1000

    # Contradiction profile distributions:
    # 0: resolved (no contradictions) ~30%
    # 1: missing symptom ~25%
    # 2: new finding ~25%
    # 3: status reversal ~20%
    profiles = ["resolved"] * 300 + ["missing_symptom"] * 250 + ["new_finding"] * 250 + ["status_reversal"] * 200
    random.shuffle(profiles)

    for i in range(total_target):
        config = DIAGNOSIS_CONFIGS[i % len(DIAGNOSIS_CONFIGS)]
        profile = profiles[i]

        age = random.randint(35, 89)
        is_male = random.random() > 0.5
        name = random.choice(FIRST_NAMES_M) if is_male else random.choice(FIRST_NAMES_F)
        gender_str = "yo male" if is_male else "yo female"

        vitals = random.choice(config["admission_vitals"])
        course = random.choice(config["hospital_course"])

        adm_sym = random.choice(config["admission_symptoms"])
        extra_sym = random.choice(config["extra_symptoms"])

        filename = f"eval1000_case_{i+1:04d}_{config['domain']}_{profile}.txt"
        expected_contradictions = []

        if profile == "resolved":
            # Clean concordant case
            content = f"""ADMISSION DIAGNOSIS AND FINDINGS:
{age}{gender_str} ({name}) admitted with {adm_sym} and {extra_sym}. Initial vitals: {vitals}.
HOSPITAL COURSE:
{course} Symptoms showed marked clinical improvement.
DISCHARGE DIAGNOSES AND STATUS:
1. {config['resolved_desc']}"""

        elif profile == "missing_symptom":
            # Admission has an explicit secondary active finding never addressed at discharge
            missing_item = random.choice(["blurry vision", "fever", "nausea", "palpitations", "cough"])
            expected_contradictions = ["missing_symptom"]
            content = f"""ADMISSION DIAGNOSIS AND FINDINGS:
{age}{gender_str} ({name}) admitted with {adm_sym} and active {missing_item}. Initial vitals: {vitals}.
HOSPITAL COURSE:
{course} Primary presentation was treated.
DISCHARGE DIAGNOSES AND STATUS:
1. {config['expected_top']} - {adm_sym} stabilized and improved. Patient cleared for discharge home."""

        elif profile == "new_finding":
            # Unexpected new condition at discharge
            new_finding_text, c_type = random.choice(NEW_FINDING_OPTIONS)
            expected_contradictions = [c_type]
            content = f"""ADMISSION DIAGNOSIS AND FINDINGS:
{age}{gender_str} ({name}) admitted with {adm_sym}. Vitals: {vitals}.
HOSPITAL COURSE:
{course}
DISCHARGE DIAGNOSES AND STATUS:
1. {config['expected_top']} - primary condition improved.
2. {new_finding_text}"""

        elif profile == "status_reversal":
            # Improved during stay, then sudden deterioration at discharge
            expected_contradictions = ["status_reversal"]
            content = f"""ADMISSION DIAGNOSIS AND FINDINGS:
{age}{gender_str} ({name}) admitted with {adm_sym}. Vitals: {vitals}.
HOSPITAL COURSE:
{adm_sym} improved significantly on hospital day 2 with medical management.
DISCHARGE DIAGNOSES AND STATUS:
1. {config['status_rev_desc']}"""

        filepath = NOTES_DIR / filename
        filepath.write_text(content.strip() + "\n", encoding="utf-8")

        eval_cases.append(
            {
                "note_file": filename,
                "expected_top_differential": config["expected_top"],
                "expected_contradiction_types": expected_contradictions,
            }
        )

    EVAL_FILE.write_text(json.dumps(eval_cases, indent=2), encoding="utf-8")
    print(f"Successfully generated {len(eval_cases)} practical evaluation test cases in {EVAL_FILE}")


if __name__ == "__main__":
    generate_1000_cases()
