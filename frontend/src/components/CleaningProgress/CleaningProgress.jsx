import { useEffect, useState, useRef } from 'react';
import { startCleaning, getCleaningResults, createCleaningSocket } from '../../utils/api';
import './CleaningProgress.css';

function CleaningProgress({ fileId, columnMapping, onComplete }) {
  const [messages, setMessages] = useState([]);
  const [currentTask, setCurrentTask] = useState('Initializing cleaning engine...');
  const [progress, setProgress] = useState(0);
  const [totalColumns, setTotalColumns] = useState(0);
  const [processedColumns, setProcessedColumns] = useState(0);
  const [status, setStatus] = useState('connecting');
  const [error, setError] = useState(null);
  const [startTime] = useState(Date.now());
  const [elapsed, setElapsed] = useState(0);
  const [showSizeWarning, setShowSizeWarning] = useState(false);
  const wsRef = useRef(null);
  const timerRef = useRef(null);

  useEffect(() => {
    timerRef.current = setInterval(() => {
      const secs = Math.floor((Date.now() - startTime) / 1000);
      setElapsed(secs);
      // Show warning if processing takes > 30 seconds
      if (secs > 30) setShowSizeWarning(true);
    }, 1000);

    return () => clearInterval(timerRef.current);
  }, [startTime]);

  useEffect(() => {
    let isActive = true;

    const initCleaning = async () => {
      try {
        // Start cleaning via REST
        const response = await startCleaning(fileId, columnMapping);
        if (!isActive) return;

        setTotalColumns(response.total_columns || Object.keys(columnMapping).length);
        setStatus('cleaning');

        // Connect WebSocket for progress
        try {
          const ws = createCleaningSocket(fileId);
          wsRef.current = ws;

          ws.onmessage = (event) => {
            if (!isActive) return;
            try {
              const data = JSON.parse(event.data);

              if (data.type === 'progress') {
                setCurrentTask(data.message);
                setProcessedColumns(data.processed || 0);
                setProgress(data.progress || 0);
                setMessages(prev => [...prev, {
                  text: data.message,
                  time: new Date().toLocaleTimeString(),
                  type: 'progress',
                }]);
              } else if (data.type === 'completed') {
                setStatus('completed');
                setProgress(100);
                clearInterval(timerRef.current);

                // Fetch results
                getCleaningResults(fileId).then(results => {
                  if (isActive) {
                    setTimeout(() => onComplete(results), 1000);
                  }
                });
              } else if (data.type === 'error') {
                setError(data.message);
                setStatus('error');
              }
            } catch (e) {
              // Ignore parse errors
            }
          };

          ws.onerror = () => {
            // Fallback: poll for results
            pollForResults();
          };

          ws.onclose = () => {
            if (status !== 'completed' && isActive) {
              pollForResults();
            }
          };
        } catch (wsErr) {
          // WebSocket not available, poll instead
          pollForResults();
        }
      } catch (err) {
        if (isActive) {
          setError(err.response?.data?.detail || 'Failed to start cleaning');
          setStatus('error');
        }
      }
    };

    const pollForResults = () => {
      const pollInterval = setInterval(async () => {
        try {
          const results = await getCleaningResults(fileId);
          if (results && results.data && isActive) {
            clearInterval(pollInterval);
            setStatus('completed');
            setProgress(100);
            clearInterval(timerRef.current);
            setTimeout(() => onComplete(results), 1000);
          }
        } catch (e) {
          // Keep polling
          setProgress(prev => Math.min(prev + 5, 90));
          setProcessedColumns(prev => prev + 1);
        }
      }, 2000);
    };

    initCleaning();

    return () => {
      isActive = false;
      if (wsRef.current) wsRef.current.close();
      clearInterval(timerRef.current);
    };
  }, [fileId, columnMapping, onComplete]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  return (
    <div className="cleaning-container">
      <div className="cleaning-visual">
        <div className="cleaning-spinner-wrapper">
          <svg className="cleaning-spinner" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="52" fill="none" stroke="rgba(59,130,246,0.1)" strokeWidth="6" />
            <circle
              cx="60" cy="60" r="52"
              fill="none"
              stroke="url(#cleanGrad)"
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={`${progress * 3.27} 327`}
              style={{ transition: 'stroke-dasharray 0.5s ease' }}
            />
            <defs>
              <linearGradient id="cleanGrad" x1="0" y1="0" x2="1" y2="1">
                <stop stopColor="#3b82f6" />
                <stop offset="0.5" stopColor="#8b5cf6" />
                <stop offset="1" stopColor="#ec4899" />
              </linearGradient>
            </defs>
          </svg>
          <div className="cleaning-spinner-center">
            <span className="cleaning-percentage">{Math.round(progress)}%</span>
            <span className="cleaning-timer">{formatTime(elapsed)}</span>
          </div>
        </div>
      </div>

      <div className="cleaning-info">
        <h2 className="cleaning-title">
          {status === 'error' ? '⚠️ Cleaning Error' :
           status === 'completed' ? '✅ Cleaning Complete!' :
           '🧹 Cleaning Your Data'}
        </h2>
        
        <p className="cleaning-current-task">{error || currentTask}</p>

        {totalColumns > 0 && (
          <div className="cleaning-columns-progress">
            <span>{processedColumns} of {totalColumns} columns processed</span>
            <div className="columns-bar">
              <div
                className="columns-bar-fill"
                style={{ width: `${(processedColumns / totalColumns) * 100}%` }}
              />
            </div>
          </div>
        )}

        {showSizeWarning && status === 'cleaning' && (
          <div className="size-warning">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 1l7 13H1L8 1z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
              <path d="M8 6v4M8 12h.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            <span>Large file detected — processing may take a while. Please don't close this page.</span>
          </div>
        )}

        <div className="cleaning-log">
          <div className="log-header">
            <span className="log-dot" />
            <span>Live Progress</span>
          </div>
          <div className="log-entries">
            {messages.slice(-8).map((msg, i) => (
              <div key={i} className="log-entry" style={{ animationDelay: `${i * 0.05}s` }}>
                <span className="log-time">{msg.time}</span>
                <span className="log-text">{msg.text}</span>
              </div>
            ))}
            {messages.length === 0 && (
              <div className="log-entry placeholder">
                <span className="log-text">Waiting for progress updates...</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default CleaningProgress;
