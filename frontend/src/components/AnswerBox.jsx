/**
 * Answer display component.
 * Shows the generated answer with confidence score.
 */
export default function AnswerBox({ answer, confidence, queryType, reasoningSteps }) {
  if (!answer) {
    return null;
  }

  // Determine confidence color
  const getConfidenceColor = (conf) => {
    if (conf >= 0.7) return '#10b981'; // green
    if (conf >= 0.4) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  };

  const confidenceColor = getConfidenceColor(confidence);

  return (
    <div className="answer-box">
      <div className="answer-header">
        <h2>Answer</h2>
        <div className="answer-meta">
          <span className="query-type-badge">{queryType}</span>
          <div className="confidence-score" style={{ color: confidenceColor }}>
            <span>Confidence: </span>
            <strong>{(confidence * 100).toFixed(1)}%</strong>
          </div>
        </div>
      </div>
      
      <div className="answer-content">
        {answer}
      </div>

      {reasoningSteps && reasoningSteps.length > 0 && (
        <details className="reasoning-details">
          <summary>Reasoning Steps</summary>
          <ul className="reasoning-steps">
            {reasoningSteps.map((step, index) => (
              <li key={index}>{step}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

