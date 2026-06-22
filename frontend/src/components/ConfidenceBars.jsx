import React from "react";

export default function ConfidenceBars({ confidenceScores = [], differentials = [] }) {
  if (!confidenceScores.length) {
    return (
      <p style={{ color: "var(--color-lichen)", fontFamily: "var(--font-roboto-mono)", fontSize: "14px", marginTop: "16px" }}>
        Confidence scores will appear here after analysis.
      </p>
    );
  }

  const styles = {
    stack: {
      display: "flex",
      flexDirection: "column",
      gap: "16px",
      marginTop: "16px",
    },
    card: {
      background: "var(--color-abyssal-ink)",
      border: "1px solid var(--color-graphite)",
      borderRadius: "var(--radius-cards)",
      padding: "24px",
    },
    header: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "flex-start",
      gap: "12px",
      marginBottom: "12px",
    },
    title: {
      fontFamily: "var(--font-aspekta)",
      fontSize: "18px",
      color: "var(--color-paper)",
      letterSpacing: "-0.01em",
    },
    rationale: {
      fontFamily: "var(--font-aspekta)",
      fontSize: "15px",
      color: "var(--color-lichen)",
      lineHeight: "1.4",
      marginTop: "6px",
    },
    percentage: {
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "20px",
      color: "var(--color-bioluminescent-lime)",
    },
    track: {
      background: "rgba(255, 255, 255, 0.05)",
      border: "1px solid var(--color-graphite)",
      height: "10px",
      borderRadius: "9999px",
      overflow: "hidden",
      marginBottom: "12px",
    },
    fill: {
      height: "100%",
      background: "var(--color-bioluminescent-lime)",
      borderRadius: "9999px",
      transition: "width 0.5s ease-out",
    },
    metadataRow: {
      display: "flex",
      gap: "16px",
      flexWrap: "wrap",
      borderTop: "1px dashed var(--color-graphite)",
      paddingTop: "10px",
    },
    metaItem: {
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "11px",
      color: "var(--color-graphite)",
      textTransform: "uppercase",
    },
    metaVal: {
      color: "var(--color-lichen)",
    },
  };

  return (
    <div style={styles.stack}>
      {confidenceScores.map((score) => {
        const differential = differentials.find((item) => item.name === score.hypothesis);
        const width = `${Math.round(score.confidence * 100)}%`;
        
        return (
          <article style={styles.card} key={score.hypothesis}>
            <div style={styles.header}>
              <div>
                <span style={styles.title}>{score.hypothesis}</span>
                <p style={styles.rationale}>{differential?.rationale || "Heuristic evidence matched."}</p>
              </div>
              <span style={styles.percentage}>{Math.round(score.confidence * 100)}%</span>
            </div>
            
            <div style={styles.track}>
              <div style={{ ...styles.fill, width }} />
            </div>
            
            <div style={styles.metadataRow}>
              <div style={styles.metaItem}>
                Mean: <span style={styles.metaVal}>{score.mean_score}</span>
              </div>
              <div style={styles.metaItem}>
                Variance: <span style={styles.metaVal}>{score.variance}</span>
              </div>
              <div style={styles.metaItem}>
                Uncertainty: <span style={styles.metaVal}>{score.uncertainty}</span>
              </div>
              {score.features && (
                <div style={styles.metaItem}>
                  Contradiction Penalty: <span style={styles.metaVal}>{score.features.contradiction_penalty}</span>
                </div>
              )}
            </div>
          </article>
        );
      })}
    </div>
  );
}
