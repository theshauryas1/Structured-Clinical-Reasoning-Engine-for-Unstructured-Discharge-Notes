# Product Context & Domain Domain

This document describes the clinical context, product guidelines, user needs, and safety principles behind the **Clinical Reasoning Engine**.

---

## 1. The Clinical Problem

Discharge summaries are narrative, multi-author documents generated at the end of a patient's hospital stay. Because they are often compiled in a hurry under stressful environments, they suffer from three major categories of errors:
1. **Clinical Contradictions**: Resolved symptoms in one section are documented as active problems elsewhere.
2. **Missing Information / Discontinuities**: Symptoms recorded during admission are left unaddressed in the discharge summaries.
3. **Implicit Diagnoses**: Relevant findings (like elevated serum creatinine) are listed, but the corresponding diagnosis (Acute Kidney Injury) is omitted.

Manual audits of these summaries are time-consuming and error-prone. The **Clinical Reasoning Engine** acts as an audit helper to identify inconsistencies, suggest diagnostic possibilities, and score confidence using a calibrated clinical reasoning system.

---

## 2. User Personas

### 2.1. Clinical Auditor
- **Role**: Hospital quality assurance and billing compliance.
- **Goal**: Verify that the documented diagnoses match clinical guidelines and the patient's stay timeline.
- **Pain Point**: Spends hours reading notes, manually cross-referencing timeline details and billing codes.

### 2.2. Attending Physician
- **Role**: Admitting and discharging doctor.
- **Goal**: Review the patient's record quickly during handoffs.
- **Pain Point**: Needs to capture new-onset conditions without wading through long, disorganized notes.

---

## 3. Clinical Safety & Disclaimers

> [!WARNING]
> This software is a research prototype and demonstration platform. It is **NOT** a medical diagnostic tool or clinical decision support system. It must not be used for direct patient care, clinical reporting, or treatment planning.

### Safety Design Gates
To maintain safety standards, the application implements the following controls:
- **Mandatory Medical Disclaimer**: Exposed prominently in the client application header, at the start of every Q&A chat session, and prepended to all AI responses.
- **Dictation Verification Step**: When clinicians upload audio logs (dictation), the system prompts them to review, edit, and approve the text transcription before submitting the note to the reasoning engine. This prevents transcription errors from generating false contradiction alerts.
- **Source Translation Transparency**: If translation occurs, the system logs the source language and provides visual translations side-by-side with the English reasoning outputs.
- **Trace Auditing**: The engine saves both reasoning traces and orchestration policy logs to help clinicians verify the logic behind every suggestion.
