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
        // Start cleaning via REST — this is synchronous, cleaning is done
        // by the time the response returns.
        setStatus('cleaning');

        // Animate progress while waiting for the synchronous call
        const fakeProgress = setInterval(() => {
          setProgress(prev => {
            if (prev >= 90) return prev;
            return prev + Math.random() * 10;
          });
          setMessages(prev => {
            const msgs = [
              'Starting cleaning engine...',
              'Validating column data...',
              'Running type checks...',
              'Checking data patterns...',
              'Identifying issues...',
              'Processing results...',
            ];
            const nextMsg = msgs[Math.min(prev.length, msgs.length - 1)];
            return [...prev, {
              text: nextMsg,
              time: new Date().toLocaleTimeString(),
              type: 'progress',
            }];
          });
        }, 1500);

        const response = await startCleaning(fileId, columnMapping);
        clearInterval(fakeProgress);

        if (!isActive) return;

        setTotalColumns(response.columns_processed || Object.keys(columnMapping).length);
        setProcessedColumns(response.columns_processed || Object.keys(columnMapping).length);

        // Cleaning is done — now fetch the full results
        setCurrentTask('Fetching cleaned data...');
        setProgress(95);

        try {
          const results = await getCleaningResults(fileId);
          if (isActive) {
            setStatus('completed');
            setProgress(100);
            clearInterval(timerRef.current);
            setCurrentTask('Cleaning complete!');
            setTimeout(() => onComplete(results), 1000);
          }
        } catch (fetchErr) {
          // If results endpoint fails, still pass what we have from the start response
          if (isActive) {
            setStatus('completed');
            setProgress(100);
            clearInterval(timerRef.current);
            setCurrentTask('Cleaning complete!');
            setTimeout(() => onComplete({
              data: [],
              issues: {},
              summary: response.summary || [],
              total_issues: response.total_issues || 0,
            }), 1000);
          }
        }
      } catch (err) {
        if (isActive) {
          setError(err.response?.data?.detail || 'Failed to start cleaning');
          setStatus('error');
        }
      }
    };

    initCleaning();

    return () => {
      isActive = false;
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
