import React from "react";

const SECTION_LABELS = {
  admission: "Admission Summary",
  hospital_course: "Hospital Course",
  discharge: "Discharge & Plan",
};

export default function TimelineView({ timeline }) {
  if (!timeline?.sections?.length) {
    return <p style={{ color: "var(--color-lichen)", fontFamily: "var(--font-roboto-mono)", fontSize: "14px" }}>No timeline returned.</p>;
  }

  const styles = {
    timelineRow: {
      display: "flex",
      flexDirection: "column",
      gap: "24px",
      marginTop: "16px",
    },
    column: {
      background: "var(--color-abyssal-ink)",
      border: "1px solid var(--color-graphite)",
      borderRadius: "var(--radius-cards)",
      padding: "24px",
      position: "relative",
    },
    heading: {
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "14px",
      textTransform: "uppercase",
      color: "var(--color-bioluminescent-lime)",
      marginBottom: "8px",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      borderBottom: "1px solid var(--color-graphite)",
      paddingBottom: "8px",
    },
    text: {
      fontFamily: "var(--font-aspekta)",
      fontSize: "16px",
      lineHeight: "1.4",
      color: "var(--color-lichen)",
      marginBottom: "16px",
    },
    eventStack: {
      display: "flex",
      flexDirection: "column",
      gap: "10px",
    },
    eventChip: {
      background: "rgba(255, 255, 255, 0.02)",
      border: "1px solid var(--color-graphite)",
      borderRadius: "8px",
      padding: "12px 16px",
      display: "flex",
      flexDirection: "column",
      gap: "6px",
    },
    badgeRow: {
      display: "flex",
      alignItems: "center",
      gap: "8px",
      flexWrap: "wrap",
    },
    eventLabel: {
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "11px",
      padding: "2px 8px",
      borderRadius: "9999px",
      border: "1px solid var(--color-lichen)",
      color: "var(--color-paper)",
      textTransform: "uppercase",
    },
    eventStatus: {
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "11px",
      color: "var(--color-bioluminescent-lime)",
      textTransform: "uppercase",
    },
    eventText: {
      fontFamily: "var(--font-aspekta)",
      fontSize: "17px",
      color: "var(--color-paper)",
      letterSpacing: "-0.01em",
    },
    eventContext: {
      fontFamily: "var(--font-aspekta)",
      fontSize: "14px",
      color: "var(--color-graphite)",
      lineHeight: "1.3",
    },
  };

  return (
    <div style={styles.timelineRow}>
      {timeline.sections.map((section) => (
        <article style={styles.column} key={section.name}>
          <div style={styles.heading}>
            <span>{SECTION_LABELS[section.name] || section.name}</span>
            <span>{section.events.length} events</span>
          </div>
          <p style={styles.text}>"{section.text}"</p>
          <div style={styles.eventStack}>
            {section.events.map((event, idx) => (
              <div style={styles.eventChip} key={`${event.start}-${event.end}-${idx}`}>
                <div style={styles.badgeRow}>
                  <span style={styles.eventLabel}>{event.label}</span>
                  <span style={styles.eventStatus}>{event.status}</span>
                  <span style={{ fontFamily: "var(--font-roboto-mono)", fontSize: "11px", color: "var(--color-graphite)" }}>
                    {event.domain}
                  </span>
                </div>
                <div style={styles.eventText}>{event.text}</div>
                {event.sentence_text && (
                  <div style={styles.eventContext}>Context: "{event.sentence_text}"</div>
                )}
              </div>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}
