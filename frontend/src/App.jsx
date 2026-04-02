import { useState } from "react";

const SAMPLE_NOTE = `ADMISSION SUMMARY:
Patient admitted with fever, cough, and shortness of breath.

HOSPITAL COURSE:
Fever resolved after 3 days on ceftriaxone and azithromycin. Oxygen requirement improved.

DISCHARGE DIAGNOSES AND PLAN:
Community-acquired pneumonia improved clinically. New onset atrial fibrillation noted during admission.`;

const API_URL = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");
const SUPPORTED_LANGUAGES = ["en", "de", "fr", "nl", "es"];

const TRANSLATIONS = {
  en: {
    appTitle: "Clinical Reasoning Engine",
    disclaimer: "This is a research/demo system and not for clinical use.",
    notePlaceholder: "Paste clinical discharge note...",
    inputLanguage: "Input language",
    displayLanguage: "Display language",
    autoDetect: "Auto-detect",
    analyze: "Analyze",
    analyzing: "Analyzing...",
    trySample: "Try Sample",
    processing: "Processing clinical note...",
    emptyInputError: "Please paste a clinical note before analyzing.",
    requestError: "Error processing request",
    languageFlow: "Language flow",
    input: "Input",
    pipeline: "Pipeline",
    display: "Display",
    translatedInput: "Translated input used for reasoning",
    timeline: "Timeline",
    contradictions: "Contradictions",
    differentialDiagnosis: "Differential Diagnosis",
    noTimeline: "No timeline returned.",
    noContradictions: "No contradictions found.",
    noDifferential: "No differential diagnosis returned.",
    unknown: "Unknown",
    languageLabels: {
      en: "English",
      de: "German",
      fr: "French",
      nl: "Dutch",
      es: "Spanish",
    },
  },
  de: {
    appTitle: "Klinische Reasoning-Engine",
    disclaimer: "Dies ist ein Forschungs-/Demo-System und nicht fuer den klinischen Einsatz bestimmt.",
    notePlaceholder: "Klinischen Entlassungsbericht einfuegen...",
    inputLanguage: "Eingabesprache",
    displayLanguage: "Anzeigesprache",
    autoDetect: "Automatisch erkennen",
    analyze: "Analysieren",
    analyzing: "Analysiere...",
    trySample: "Beispiel laden",
    processing: "Klinische Notiz wird verarbeitet...",
    emptyInputError: "Bitte fuegen Sie vor der Analyse eine klinische Notiz ein.",
    requestError: "Fehler bei der Verarbeitung der Anfrage",
    languageFlow: "Sprachfluss",
    input: "Eingabe",
    pipeline: "Pipeline",
    display: "Anzeige",
    translatedInput: "Fuer die Analyse verwendete Uebersetzung",
    timeline: "Zeitverlauf",
    contradictions: "Widersprueche",
    differentialDiagnosis: "Differenzialdiagnosen",
    noTimeline: "Keine Zeitleiste zurueckgegeben.",
    noContradictions: "Keine Widersprueche gefunden.",
    noDifferential: "Keine Differenzialdiagnose zurueckgegeben.",
    unknown: "Unbekannt",
    languageLabels: {
      en: "Englisch",
      de: "Deutsch",
      fr: "Franzoesisch",
      nl: "Niederlaendisch",
      es: "Spanisch",
    },
  },
  fr: {
    appTitle: "Moteur de raisonnement clinique",
    disclaimer: "Il s'agit d'un systeme de recherche/demo et non destine a un usage clinique.",
    notePlaceholder: "Collez la note de sortie clinique...",
    inputLanguage: "Langue d'entree",
    displayLanguage: "Langue d'affichage",
    autoDetect: "Detection automatique",
    analyze: "Analyser",
    analyzing: "Analyse en cours...",
    trySample: "Charger un exemple",
    processing: "Traitement de la note clinique...",
    emptyInputError: "Veuillez coller une note clinique avant l'analyse.",
    requestError: "Erreur lors du traitement de la requete",
    languageFlow: "Flux de langue",
    input: "Entree",
    pipeline: "Pipeline",
    display: "Affichage",
    translatedInput: "Traduction utilisee pour le raisonnement",
    timeline: "Chronologie",
    contradictions: "Contradictions",
    differentialDiagnosis: "Diagnostic differentiel",
    noTimeline: "Aucune chronologie retournee.",
    noContradictions: "Aucune contradiction detectee.",
    noDifferential: "Aucun diagnostic differentiel retourne.",
    unknown: "Inconnu",
    languageLabels: {
      en: "Anglais",
      de: "Allemand",
      fr: "Francais",
      nl: "Neerlandais",
      es: "Espagnol",
    },
  },
  nl: {
    appTitle: "Klinische redeneerengine",
    disclaimer: "Dit is een onderzoeks-/demosysteem en niet bedoeld voor klinisch gebruik.",
    notePlaceholder: "Plak klinische ontslagnotitie...",
    inputLanguage: "Invoertaal",
    displayLanguage: "Weergavetaal",
    autoDetect: "Automatisch detecteren",
    analyze: "Analyseren",
    analyzing: "Bezig met analyseren...",
    trySample: "Voorbeeld laden",
    processing: "Klinische notitie wordt verwerkt...",
    emptyInputError: "Plak eerst een klinische notitie voordat je analyseert.",
    requestError: "Fout bij het verwerken van de aanvraag",
    languageFlow: "Taalstroom",
    input: "Invoer",
    pipeline: "Pipeline",
    display: "Weergave",
    translatedInput: "Vertaalde invoer gebruikt voor de redenering",
    timeline: "Tijdlijn",
    contradictions: "Tegenstrijdigheden",
    differentialDiagnosis: "Differentialdiagnose",
    noTimeline: "Geen tijdlijn ontvangen.",
    noContradictions: "Geen tegenstrijdigheden gevonden.",
    noDifferential: "Geen differentiaaldiagnose ontvangen.",
    unknown: "Onbekend",
    languageLabels: {
      en: "Engels",
      de: "Duits",
      fr: "Frans",
      nl: "Nederlands",
      es: "Spaans",
    },
  },
  es: {
    appTitle: "Motor de razonamiento clinico",
    disclaimer: "Este es un sistema de investigacion/demostracion y no para uso clinico.",
    notePlaceholder: "Pegue la nota clinica de alta...",
    inputLanguage: "Idioma de entrada",
    displayLanguage: "Idioma de visualizacion",
    autoDetect: "Deteccion automatica",
    analyze: "Analizar",
    analyzing: "Analizando...",
    trySample: "Cargar ejemplo",
    processing: "Procesando la nota clinica...",
    emptyInputError: "Pegue una nota clinica antes de analizar.",
    requestError: "Error al procesar la solicitud",
    languageFlow: "Flujo de idioma",
    input: "Entrada",
    pipeline: "Pipeline",
    display: "Visualizacion",
    translatedInput: "Entrada traducida usada para el razonamiento",
    timeline: "Cronologia",
    contradictions: "Contradicciones",
    differentialDiagnosis: "Diagnostico diferencial",
    noTimeline: "No se devolvio ninguna cronologia.",
    noContradictions: "No se encontraron contradicciones.",
    noDifferential: "No se devolvio ningun diagnostico diferencial.",
    unknown: "Desconocido",
    languageLabels: {
      en: "Ingles",
      de: "Aleman",
      fr: "Frances",
      nl: "Neerlandes",
      es: "Espanol",
    },
  },
};

const styles = {
  page: {
    fontFamily: "Arial, sans-serif",
    background: "#f8f9fa",
    minHeight: "100vh",
    padding: "24px 16px 48px",
  },
  shell: {
    maxWidth: "860px",
    margin: "0 auto",
  },
  title: {
    marginBottom: "8px",
  },
  disclaimer: {
    color: "#b42318",
    fontWeight: 700,
    marginBottom: "20px",
  },
  textarea: {
    width: "100%",
    minHeight: "220px",
    padding: "14px",
    border: "1px solid #d0d5dd",
    borderRadius: "8px",
    resize: "vertical",
    background: "#ffffff",
    marginBottom: "14px",
  },
  fieldLabel: {
    display: "block",
    fontWeight: 700,
    marginBottom: "8px",
  },
  select: {
    width: "100%",
    padding: "12px",
    border: "1px solid #d0d5dd",
    borderRadius: "8px",
    background: "#ffffff",
    marginBottom: "14px",
  },
  buttonRow: {
    display: "flex",
    gap: "10px",
    flexWrap: "wrap",
    marginBottom: "18px",
  },
  primaryButton: {
    padding: "10px 15px",
    background: "#007bff",
    color: "white",
    border: "none",
    borderRadius: "5px",
    cursor: "pointer",
  },
  secondaryButton: {
    padding: "10px 15px",
    background: "#e9ecef",
    color: "#111827",
    border: "none",
    borderRadius: "5px",
    cursor: "pointer",
  },
  section: {
    background: "#ffffff",
    border: "1px solid #e5e7eb",
    borderRadius: "10px",
    padding: "18px",
    marginTop: "18px",
  },
  timelineWrap: {
    borderLeft: "3px solid #007bff",
    paddingLeft: "12px",
  },
  timelineItem: {
    padding: "12px 0",
    borderBottom: "1px solid #e5e7eb",
  },
  timelineEvent: {
    marginTop: "8px",
    padding: "10px",
    background: "#f8fafc",
    borderRadius: "8px",
  },
  contradictionCard: {
    background: "#ffe6e6",
    padding: "12px",
    marginBottom: "10px",
    borderLeft: "5px solid red",
    borderRadius: "6px",
  },
  diagnosisCard: {
    padding: "12px",
    border: "1px solid #e5e7eb",
    borderRadius: "8px",
    marginBottom: "10px",
    background: "#ffffff",
  },
  confidenceTrack: {
    background: "#ddd",
    borderRadius: "5px",
    overflow: "hidden",
    marginTop: "6px",
  },
  confidenceFill: {
    background: "#28a745",
    color: "white",
    padding: "5px",
    minWidth: "52px",
    whiteSpace: "nowrap",
  },
  meta: {
    color: "#475467",
    marginTop: "6px",
  },
  infoPanel: {
    background: "#eef4ff",
    border: "1px solid #c7d7fe",
    borderRadius: "8px",
    padding: "12px",
    marginTop: "12px",
  },
  error: {
    color: "#b42318",
    marginTop: "8px",
  },
};

function formatSectionName(value, translations) {
  if (!value) {
    return translations.unknown;
  }
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function getTranslations(language) {
  return TRANSLATIONS[language] || TRANSLATIONS.en;
}

function buildLanguageOptions(translations) {
  return [
    { value: "auto", label: translations.autoDetect },
    ...SUPPORTED_LANGUAGES.map((value) => ({
      value,
      label: translations.languageLabels[value],
    })),
  ];
}

function App() {
  const [input, setInput] = useState("");
  const [language, setLanguage] = useState("auto");
  const [displayLanguage, setDisplayLanguage] = useState("en");
  const [output, setOutput] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const uiLanguage = output?.display_language || displayLanguage;
  const t = getTranslations(uiLanguage);
  const inputLanguageOptions = buildLanguageOptions(t);
  const displayLanguageOptions = SUPPORTED_LANGUAGES.map((value) => ({
    value,
    label: t.languageLabels[value],
  }));

  const report = output?.display_report || output;
  const timeline = report?.timeline?.sections || [];
  const contradictions = report?.contradiction_flags || [];
  const differentials = report?.differentials || [];
  const confidenceScores = report?.confidence_scores || [];

  const confidenceByName = new Map();
  for (const item of confidenceScores) {
    confidenceByName.set(item.hypothesis, item.confidence);
  }

  const analyze = async () => {
    if (!input.trim()) {
      setError(t.emptyInputError);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/ingest`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ note_text: input, lang: language, display_lang: displayLanguage }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || t.requestError);
      }

      setOutput(data);
    } catch (err) {
      console.error(err);
      setError(err.message || t.requestError);
    } finally {
      setLoading(false);
    }
  };

  const loadSample = () => {
    setInput(SAMPLE_NOTE);
    setError("");
  };

  return (
    <div style={styles.page}>
      <div style={styles.shell}>
        <h1 style={styles.title}>{t.appTitle}</h1>
        <p style={styles.disclaimer}>{t.disclaimer}</p>

        <textarea
          rows={10}
          style={styles.textarea}
          placeholder={t.notePlaceholder}
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />

        <label htmlFor="language-select" style={styles.fieldLabel}>
          {t.inputLanguage}
        </label>
        <select
          id="language-select"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          style={styles.select}
        >
          {inputLanguageOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <label htmlFor="display-language-select" style={styles.fieldLabel}>
          {t.displayLanguage}
        </label>
        <select
          id="display-language-select"
          value={displayLanguage}
          onChange={(e) => setDisplayLanguage(e.target.value)}
          style={styles.select}
        >
          {displayLanguageOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <div style={styles.buttonRow}>
          <button onClick={analyze} disabled={!input.trim() || loading} style={styles.primaryButton}>
            {loading ? t.analyzing : t.analyze}
          </button>
          <button onClick={loadSample} type="button" style={styles.secondaryButton}>
            {t.trySample}
          </button>
        </div>

        {loading && <p>{t.processing}</p>}
        {error ? <p style={styles.error}>{error}</p> : null}

        {report ? (
          <div style={{ marginTop: "30px" }}>
            <div style={styles.infoPanel}>
              <strong>{t.languageFlow}</strong>
              <div style={styles.meta}>
                {t.input}: {output?.source_language || language}
              </div>
              <div style={styles.meta}>
                {t.pipeline}: {output?.pipeline_language || "en"}
              </div>
              <div style={styles.meta}>
                {t.display}: {output?.display_language || displayLanguage}
              </div>
              {output?.translated_input_text && output?.translated_input_text !== input ? (
                <div style={styles.meta}>
                  {t.translatedInput}: {output.translated_input_text}
                </div>
              ) : null}
            </div>

            <div style={styles.section}>
              <h2>{t.timeline}</h2>
              {timeline.length ? (
                <div style={styles.timelineWrap}>
                  {timeline.map((section) => (
                    <div key={section.name} style={styles.timelineItem}>
                      <strong>{formatSectionName(section.name, t)}</strong>
                      <div style={styles.meta}>{section.text}</div>
                      {section.events?.map((event, index) => (
                        <div key={`${event.start}-${event.end}-${index}`} style={styles.timelineEvent}>
                          <strong>{event.text}</strong>
                          <div>
                            {event.label} | {event.status}
                          </div>
                          <div style={styles.meta}>{event.sentence_text}</div>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              ) : (
                <p>{t.noTimeline}</p>
              )}
            </div>

            <div style={styles.section}>
              <h2>{t.contradictions}</h2>
              {contradictions.length === 0 && <p>{t.noContradictions}</p>}
              {contradictions.map((item, index) => (
                <div key={`${item.type}-${item.entity}-${index}`} style={styles.contradictionCard}>
                  <strong>{item.type}</strong>
                  <p style={{ marginBottom: 0 }}>{item.description}</p>
                </div>
              ))}
            </div>

            <div style={styles.section}>
              <h2>{t.differentialDiagnosis}</h2>
              {differentials.length ? (
                differentials.map((item, index) => {
                  const confidence = confidenceByName.get(item.name) ?? item.score ?? 0;
                  const percentage = `${Math.max(0, Math.min(100, confidence * 100))}%`;
                  return (
                    <div key={`${item.name}-${index}`} style={styles.diagnosisCard}>
                      <strong>{item.name}</strong>
                      {item.rationale ? <div style={styles.meta}>{item.rationale}</div> : null}
                      <div style={styles.confidenceTrack}>
                        <div style={{ ...styles.confidenceFill, width: percentage }}>
                          {(confidence * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <p>{t.noDifferential}</p>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default App;
