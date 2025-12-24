import { useState } from 'react';
import QueryBox from './components/QueryBox';
import AnswerBox from './components/AnswerBox';
import SourceList from './components/SourceList';
import { query as queryAPI } from './api';

/**
 * Main application component.
 * Orchestrates query flow and displays results.
 */
function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [queryResult, setQueryResult] = useState(null);

  const handleQuery = async (question, useHybrid) => {
    setLoading(true);
    setError(null);
    setQueryResult(null);

    try {
      const result = await queryAPI(question, useHybrid);
      setQueryResult(result);
    } catch (err) {
      setError(err.message || 'An error occurred while processing your query');
      console.error('Query error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Hybrid RAG + Knowledge Graph QA System</h1>
        <p>Ask questions about your documents using vector search and knowledge graph reasoning</p>
      </header>

      <main className="app-main">
        <DocumentUpload />
        <QueryBox onQuery={handleQuery} isLoading={loading} />

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {loading && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <p>Processing your query...</p>
          </div>
        )}

        {queryResult && !loading && (
          <>
            <AnswerBox
              answer={queryResult.answer}
              confidence={queryResult.confidence}
              queryType={queryResult.query_type}
              reasoningSteps={queryResult.reasoning_steps}
            />
            <SourceList
              sources={queryResult.sources}
              kgContext={queryResult.kg_context}
            />
          </>
        )}
      </main>

      <footer className="app-footer">
        <p>Hybrid RAG + KG System v1.0</p>
      </footer>
    </div>
  );
}

export default App;

