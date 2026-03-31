export default function ConfidenceBars({ confidenceScores = [], differentials = [] }) {
  if (!confidenceScores.length) {
    return <p className="empty-state">Confidence bars will appear after hypotheses are scored.</p>;
  }

  return (
    <div className="confidence-stack">
      {confidenceScores.map((score) => {
        const differential = differentials.find((item) => item.name === score.hypothesis);
        const width = `${Math.round(score.confidence * 100)}%`;
        return (
          <article className="confidence-card" key={score.hypothesis}>
            <div className="confidence-header">
              <div>
                <strong>{score.hypothesis}</strong>
                <p>{differential?.rationale || "Heuristic confidence estimate"}</p>
              </div>
              <span>{Math.round(score.confidence * 100)}%</span>
            </div>
            <div className="confidence-track">
              <div className="confidence-fill" style={{ width }} />
            </div>
            <small>
              Mean {score.mean_score} • Variance {score.variance} • Uncertainty {score.uncertainty}
            </small>
          </article>
        );
      })}
    </div>
  );
}
