# UI/UX Design Document
## Clinical Reasoning Engine

---

## 1. Design Philosophy & Guidelines
The Clinical Reasoning Engine UI/UX is built to deliver a **clean, high-density, clinician-centric dashboard**. Medical records are verbose and cognitively demanding; therefore, the interface prioritizes clear separation of concerns, high contrast alerts, and interactive, structured visual elements rather than large walls of text.

### Key Visual Language Elements
- **Layout & Structure**: Single-column structured container with a max width of `860px`, focusing the user's attention down a linear audit path.
- **Color Systems**:
  - *Primary Actions*: Deep Blue (`#007bff`) for focus indicators and primary buttons.
  - *Alerts & Contradictions*: Red tint (`#ffe6e6` background, `#b42318` text, `red` borders) to immediately highlight safety-critical data contradictions.
  - *Calibrated Fills*: Green (`#28a745`) to represent high-confidence findings.
  - *Neutrals*: Clean whites (`#ffffff`), soft greys (`#f8f9fa` background), and dark slate text (`#111827`) to maintain high reading contrast.
- **Typography**: Highly readable sans-serif typography, utilizing system defaults (Inter, Helvetica, Arial) with clean weights for headers and metadata details.

---

## 2. Page Layout & Component Structure

The interface, implemented in [App.jsx](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/frontend/src/App.jsx), dynamically adapts its grid layout. When a note is processed, the interface splits into a **60/40 responsive column grid**:

### 2.1. Note Input Area (Top)
- **File Uploader (Drag & Drop Zone)**: Dotted blue container supporting drag-and-drop or click-to-browse file inputs. Displays selected filename, file requirements, and OCR limitation warnings.
- **Clinical Note Textarea**: A large input box with a minimum height of `180px` for pasting raw clinical text.
- **Language Config Dropdowns**:
  - *Input Language Selector*: Dropdown supporting `Auto-Detect` and the 5 supported languages.
  - *Display Language Selector*: Dropdown specifying the output language for the audit report.
- **Action Buttons**: Primary blue button for analysis and secondary grey button to load a sample.

### 2.2. Language Flow Info Banner (Middle)
Appears only when a report has been successfully ingested. Displays detected language flow information and translation previews.

### 2.3. View Toggle Bar (Middle-Bottom)
A pill-shaped selector with tabs for:
- **Clinical Audit Report**: Displays the detailed medical timeline, identified contradictions, and calibrated differentials.
- **Plain-Language Summary**: Replaces the medical dashboards with a simplified patient-friendly narrative breakdown, timeline explanation, and diagnostic analogies.

### 2.4. Split Grid Panels (Bottom)
- **Main Analysis Panel (60% width)**:
  - *Timeline View*: Visualizes clinical events chronological segmented.
  - *Contradiction Cards*: Highlights contradictions requiring clinician review.
  - *Differential Diagnosis List*: Shows hypothesis ranking with calibrated confidence bars.
- **Chat Q&A Panel (40% width)**:
  - A persistent sidebar containing the interactive chatbot, styled message bubbles, a persona dropdown (Clinical vs. Layperson), and clear medical liability disclaimers.

```
+-------------------------------------------------------------------------------------------------+
|                                    CLINICAL REASONING ENGINE                                    |
|  [!] Disclaimer: Research/demo system                                                           |
+-------------------------------------------------------------------------------------------------+
|  +-------------------------------------------------------------------------------------------+  |
|  | [ Drag & Drop PDF, Image, or Audio File Here ]                                            |  |
|  +-------------------------------------------------------------------------------------------+  |
|  [ Textarea: Paste discharge summary notes here...                                           ]  |
|                                                                                                 |
|  Input Language: [Auto-Detect]                  Display Language: [English]                    |
|  [ Analyze Note ]   [ Try Sample ]                                                              |
+-------------------------------------------------------------------------------------------------+
|  Language Flow: Input: ES | Pipeline: EN | Display: ES                                          |
|  "Entrada traducida: ADMISSION SUMMARY..."                                                      |
+-------------------------------------------------------------------------------------------------+
|  [ CLINICAL AUDIT REPORT ] [ PLAIN-LANGUAGE SUMMARY ] (View Toggle)                             |
+-------------------------------------------------------------------------------------------------+
| (60% Main Col - Clinical View)                 | (40% Chat Col - Sidebar Chat)                  |
|                                                |                                                |
| TIMELINE VIEW                                  | REPORT CHAT Q&A                                |
| * ADMISSION                                    | Mode: [Clinical Mode v]                        |
|   - Fever (Symptom | Active)                   | +--------------------------------------------+ |
| * HOSPITAL COURSE                              | | [Disclaimer: For educational/audit purposes| |
|   - Ceftriaxone (Medication | Active)          | +--------------------------------------------+ |
| * DISCHARGE                                    | | assistant: [Disclaimer: ...] How can I ... | |
|   - Pneumonia (Diagnosis | Resolved)           | | user: What antibiotic did they receive?    | |
|                                                | | assistant: [Disclaimer: ...] The patient...| |
| CONTRADICTIONS                                 | +--------------------------------------------+ |
| +--------------------------------------------+ | [ Ask a question...            ] [ Send ]     |
| | [!] Status Reversal: Pneumonia             | |                                              |
| | Pneumonia resolved but discharge active... | |                                              |
| +--------------------------------------------+ |                                              |
|                                                |                                              |
| DIFFERENTIAL DIAGNOSIS                         |                                              |
| 1. Community-Acquired Pneumonia                |                                              |
|    [=========================> (89.2% Calib)]  |                                              |
+-------------------------------------------------------------------------------------------------+
```

---

## 3. Detailed Component Interaction

### 3.1. Timeline View
- **Code**: [TimelineView.jsx](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/frontend/src/components/TimelineView.jsx)
- **UX Goal**: Give structure to narrative.
- **UI Element**: Sections are displayed in chronological order (Admission -> Hospital Course -> Discharge) with a vertical timeline guide border. Individual events appear as clean sub-cards containing the exact extracted clinical entity text, its classification label (e.g., SYMPTOM, MEDICATION), its status (e.g., active, resolved), and the context sentence highlight.

### 3.2. Contradiction Cards
- **Code**: [ContradictionCards.jsx](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/frontend/src/components/ContradictionCards.jsx)
- **UX Goal**: Surface high-severity findings that require clinical validation.
- **UI Element**: Warning cards colored in light-red with bold red left borders. Each alert lists the contradiction type (e.g., `status_reversal`) and a detailed explanation of why the admission-to-discharge clinical story does not match.

### 3.3. Confidence Bars
- **Code**: [ConfidenceBars.jsx](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/frontend/src/components/ConfidenceBars.jsx)
- **UX Goal**: Visually convey confidence calibration.
- **UI Element**: Differential diagnoses are listed in ranked order. Under each item, a progress track is displayed. A green fill indicator grows to match the calibrated confidence score (e.g., 78.4%). The raw percentage value is displayed within the fill block.

### 3.4. Drag & Drop File Uploader
- **Code**: [App.jsx](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/frontend/src/App.jsx#L720-L768)
- **UX Goal**: Allow rapid note ingestion from raw clinical artifacts.
- **UI Element**: Dashed drag-and-drop container. Detects active dragging to highlight the drop-zone. Prompts the user with file requirements and supports immediate PDF, image, and audio upload. Triggers a full analysis flow on submission.

### 3.5. View Switcher Toggle
- **Code**: [App.jsx](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/frontend/src/App.jsx#L905-L935)
- **UX Goal**: Support distinct auditor vs. patient user flows.
- **UI Element**: Horizontal toggle bar at the top of the report section. Clicking "Plain-Language Summary" issues an asynchronous call to `/explain/{note_id}` and renders the markdown response.

### 3.6. Sidebar Chat Widget
- **Code**: [App.jsx](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/frontend/src/App.jsx#L936-L1010)
- **UX Goal**: Enable interactive, contextual Q&A over the clinical report.
- **UI Element**: Sidebar column containing a message scroll window, message input bar, and a mode selector (Clinical vs. Layperson). Messages are color-coded (user: blue bubble, right-aligned; chatbot: light-blue bubble, left-aligned). Enforces a mandatory, warning-red clinical disclaimer at the start of every session and at the beginning of each chatbot response.

---

## 4. Accessibility (a11y) & SEO Requirements
- **Semantic HTML**: Utilize appropriate semantic structure (`<h1>`, `<h2>`, `<label>`, `<main>`, `<section>`).
- **Unique Identifiers**: Explicit `id` selectors for form controls (e.g., `id="language-select"` and `id="display-language-select"`) to facilitate automation testing and assistive technologies.
- **Descriptive Labels**: Every input is paired with a matching `<label htmlFor="...">` tag.
- **SEO Elements**: Includes custom `<title>` and metadata definitions inside `index.html` referencing the Structured Clinical Reasoning Engine.

---

## 5. Document Links
- Product Context: [prd.md](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/docs/prd.md)
- Technical Details: [trd.md](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/docs/trd.md)
- Database Layout: [backend_schema.md](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/docs/backend_schema.md)
- Implementation and Training Guide: [implementation_guide.md](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/docs/implementation_guide.md)
