import { useEffect, useState, useRef } from 'react';
import { startProfiling, getProfilingStatus, getProfilingResults } from '../../utils/api';
import './ProfilingLoader.css';

const SCAN_MESSAGES = [
  'Reading file contents...',
  'Analyzing column structure...',
  'Detecting data types...',
  'Sampling data patterns...',
  'Running ML column prediction...',
  'Calculating statistics...',
  'Identifying missing values...',
  'Building data profile...',
  'Finalizing analysis...',
];

function ProfilingLoader({ fileId, onComplete }) {
  const [status, setStatus] = useState('starting');
  const [messageIndex, setMessageIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const pollingRef = useRef(null);
  const messageTimerRef = useRef(null);

  useEffect(() => {
    // Cycle through messages
    messageTimerRef.current = setInterval(() => {
      setMessageIndex(prev => {
        const next = prev + 1;
        if (next >= SCAN_MESSAGES.length) return prev;
        return next;
      });
    }, 1800);

    // Animate progress bar
    const progressTimer = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) return prev;
        return prev + Math.random() * 8;
      });
    }, 600);

    // Start profiling
    const initProfiling = async () => {
      try {
        // The backend POST /profile/{file_id} is synchronous and returns
        // the full profiling result directly, so use it as a fast path.
        const directResult = await startProfiling(fileId);
        setStatus('processing');

        // If the direct response already contains profile data, use it
        if (directResult && directResult.profile) {
          setProgress(100);
          setStatus('completed');
          setTimeout(() => {
            onComplete(directResult);
          }, 800);
          return;
        }

        // Fallback: poll for completion
        pollingRef.current = setInterval(async () => {
          try {
            const statusResult = await getProfilingStatus(fileId);
            // Backend returns "complete" (not "completed")
            if (statusResult.status === 'complete' || statusResult.status === 'completed') {
              clearInterval(pollingRef.current);
              const results = await getProfilingResults(fileId);
              setProgress(100);
              setStatus('completed');
              
              setTimeout(() => {
                onComplete(results);
              }, 800);
            } else if (statusResult.status === 'error') {
              clearInterval(pollingRef.current);
              setError(statusResult.message || 'Profiling failed');
              setStatus('error');
            }
          } catch (err) {
            // Keep polling on network errors
          }
        }, 1500);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to start profiling');
        setStatus('error');
      }
    };

    initProfiling();

    return () => {
      clearInterval(pollingRef.current);
      clearInterval(messageTimerRef.current);
      clearInterval(progressTimer);
    };
  }, [fileId, onComplete]);

  return (
    <div className="profiling-container">
      <div className="profiling-visual">
        {/* Animated rings */}
        <div className="scan-rings">
          <div className="ring ring-1" />
          <div className="ring ring-2" />
          <div className="ring ring-3" />
          <div className="scan-core">
            {status === 'error' ? (
              <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                <path d="M12 12l16 16M28 12L12 28" stroke="var(--error)" strokeWidth="3" strokeLinecap="round" />
              </svg>
            ) : status === 'completed' ? (
              <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                <path d="M10 20l8 8 12-16" stroke="var(--success)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            ) : (
              <svg width="40" height="40" viewBox="0 0 40 40" fill="none" className="scan-icon">
                <rect x="4" y="8" width="32" height="24" rx="3" stroke="currentColor" strokeWidth="2" fill="none" />
                <path d="M4 16h32" stroke="currentColor" strokeWidth="2" />
                <path d="M14 16v16M26 16v16" stroke="currentColor" strokeWidth="1.5" opacity="0.5" />
                <rect x="7" y="11" width="8" height="2" rx="1" fill="currentColor" opacity="0.7" />
              </svg>
            )}
          </div>
        </div>

        {/* Data stream particles */}
        <div className="data-particles">
          {[...Array(12)].map((_, i) => (
            <div
              key={i}
              className="particle"
              style={{
                left: `${10 + Math.random() * 80}%`,
                animationDelay: `${i * 0.3}s`,
                animationDuration: `${2 + Math.random() * 2}s`,
              }}
            />
          ))}
        </div>
      </div>

      <div className="profiling-info">
        <h2 className="profiling-title">
          {status === 'error'
            ? 'Profiling Error'
            : status === 'completed'
            ? 'Profile Complete!'
            : 'Analyzing Your Data'}
        </h2>
        
        <p className={`profiling-message ${error ? 'error' : ''}`}>
          {error || SCAN_MESSAGES[messageIndex]}
        </p>

        <div className="profiling-progress">
          <div className="profiling-progress-bar">
            <div
              className={`profiling-progress-fill ${status === 'error' ? 'error' : ''} ${status === 'completed' ? 'complete' : ''}`}
              style={{ width: `${Math.min(progress, 100)}%` }}
            />
          </div>
          <span className="profiling-progress-text">{Math.round(Math.min(progress, 100))}%</span>
        </div>

        {status !== 'error' && (
          <div className="profiling-steps-list">
            {SCAN_MESSAGES.slice(0, messageIndex + 1).map((msg, i) => (
              <div key={i} className={`profiling-step-item ${i === messageIndex ? 'current' : 'done'}`}>
                <span className="step-dot">
                  {i < messageIndex ? '✓' : i === messageIndex ? '◉' : '○'}
                </span>
                <span>{msg}</span>
              </div>
            ))}
          </div>
        )}

        {error && (
          <button className="btn-primary" style={{ marginTop: 16 }} onClick={() => window.location.reload()}>
            Try Again
          </button>
        )}
      </div>
    </div>
  );
}

export default ProfilingLoader;
