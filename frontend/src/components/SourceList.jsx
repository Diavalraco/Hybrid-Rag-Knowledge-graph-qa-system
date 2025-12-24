/**
 * Source list component.
 * Displays retrieved source chunks and KG context.
 */
export default function SourceList({ sources, kgContext }) {
  if ((!sources || sources.length === 0) && (!kgContext || (!kgContext.entities?.length && !kgContext.relations?.length))) {
    return null;
  }

  return (
    <div className="source-list">
      <h2>Sources & Context</h2>

      {/* Vector-based sources */}
      {sources && sources.length > 0 && (
        <div className="sources-section">
          <h3>Retrieved Chunks ({sources.length})</h3>
          <div className="sources-grid">
            {sources.map((source, index) => (
              <div key={source.chunk_id || index} className="source-card">
                <div className="source-header">
                  <span className="source-index">#{index + 1}</span>
                  <span className="source-score">
                    Score: {(source.score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="source-content">
                  {source.content.substring(0, 300)}
                  {source.content.length > 300 && '...'}
                </div>
                <div className="source-meta">
                  Document: {source.document_id}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Knowledge Graph context */}
      {kgContext && (kgContext.entities?.length > 0 || kgContext.relations?.length > 0) && (
        <div className="kg-section">
          <h3>Knowledge Graph Context</h3>
          
          {kgContext.entities && kgContext.entities.length > 0 && (
            <div className="kg-entities">
              <h4>Entities ({kgContext.entities.length})</h4>
              <div className="entity-list">
                {kgContext.entities.map((entity, index) => (
                  <div key={entity.entity_id || index} className="entity-item">
                    <strong>{entity.name}</strong>
                    <span className="entity-type">{entity.entity_type}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {kgContext.relations && kgContext.relations.length > 0 && (
            <div className="kg-relations">
              <h4>Relations ({kgContext.relations.length})</h4>
              <div className="relation-list">
                {kgContext.relations.map((rel, index) => (
                  <div key={index} className="relation-item">
                    <span className="relation-source">{rel.source_entity}</span>
                    <span className="relation-arrow">--[{rel.relation_type}]--&gt;</span>
                    <span className="relation-target">{rel.target_entity}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {kgContext.traversal_path && kgContext.traversal_path.length > 0 && (
            <details className="kg-path">
              <summary>Graph Traversal Path</summary>
              <ul>
                {kgContext.traversal_path.map((step, index) => (
                  <li key={index}>{step}</li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}
    </div>
  );
}

