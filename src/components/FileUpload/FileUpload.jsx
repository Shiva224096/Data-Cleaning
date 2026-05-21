import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadFile } from '../../utils/api';
import './FileUpload.css';

const ACCEPTED_TYPES = {
  'text/csv': ['.csv'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/vnd.ms-excel': ['.xls'],
};

function FileUpload({ onFileUploaded }) {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const onDrop = useCallback(async (acceptedFiles, rejectedFiles) => {
    setError(null);

    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      if (rejection.errors[0]?.code === 'file-invalid-type') {
        setError('Invalid file type. Please upload a .csv, .xlsx, or .xls file.');
      } else {
        setError(rejection.errors[0]?.message || 'File upload failed.');
      }
      return;
    }

    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setSelectedFile(file);
    setUploading(true);
    setUploadProgress(0);

    try {
      const result = await uploadFile(file, (progress) => {
        setUploadProgress(progress);
      });
      
      // Brief pause to show 100%
      setUploadProgress(100);
      await new Promise(r => setTimeout(r, 500));
      
      onFileUploaded(result.file_id, file.name);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
      setUploading(false);
      setUploadProgress(0);
    }
  }, [onFileUploaded]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    multiple: false,
    disabled: uploading,
  });

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  return (
    <div className="file-upload-container">
      <div className="upload-hero">
        <h2 className="upload-title">
          Upload Your <span className="gradient-text">Dataset</span>
        </h2>
        <p className="upload-subtitle">
          Drop your Excel or CSV file to begin the data cleaning process
        </p>
      </div>

      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'drag-active' : ''} ${isDragReject ? 'drag-reject' : ''} ${uploading ? 'uploading' : ''} ${error ? 'has-error' : ''}`}
      >
        <input {...getInputProps()} id="file-upload-input" />
        
        {uploading ? (
          <div className="upload-progress-container">
            <div className="upload-spinner">
              <svg className="spinner-ring" viewBox="0 0 60 60">
                <circle cx="30" cy="30" r="26" fill="none" stroke="rgba(59,130,246,0.15)" strokeWidth="4" />
                <circle cx="30" cy="30" r="26" fill="none" stroke="url(#spinnerGrad)" strokeWidth="4" strokeLinecap="round" strokeDasharray="120 200" className="spinner-arc" />
                <defs>
                  <linearGradient id="spinnerGrad" x1="0" y1="0" x2="1" y2="1">
                    <stop stopColor="#3b82f6" />
                    <stop offset="1" stopColor="#8b5cf6" />
                  </linearGradient>
                </defs>
              </svg>
              <span className="progress-percentage">{uploadProgress}%</span>
            </div>
            <p className="upload-status">Uploading {selectedFile?.name}...</p>
            <div className="progress-bar-container">
              <div className="progress-bar-fill" style={{ width: `${uploadProgress}%` }} />
            </div>
          </div>
        ) : (
          <>
            <div className="dropzone-icon">
              <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                <rect x="8" y="16" width="48" height="36" rx="4" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.3" />
                <path d="M32 12v28M22 24l10-12 10 12" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div className="dropzone-text">
              <p className="dropzone-primary">
                {isDragActive ? 'Drop your file here!' : 'Drag & drop your file here'}
              </p>
              <p className="dropzone-secondary">
                or <span className="browse-link">browse files</span>
              </p>
            </div>
            <div className="dropzone-formats">
              <span className="format-badge">.CSV</span>
              <span className="format-badge">.XLSX</span>
              <span className="format-badge">.XLS</span>
            </div>
          </>
        )}
      </div>

      {error && (
        <div className="upload-error">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
            <path d="M8 5v4M8 11h.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      <div className="upload-features">
        <div className="feature-item">
          <div className="feature-icon">🔒</div>
          <div>
            <h4>Secure Processing</h4>
            <p>Your data never leaves your machine</p>
          </div>
        </div>
        <div className="feature-item">
          <div className="feature-icon">⚡</div>
          <div>
            <h4>Fast Analysis</h4>
            <p>ML-powered column detection</p>
          </div>
        </div>
        <div className="feature-item">
          <div className="feature-icon">🎯</div>
          <div>
            <h4>25+ Validators</h4>
            <p>Email, phone, IBAN, and more</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default FileUpload;
