/**
 * API client for communicating with the backend.
 * Handles all HTTP requests to the Hybrid RAG + KG API.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Send a query to the backend and get an answer.
 * @param {string} question - User's question
 * @param {boolean} useHybrid - Whether to use hybrid retrieval
 * @returns {Promise<Object>} Query response with answer, confidence, sources, etc.
 */
export async function query(question, useHybrid = true) {
  try {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: question,
        use_hybrid: useHybrid,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error querying API:', error);
    throw error;
  }
}

/**
 * Ingest a document into the system.
 * @param {string} fileName - Name of the file
 * @param {string} fileContent - Base64 encoded file content or plain text
 * @param {string} fileType - File type: 'pdf' or 'txt'
 * @returns {Promise<Object>} Ingestion response with document ID and stats
 */
export async function ingestDocument(fileName, fileContent, fileType) {
  try {
    const response = await fetch(`${API_BASE_URL}/ingest/document`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        file_name: fileName,
        file_content: fileContent,
        file_type: fileType,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error ingesting document:', error);
    throw error;
  }
}

/**
 * Check system health status.
 * @returns {Promise<Object>} Health response with system status
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error checking health:', error);
    throw error;
  }
}

