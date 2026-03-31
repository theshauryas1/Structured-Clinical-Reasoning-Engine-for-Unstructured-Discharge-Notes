export default function ContradictionCards({ contradictions = [] }) {
  if (!contradictions.length) {
    return <p className="empty-state">No contradiction flags were raised for this note.</p>;
  }

  return (
    <div className="card-stack">
      {contradictions.map((item) => (
        <article className="contradiction-card" key={`${item.type}-${item.entity}`}>
          <div className="contradiction-meta">
            <span className={`type-badge type-${item.type}`}>{item.type}</span>
            <strong>{item.entity}</strong>
          </div>
          <p>{item.description}</p>
          <div className="evidence-grid">
            {item.admission_evidence ? (
              <div className="evidence-box">
                <span>Admission evidence</span>
                <strong>{item.admission_evidence.text_span}</strong>
                <small>{item.admission_evidence.sentence_text}</small>
              </div>
            ) : null}
            {item.discharge_evidence ? (
              <div className="evidence-box">
                <span>Discharge evidence</span>
                <strong>{item.discharge_evidence.text_span}</strong>
                <small>{item.discharge_evidence.sentence_text}</small>
              </div>
            ) : null}
          </div>
        </article>
      ))}
    </div>
  );
}
