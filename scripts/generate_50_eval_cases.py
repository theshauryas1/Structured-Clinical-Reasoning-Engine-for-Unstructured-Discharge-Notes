import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTES_DIR = ROOT / "tests" / "synthetic_notes"
EVAL_FILE = ROOT / "tests" / "eval" / "eval_cases_50.json"

CASES_DATA = [
    # --- ACUTE ISCHEMIC STROKE (10 cases) ---
    {
        "filename": "eval50_stroke_01_resolved.txt",
        "expected_top": "Acute ischemic stroke",
        "expected_contradictions": [],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
74yo male presenting with sudden onset left-sided weakness and facial droop. CT head negative for acute hemorrhage. BP 178/92, HR 78.
HOSPITAL COURSE:
Patient received IV tPA in ED. Transferred to Neuro ICU. Left-sided weakness and facial droop progressively resolved over 48 hours. MRI brain confirmed subacute right MCA infarct.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute ischemic stroke (right MCA) - resolved left-sided weakness and resolved facial droop. Discharged home in stable condition."""
    },
    {
        "filename": "eval50_stroke_02_missing_symptom.txt",
        "expected_top": "Acute ischemic stroke",
        "expected_contradictions": ["missing_symptom"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
68yo female admitted with acute expressive aphasia, right-sided weakness, and blurry vision. Vitals stable.
HOSPITAL COURSE:
Admitted to stroke unit. Right-sided weakness improved with physical therapy. Aphasia improved to baseline speech fluency. MRI confirmed left MCA ischemic stroke.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute ischemic stroke - right-sided weakness resolved, aphasia resolved. Patient cleared for discharge to outpatient rehab."""
    },
    {
        "filename": "eval50_stroke_03_new_finding.txt",
        "expected_top": "Acute ischemic stroke",
        "expected_contradictions": ["new_finding"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
79yo male with acute left-sided weakness and dysarthria. CT brain negative for bleed.
HOSPITAL COURSE:
Patient treated conservatively with antiplatelet therapy. Weakness improved steadily over hospital stay.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute ischemic stroke - left-sided weakness improving.
2. New onset atrial fibrillation - developed rapid heart rate on day of discharge requiring metoprolol."""
    },
    {
        "filename": "eval50_stroke_04_status_reversal.txt",
        "expected_top": "Acute ischemic stroke",
        "expected_contradictions": ["status_reversal"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
66yo female admitted with right-sided weakness. BP 160/90.
HOSPITAL COURSE:
Motor strength improved to 5/5 by hospital day 3 with rehabilitation therapy.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute ischemic stroke.
Discharge exam noted sudden worsening right-sided weakness and deterioration at rest requiring emergent repeat neurology consult."""
    },
    {
        "filename": "eval50_stroke_05_resolved.txt",
        "expected_top": "Acute ischemic stroke",
        "expected_contradictions": [],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
70yo male presenting with sudden right facial droop and right arm weakness.
HOSPITAL COURSE:
Symptoms resolved within 36 hours post-thrombolytic therapy. MRI brain demonstrated lacunar infarct.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute ischemic stroke - resolved weakness and resolved facial droop. Patient stable for discharge home."""
    },
    {
        "filename": "eval50_stroke_06_missing_symptom.txt",
        "expected_top": "Acute ischemic stroke",
        "expected_contradictions": ["missing_symptom"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
82yo female presenting with aphasia and left-sided weakness. Also noted severe vision changes on initial neuro exam.
HOSPITAL COURSE:
Speech therapy initiated for aphasia. Weakness showed significant recovery.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute ischemic stroke - left-sided weakness stable, aphasia resolved. Discharged to rehabilitation facility."""
    },
    {
        "filename": "eval50_stroke_07_new_finding.txt",
        "expected_top": "Acute ischemic stroke",
        "expected_contradictions": ["new_finding"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
65yo male admitted with sudden left facial droop and weakness.
HOSPITAL COURSE:
Treated with aspirin and statin. Neurologic deficits stabilized.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute ischemic stroke - stable neurological status.
2. New onset acute kidney injury - acute creatinine elevation noted prior to discharge requiring follow-up."""
    },
    {
        "filename": "eval50_stroke_08_status_reversal.txt",
        "expected_top": "Acute ischemic stroke",
        "expected_contradictions": ["status_reversal"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
71yo male with left-sided weakness and aphasia.
HOSPITAL COURSE:
Aphasia resolved completely during the hospital course.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute ischemic stroke - discharge note documents worsening expressive aphasia and clinical deterioration."""
    },
    {
        "filename": "eval50_stroke_09_resolved.txt",
        "expected_top": "Acute ischemic stroke",
        "expected_contradictions": [],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
63yo female admitted with acute right hemiparesis and facial droop.
HOSPITAL COURSE:
Received acute stroke protocol care. Hemiparesis and facial droop resolved before discharge.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute ischemic stroke - full motor recovery, facial droop resolved. Safe for discharge home with outpatient therapy."""
    },
    {
        "filename": "eval50_stroke_10_missing_symptom.txt",
        "expected_top": "Acute ischemic stroke",
        "expected_contradictions": ["missing_symptom"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
77yo male presenting with sudden onset left-sided weakness, blurry vision, and mild dysarthria.
HOSPITAL COURSE:
Weakness improved with physical therapy. Brain MRI showed right hemisphere infarction.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute ischemic stroke - left-sided weakness improved, dysarthria resolved. Patient discharged to skilled nursing facility."""
    },

    # --- COMMUNITY-ACQUIRED PNEUMONIA (10 cases) ---
    {
        "filename": "eval50_pna_01_resolved.txt",
        "expected_top": "Community-acquired pneumonia",
        "expected_contradictions": [],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
58yo male admitted with fever, productive cough, and shortness of breath. Chest x-ray confirmed right lower lobe pneumonia infiltrate.
HOSPITAL COURSE:
Treated with 5 days of IV ceftriaxone and azithromycin. Defervesced by day 2. Cough and shortness of breath resolved.
DISCHARGE DIAGNOSES AND STATUS:
1. Community-acquired pneumonia - resolved fever, resolved cough, resolved shortness of breath. Discharged on oral antibiotics."""
    },
    {
        "filename": "eval50_pna_02_missing_symptom.txt",
        "expected_top": "Community-acquired pneumonia",
        "expected_contradictions": ["missing_symptom"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
64yo female with productive cough, fever of 39C, and chest pain on inspiration. CXR showed left lower lobe pneumonia.
HOSPITAL COURSE:
Patient received intravenous antibiotics. Fever resolved and clinical status improved.
DISCHARGE DIAGNOSES AND STATUS:
1. Community-acquired pneumonia - cough and fever resolved. Patient discharged home on oral cefdinir."""
    },
    {
        "filename": "eval50_pna_03_new_finding.txt",
        "expected_top": "Community-acquired pneumonia",
        "expected_contradictions": ["new_finding"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
72yo male admitted with fever and productive cough due to community-acquired pneumonia.
HOSPITAL COURSE:
Infection responded well to antibiotic therapy with resolution of fever and improvement in sputum production.
DISCHARGE DIAGNOSES AND STATUS:
1. Community-acquired pneumonia - improved.
2. New onset atrial fibrillation - developed acute palpitations with rapid ventricular rate at discharge."""
    },
    {
        "filename": "eval50_pna_04_status_reversal.txt",
        "expected_top": "Community-acquired pneumonia",
        "expected_contradictions": ["status_reversal"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
61yo female admitted with community-acquired pneumonia, fever, and productive cough.
HOSPITAL COURSE:
Patient defervesced and productive cough improved on hospital day 3.
DISCHARGE DIAGNOSES AND STATUS:
1. Community-acquired pneumonia.
Discharge summary notes worsening productive cough, recurrent febrile spikes, and respiratory deterioration at rest."""
    },
    {
        "filename": "eval50_pna_05_resolved.txt",
        "expected_top": "Community-acquired pneumonia",
        "expected_contradictions": [],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
55yo male admitted with high fever, chills, and productive cough. Chest imaging confirmed right middle lobe pneumonia.
HOSPITAL COURSE:
Started on ceftriaxone. Fever resolved, sputum cleared, and patient remained afebrile for 48 hours.
DISCHARGE DIAGNOSES AND STATUS:
1. Community-acquired pneumonia - resolved fever and resolved cough. Discharged in stable condition."""
    },
    {
        "filename": "eval50_pna_06_missing_symptom.txt",
        "expected_top": "Community-acquired pneumonia",
        "expected_contradictions": ["missing_symptom"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
69yo male with pneumonia, fever, cough, and significant shortness of breath on exertion.
HOSPITAL COURSE:
Antibiotics administered. Fever resolved and cough improved significantly.
DISCHARGE DIAGNOSES AND STATUS:
1. Community-acquired pneumonia - fever resolved, productive cough improved. Stable for discharge home."""
    },
    {
        "filename": "eval50_pna_07_new_finding.txt",
        "expected_top": "Community-acquired pneumonia",
        "expected_contradictions": ["new_finding"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
80yo female with community-acquired pneumonia, productive cough, and fever.
HOSPITAL COURSE:
Infection cleared with antibiotic regimen.
DISCHARGE DIAGNOSES AND STATUS:
1. Community-acquired pneumonia - resolved.
2. New onset acute respiratory failure - acute hypoxia requiring 3L oxygen at discharge."""
    },
    {
        "filename": "eval50_pna_08_status_reversal.txt",
        "expected_top": "Community-acquired pneumonia",
        "expected_contradictions": ["status_reversal"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
52yo male with pneumonia and shortness of breath.
HOSPITAL COURSE:
Shortness of breath improved steadily during hospital course.
DISCHARGE DIAGNOSES AND STATUS:
1. Community-acquired pneumonia - discharge exam shows worsening shortness of breath and respiratory deterioration."""
    },
    {
        "filename": "eval50_pna_09_resolved.txt",
        "expected_top": "Community-acquired pneumonia",
        "expected_contradictions": [],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
47yo male presenting with fever, pleuritic chest discomfort, productive cough, and infiltrate on chest x-ray.
HOSPITAL COURSE:
Clinical improvement with oral/IV antimicrobial therapy. No fever for 72 hours.
DISCHARGE DIAGNOSES AND STATUS:
1. Community-acquired pneumonia - resolved fever, resolved cough. Discharged with completed treatment plan."""
    },
    {
        "filename": "eval50_pna_10_missing_symptom.txt",
        "expected_top": "Community-acquired pneumonia",
        "expected_contradictions": ["missing_symptom"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
75yo female admitted with severe productive cough, fever, and palpitations. CXR confirmed lobar pneumonia.
HOSPITAL COURSE:
Antibiotic therapy completed with clear clinical and radiographic improvement. Fever subsided.
DISCHARGE DIAGNOSES AND STATUS:
1. Community-acquired pneumonia - fever resolved, cough resolved. Discharged home in good condition."""
    },

    # --- ACUTE KIDNEY INJURY (8 cases) ---
    {
        "filename": "eval50_aki_01_resolved.txt",
        "expected_top": "Acute kidney injury",
        "expected_contradictions": [],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
67yo male admitted with acute kidney injury. Admission creatinine was 3.1 mg/dL, baseline 1.0.
HOSPITAL COURSE:
Aggressive IV fluid hydration given. Creatinine steadily dropped to 1.1 mg/dL. Urine output normalized.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute kidney injury - resolved, creatinine normalized at 1.1 mg/dL. Discharged home."""
    },
    {
        "filename": "eval50_aki_02_status_reversal.txt",
        "expected_top": "Acute kidney injury",
        "expected_contradictions": ["status_reversal"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
73yo female admitted with acute kidney injury. Baseline creatinine 0.9, admission 2.6.
HOSPITAL COURSE:
Creatinine improved to 1.2 by day 3 following volume repletion.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute kidney injury.
Discharge labs demonstrate worsening renal function with creatinine bumped to 3.4 mg/dL and acute deterioration."""
    },
    {
        "filename": "eval50_aki_03_new_finding.txt",
        "expected_top": "Acute kidney injury",
        "expected_contradictions": ["new_finding"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
62yo male admitted with acute kidney injury and volume depletion.
HOSPITAL COURSE:
Renal function normalized with intravenous fluids.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute kidney injury - resolved creatinine.
2. New onset shortness of breath - acute hypoxia developed on discharge day requiring oxygen."""
    },
    {
        "filename": "eval50_aki_04_missing_symptom.txt",
        "expected_top": "Acute kidney injury",
        "expected_contradictions": ["missing_symptom"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
70yo female admitted with acute kidney injury, creatinine 2.8, and severe nausea and fever.
HOSPITAL COURSE:
Hydration given with prompt drop in creatinine to baseline.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute kidney injury - creatinine resolved to 1.0. Discharged in stable condition."""
    },
    {
        "filename": "eval50_aki_05_resolved.txt",
        "expected_top": "Acute kidney injury",
        "expected_contradictions": [],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
59yo male with acute kidney injury secondary to dehydration. Creatinine elevated at 2.9 mg/dL.
HOSPITAL COURSE:
Fluid resuscitation resulted in normalization of renal function and resolution of azotemia.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute kidney injury - resolved creatinine (1.0 mg/dL). Patient medically cleared for discharge."""
    },
    {
        "filename": "eval50_aki_06_status_reversal.txt",
        "expected_top": "Acute kidney injury",
        "expected_contradictions": ["status_reversal"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
81yo male with acute kidney injury. Creatinine 2.5 on admission.
HOSPITAL COURSE:
Renal parameters improved to normal range on hospital day 2.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute kidney injury - discharge summary shows worsening creatinine up to 3.8 and clinical deterioration."""
    },
    {
        "filename": "eval50_aki_07_new_finding.txt",
        "expected_top": "Acute kidney injury",
        "expected_contradictions": ["new_finding"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
66yo female admitted with acute kidney injury and elevated blood urea nitrogen.
HOSPITAL COURSE:
Creatinine returned to baseline with isotonic hydration.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute kidney injury - resolved.
2. New onset atrial fibrillation - developed acute palpitations and rapid heart rate at discharge."""
    },
    {
        "filename": "eval50_aki_08_resolved.txt",
        "expected_top": "Acute kidney injury",
        "expected_contradictions": [],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
74yo male presenting with prerenal acute kidney injury, creatinine 2.7.
HOSPITAL COURSE:
Responded rapidly to IV crystalloid therapy. Creatinine normalized to 1.1.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute kidney injury - resolved, creatinine normal. Patient discharged home."""
    },

    # --- ATRIAL FIBRILLATION (8 cases) ---
    {
        "filename": "eval50_afib_01_resolved.txt",
        "expected_top": "Atrial fibrillation",
        "expected_contradictions": [],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
68yo male admitted with atrial fibrillation with rapid ventricular response and palpitations. HR 142.
HOSPITAL COURSE:
Rate control achieved with IV diltiazem then transitioned to oral metoprolol. Normal sinus rhythm restored. Palpitations resolved.
DISCHARGE DIAGNOSES AND STATUS:
1. Atrial fibrillation - rate controlled on metoprolol, palpitations resolved. Discharged on apixaban."""
    },
    {
        "filename": "eval50_afib_02_new_finding.txt",
        "expected_top": "Atrial fibrillation",
        "expected_contradictions": ["new_finding"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
71yo female admitted with atrial fibrillation and palpitations.
HOSPITAL COURSE:
Rate controlled with beta-blockers.
DISCHARGE DIAGNOSES AND STATUS:
1. Atrial fibrillation - rate controlled.
2. New onset acute kidney injury - developed acute creatinine elevation requiring medication review."""
    },
    {
        "filename": "eval50_afib_03_missing_symptom.txt",
        "expected_top": "Atrial fibrillation",
        "expected_contradictions": ["missing_symptom"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
65yo male admitted with atrial fibrillation, palpitations, and shortness of breath.
HOSPITAL COURSE:
Ventricular rate controlled with metoprolol. Rhythm stabilized.
DISCHARGE DIAGNOSES AND STATUS:
1. Atrial fibrillation - rate controlled on oral antiarrhythmic therapy, palpitations resolved."""
    },
    {
        "filename": "eval50_afib_04_status_reversal.txt",
        "expected_top": "Atrial fibrillation",
        "expected_contradictions": ["status_reversal"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
77yo female with atrial fibrillation and palpitations.
HOSPITAL COURSE:
Heart rate normalized and palpitations resolved on day 2.
DISCHARGE DIAGNOSES AND STATUS:
1. Atrial fibrillation - discharge telemetry shows worsening palpitations and rapid ventricular response at rest."""
    },
    {
        "filename": "eval50_afib_05_resolved.txt",
        "expected_top": "Atrial fibrillation",
        "expected_contradictions": [],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
62yo male admitted with paroxysmal atrial fibrillation and palpitations.
HOSPITAL COURSE:
Spontaneous cardioversion to sinus rhythm. Started on anticoagulation.
DISCHARGE DIAGNOSES AND STATUS:
1. Atrial fibrillation - stable sinus rhythm, palpitations resolved. Discharged home."""
    },
    {
        "filename": "eval50_afib_06_new_finding.txt",
        "expected_top": "Atrial fibrillation",
        "expected_contradictions": ["new_finding"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
80yo male with atrial fibrillation.
HOSPITAL COURSE:
Adequately rate controlled on beta-blockers.
DISCHARGE DIAGNOSES AND STATUS:
1. Atrial fibrillation - rate controlled.
2. New onset acute respiratory failure - acute hypoxia requiring oxygen at discharge."""
    },
    {
        "filename": "eval50_afib_07_missing_symptom.txt",
        "expected_top": "Atrial fibrillation",
        "expected_contradictions": ["missing_symptom"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
73yo female admitted with atrial fibrillation, palpitations, and fever.
HOSPITAL COURSE:
Rate control established with diltiazem infusion.
DISCHARGE DIAGNOSES AND STATUS:
1. Atrial fibrillation - heart rate controlled on oral diltiazem, palpitations resolved. Discharged home."""
    },
    {
        "filename": "eval50_afib_08_resolved.txt",
        "expected_top": "Atrial fibrillation",
        "expected_contradictions": [],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
69yo female with new atrial fibrillation and rapid palpitations.
HOSPITAL COURSE:
Pharmacologic rate control successful. Anticoagulation initiated.
DISCHARGE DIAGNOSES AND STATUS:
1. Atrial fibrillation - heart rate controlled, palpitations resolved. Safe for discharge with cardiology follow-up."""
    },

    # --- ACUTE HYPOXEMIC RESPIRATORY FAILURE (7 cases) ---
    {
        "filename": "eval50_resp_01_resolved.txt",
        "expected_top": "Acute hypoxemic respiratory failure",
        "expected_contradictions": [],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
75yo male admitted with acute respiratory failure, hypoxia, and shortness of breath requiring 4L nasal cannula.
HOSPITAL COURSE:
Treated with diuresis and oxygen support. Successfully weaned to room air. Dyspnea resolved.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute respiratory failure - resolved hypoxia, resolved shortness of breath. Discharged on room air in stable condition."""
    },
    {
        "filename": "eval50_resp_02_new_finding.txt",
        "expected_top": "Acute hypoxemic respiratory failure",
        "expected_contradictions": ["new_finding"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
68yo female admitted with acute respiratory failure and shortness of breath.
HOSPITAL COURSE:
Respiratory status improved with supplemental oxygen weaning.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute respiratory failure - improving.
2. New onset acute kidney injury - acute creatinine rise documented before discharge."""
    },
    {
        "filename": "eval50_resp_03_missing_symptom.txt",
        "expected_top": "Acute hypoxemic respiratory failure",
        "expected_contradictions": ["missing_symptom"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
70yo male admitted with acute respiratory failure, severe shortness of breath, hypoxia, and fever.
HOSPITAL COURSE:
Diuresis and respiratory therapy provided. Oxygen requirements decreased to baseline.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute respiratory failure - hypoxia resolved, shortness of breath resolved. Stable for discharge."""
    },
    {
        "filename": "eval50_resp_04_status_reversal.txt",
        "expected_top": "Acute hypoxemic respiratory failure",
        "expected_contradictions": ["status_reversal"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
83yo female with acute respiratory failure and hypoxia.
HOSPITAL COURSE:
Oxygen requirements improved and patient was placed on room air on day 3.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute respiratory failure.
Discharge physical exam reveals worsening hypoxia and acute respiratory deterioration requiring high-flow oxygen."""
    },
    {
        "filename": "eval50_resp_05_resolved.txt",
        "expected_top": "Acute hypoxemic respiratory failure",
        "expected_contradictions": [],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
63yo male with acute respiratory failure and shortness of breath.
HOSPITAL COURSE:
Responded well to bronchodilators and diuresis. Weaned to room air.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute respiratory failure - resolved hypoxia, resolved shortness of breath. Patient discharged home."""
    },
    {
        "filename": "eval50_resp_06_new_finding.txt",
        "expected_top": "Acute hypoxemic respiratory failure",
        "expected_contradictions": ["new_finding"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
72yo male admitted with acute respiratory failure.
HOSPITAL COURSE:
Oxygenation improved on non-invasive ventilation then room air.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute respiratory failure - resolved.
2. New onset atrial fibrillation - developed palpitations and irregular tachycardia at discharge."""
    },
    {
        "filename": "eval50_resp_07_status_reversal.txt",
        "expected_top": "Acute hypoxemic respiratory failure",
        "expected_contradictions": ["status_reversal"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
78yo female with acute respiratory failure and shortness of breath.
HOSPITAL COURSE:
Dyspnea improved significantly during hospital stay.
DISCHARGE DIAGNOSES AND STATUS:
1. Acute respiratory failure - discharge note documents worsening shortness of breath and respiratory deterioration."""
    },

    # --- POST-OPERATIVE TOTAL KNEE ARTHROPLASTY RECOVERY (7 cases) ---
    {
        "filename": "eval50_tka_01_resolved.txt",
        "expected_top": "Post-operative recovery after total knee arthroplasty",
        "expected_contradictions": [],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
64yo female admitted following total knee arthroplasty for severe knee osteoarthritis.
HOSPITAL COURSE:
Post-op recovery uneventful. Incision clean and dry. Ambulating 150ft with PT. Pain well controlled.
DISCHARGE DIAGNOSES AND STATUS:
1. Post-operative recovery after total knee arthroplasty - healing cleanly, pain controlled, mobility progressing well. Discharged home."""
    },
    {
        "filename": "eval50_tka_02_new_finding.txt",
        "expected_top": "Post-operative recovery after total knee arthroplasty",
        "expected_contradictions": ["new_finding"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
71yo male admitted following elective total knee arthroplasty.
HOSPITAL COURSE:
Knee incision healing well. Physical therapy goals met.
DISCHARGE DIAGNOSES AND STATUS:
1. Post-operative recovery after total knee arthroplasty - stable.
2. New onset acute respiratory failure - developed acute hypoxia requiring supplemental oxygen."""
    },
    {
        "filename": "eval50_tka_03_status_reversal.txt",
        "expected_top": "Post-operative recovery after total knee arthroplasty",
        "expected_contradictions": ["status_reversal"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
67yo female post total knee arthroplasty with surgical pain.
HOSPITAL COURSE:
Pain improved significantly and patient was ambulating on postoperative day 2.
DISCHARGE DIAGNOSES AND STATUS:
1. Post-operative recovery after total knee arthroplasty.
Discharge evaluation documents worsening pain and surgical site deterioration at rest."""
    },
    {
        "filename": "eval50_tka_04_missing_symptom.txt",
        "expected_top": "Post-operative recovery after total knee arthroplasty",
        "expected_contradictions": ["missing_symptom"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
69yo male admitted after total knee arthroplasty with post-op knee pain, swelling, and mild fever.
HOSPITAL COURSE:
Knee pain controlled on oral analgesics. Incision clean and intact.
DISCHARGE DIAGNOSES AND STATUS:
1. Post-operative recovery after total knee arthroplasty - pain controlled, mobility improved. Discharged home."""
    },
    {
        "filename": "eval50_tka_05_resolved.txt",
        "expected_top": "Post-operative recovery after total knee arthroplasty",
        "expected_contradictions": [],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
59yo male admitted after left total knee arthroplasty.
HOSPITAL COURSE:
Physical therapy completed. Surgical dressing dry and clean.
DISCHARGE DIAGNOSES AND STATUS:
1. Post-operative recovery after total knee arthroplasty - uncomplicated recovery, pain controlled. Discharged home."""
    },
    {
        "filename": "eval50_tka_06_new_finding.txt",
        "expected_top": "Post-operative recovery after total knee arthroplasty",
        "expected_contradictions": ["new_finding"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
76yo female admitted following right total knee arthroplasty.
HOSPITAL COURSE:
Mobility achieved with physical therapy assistance.
DISCHARGE DIAGNOSES AND STATUS:
1. Post-operative recovery after total knee arthroplasty - stable.
2. New onset atrial fibrillation - developed rapid irregular palpitations at discharge."""
    },
    {
        "filename": "eval50_tka_07_status_reversal.txt",
        "expected_top": "Post-operative recovery after total knee arthroplasty",
        "expected_contradictions": ["status_reversal"],
        "content": """ADMISSION DIAGNOSIS AND FINDINGS:
70yo male admitted following total knee arthroplasty.
HOSPITAL COURSE:
Post-operative pain and mobility improved on day 2.
DISCHARGE DIAGNOSES AND STATUS:
1. Post-operative recovery after total knee arthroplasty - discharge note documents worsening pain and clinical deterioration."""
    },
]


def generate():
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_FILE.parent.mkdir(parents=True, exist_ok=True)

    eval_cases = []

    for item in CASES_DATA:
        filepath = NOTES_DIR / item["filename"]
        filepath.write_text(item["content"].strip() + "\n", encoding="utf-8")

        eval_cases.append(
            {
                "note_file": item["filename"],
                "expected_top_differential": item["expected_top"],
                "expected_contradiction_types": item["expected_contradictions"],
            }
        )

    EVAL_FILE.write_text(json.dumps(eval_cases, indent=2), encoding="utf-8")
    print(f"Successfully generated {len(eval_cases)} evaluation cases in {EVAL_FILE}")


if __name__ == "__main__":
    generate()
