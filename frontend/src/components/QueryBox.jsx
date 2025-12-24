import { useState } from 'react';

/**
 * Query input component.
 * Handles user question input and submission.
 */
export default function QueryBox({ onQuery, isLoading }) {
  const [question, setQuestion] = useState('');
  const [useHybrid, setUseHybrid] = useState(true);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (question.trim() && !isLoading) {
      onQuery(question.trim(), useHybrid);
    }
  };

  return (
    <div className="query-box">
      <form onSubmit={handleSubmit}>
        <div className="query-input-group">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about your documents..."
            rows="4"
            disabled={isLoading}
            className="query-textarea"
          />
        </div>
        
        <div className="query-controls">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={useHybrid}
              onChange={(e) => setUseHybrid(e.target.checked)}
              disabled={isLoading}
            />
            <span>Use Hybrid Retrieval (Vector + Knowledge Graph)</span>
          </label>
          
          <button
            type="submit"
            disabled={!question.trim() || isLoading}
            className="submit-button"
          >
            {isLoading ? 'Processing...' : 'Submit Query'}
          </button>
        </div>
      </form>
    </div>
  );
}

