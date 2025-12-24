import { useState } from 'react';
import { ingestDocument } from '../api';

/**
 * Document upload component.
 * Allows users to upload PDF or TXT files for ingestion.
 */
export default function DocumentUpload({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      setSuccess(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const fileType = file.name.toLowerCase().endsWith('.pdf') ? 'pdf' : 'txt';
      let fileContent;

      if (fileType === 'pdf') {
        // For PDF, we need to read as base64
        const reader = new FileReader();
        fileContent = await new Promise((resolve, reject) => {
          reader.onload = (e) => resolve(e.target.result.split(',')[1]); // Remove data:application/pdf;base64, prefix
          reader.onerror = reject;
          reader.readAsDataURL(file);
        });
      } else {
        // For TXT, read as plain text
        fileContent = await file.text();
      }

      const result = await ingestDocument(file.name, fileContent, fileType);
      
      setSuccess(`Document "${file.name}" ingested successfully! ${result.chunks_created} chunks created.`);
      setFile(null);
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
    } catch (err) {
      setError(err.message || 'Failed to upload document');
      console.error('Upload error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="document-upload">
      <h3>Upload Document</h3>
      <p className="upload-description">
        Upload a PDF or TXT file to add it to the knowledge base. After uploading, you can query the document.
      </p>
      
      <div className="upload-controls">
        <input
          type="file"
          accept=".pdf,.txt"
          onChange={handleFileChange}
          disabled={loading}
          className="file-input"
        />
        
        {file && (
          <div className="file-info">
            <p>Selected: <strong>{file.name}</strong> ({(file.size / 1024).toFixed(2)} KB)</p>
          </div>
        )}
        
        <button
          onClick={handleUpload}
          disabled={!file || loading}
          className="upload-button"
        >
          {loading ? 'Uploading...' : 'Upload Document'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {success && (
        <div className="success-message">
          <strong>Success:</strong> {success}
        </div>
      )}
    </div>
  );
}

