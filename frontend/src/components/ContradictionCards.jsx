import React from "react";

export default function ContradictionCards({ contradictions = [] }) {
  if (!contradictions.length) {
    return (
      <p style={{ color: "var(--color-bioluminescent-lime)", fontFamily: "var(--font-roboto-mono)", fontSize: "14px", marginTop: "16px" }}>
        No clinical contradictions flagged for this note.
      </p>
    );
  }

  const styles = {
    cardStack: {
      display: "flex",
      flexDirection: "column",
      gap: "16px",
      marginTop: "16px",
    },
    contradictionCard: {
      background: "rgba(180, 35, 24, 0.05)",
      border: "1px solid #b42318",
      borderRadius: "var(--radius-cards)",
      padding: "24px",
    },
    meta: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      borderBottom: "1px solid rgba(180, 35, 24, 0.2)",
      paddingBottom: "8px",
      marginBottom: "12px",
    },
    typeBadge: {
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "11px",
      padding: "2px 8px",
      borderRadius: "9999px",
      background: "#b42318",
      color: "var(--color-paper)",
      textTransform: "uppercase",
    },
    entity: {
      fontFamily: "var(--font-aspekta)",
      fontSize: "18px",
      color: "#ff8080",
    },
    description: {
      fontFamily: "var(--font-aspekta)",
      fontSize: "16px",
      lineHeight: "1.4",
      color: "var(--color-paper)",
      marginBottom: "18px",
    },
    evidenceGrid: {
      display: "flex",
      gap: "16px",
      flexWrap: "wrap",
    },
    evidenceBox: {
      flex: "1 1 240px",
      background: "rgba(0, 0, 0, 0.2)",
      border: "1px solid var(--color-graphite)",
      borderRadius: "8px",
      padding: "14px",
    },
    evidenceLabel: {
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "11px",
      color: "var(--color-lichen)",
      textTransform: "uppercase",
      marginBottom: "6px",
      display: "block",
    },
    evidenceText: {
      fontFamily: "var(--font-aspekta)",
      fontSize: "15px",
      color: "var(--color-paper)",
      marginBottom: "4px",
    },
    evidenceContext: {
      fontFamily: "var(--font-aspekta)",
      fontSize: "13px",
      color: "var(--color-graphite)",
      lineHeight: "1.3",
    },
  };

  return (
    <div style={styles.cardStack}>
      {contradictions.map((item, index) => (
        <article className="animate-warning-alert" style={styles.contradictionCard} key={`${item.type}-${item.entity}-${index}`}>
          <div style={styles.meta}>
            <span style={styles.typeBadge}>{item.type.replace("_", " ")}</span>
            <span style={styles.entity}>{item.entity}</span>
          </div>
          <p style={styles.description}>{item.description}</p>
          
          <div style={styles.evidenceGrid}>
            {item.admission_evidence && (
              <div style={styles.evidenceBox}>
                <span style={styles.evidenceLabel}>Admission Evidence ({item.admission_evidence.section})</span>
                <div style={styles.evidenceText}>{item.admission_evidence.text_span}</div>
                {item.admission_evidence.sentence_text && (
                  <div style={styles.evidenceContext}>Context: "{item.admission_evidence.sentence_text}"</div>
                )}
              </div>
            )}
            
            {item.discharge_evidence && (
              <div style={styles.evidenceBox}>
                <span style={styles.evidenceLabel}>Discharge Evidence ({item.discharge_evidence.section})</span>
                <div style={styles.evidenceText}>{item.discharge_evidence.text_span}</div>
                {item.discharge_evidence.sentence_text && (
                  <div style={styles.evidenceContext}>Context: "{item.discharge_evidence.sentence_text}"</div>
                )}
              </div>
            )}
          </div>
        </article>
      ))}
    </div>
  );
}
