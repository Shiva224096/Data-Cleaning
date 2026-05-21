import { useState, useMemo } from 'react';
import { exportFile } from '../../utils/api';
import './ExportPanel.css';

function ExportPanel({ fileId, fileName, data, issues, summary }) {
  const [format, setFormat] = useState('xlsx');
  const [exporting, setExporting] = useState(false);
  const [exported, setExported] = useState(false);

  // Build issue status preview
  const issueStatusPreview = useMemo(() => {
    if (!data || !issues) return [];
    return data.slice(0, 8).map((row, rowIdx) => {
      const rowIssues = [];
      Object.entries(issues).forEach(([col, colIssues]) => {
        const issue = colIssues[rowIdx];
        if (issue && issue !== '') {
          rowIssues.push(`${col}: ${issue}`);
        }
      });
      return {
        row: rowIdx + 1,
        firstCol: Object.values(row)[0],
        status: rowIssues.length > 0 ? rowIssues.join('; ') : '✅ Clean',
        hasIssues: rowIssues.length > 0,
      };
    });
  }, [data, issues]);

  const totalRows = data?.length || 0;
  const totalIssueRows = useMemo(() => {
    if (!data || !issues) return 0;
    let count = 0;
    data.forEach((_, rowIdx) => {
      const hasIssue = Object.values(issues).some(colIssues => {
        const issue = colIssues[rowIdx];
        return issue && issue !== '';
      });
      if (hasIssue) count++;
    });
    return count;
  }, [data, issues]);

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await exportFile(fileId, format, data);
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      const baseName = fileName?.replace(/\.[^/.]+$/, '') || 'datascrub_export';
      link.href = url;
      link.setAttribute('download', `${baseName}_cleaned.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setExported(true);
    } catch (err) {
      // Fallback: generate client-side CSV
      try {
        const csvContent = generateClientCSV();
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        const baseName = fileName?.replace(/\.[^/.]+$/, '') || 'datascrub_export';
        link.href = url;
        link.setAttribute('download', `${baseName}_cleaned.csv`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        setExported(true);
      } catch (fallbackErr) {
        alert('Export failed. Please try again.');
      }
    } finally {
      setExporting(false);
    }
  };

  const generateClientCSV = () => {
    if (!data || data.length === 0) return '';
    
    const headers = [...Object.keys(data[0]), 'DataScrub_Issue_Status'];
    const rows = data.map((row, rowIdx) => {
      const rowIssues = [];
      Object.entries(issues || {}).forEach(([col, colIssues]) => {
        const issue = colIssues[rowIdx];
        if (issue && issue !== '') {
          rowIssues.push(`${col}: ${issue}`);
        }
      });
      const statusStr = rowIssues.length > 0 ? rowIssues.join('; ') : '';
      
      const values = Object.values(row).map(v => {
        const str = String(v ?? '');
        // Escape CSV
        if (str.includes(',') || str.includes('"') || str.includes('\n')) {
          return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
      });
      
      const statusEscaped = statusStr.includes(',') || statusStr.includes('"')
        ? `"${statusStr.replace(/"/g, '""')}"`
        : statusStr;
      
      return [...values, statusEscaped].join(',');
    });
    
    return [headers.join(','), ...rows].join('\n');
  };

  return (
    <div className="export-container">
      <div className="export-hero">
        <div className="export-icon-wrapper">
          {exported ? (
            <div className="export-success-icon">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                <circle cx="24" cy="24" r="22" stroke="var(--success)" strokeWidth="3" />
                <path d="M14 24l7 7 13-17" stroke="var(--success)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
          ) : (
            <div className="export-download-icon">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                <rect x="8" y="6" width="32" height="36" rx="4" stroke="currentColor" strokeWidth="2.5" fill="none" />
                <path d="M24 16v14M18 24l6 6 6-6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M14 36h20" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
              </svg>
            </div>
          )}
        </div>
        <h2 className="export-title">
          {exported ? 'Export Complete!' : 'Export Your'} <span className="gradient-text">{exported ? '🎉' : 'Clean Data'}</span>
        </h2>
        <p className="export-subtitle">
          {exported
            ? 'Your cleaned file has been downloaded with the DataScrub_Issue_Status column appended.'
            : 'Download your cleaned dataset with a detailed issue status column.'}
        </p>
      </div>

      {/* Stats Summary */}
      <div className="export-stats glass-card-static">
        <div className="stat-item">
          <span className="stat-number">{totalRows.toLocaleString()}</span>
          <span className="stat-desc">Total Rows</span>
        </div>
        <div className="stat-divider-v" />
        <div className="stat-item">
          <span className="stat-number" style={{ color: 'var(--success)' }}>
            {(totalRows - totalIssueRows).toLocaleString()}
          </span>
          <span className="stat-desc">Clean Rows</span>
        </div>
        <div className="stat-divider-v" />
        <div className="stat-item">
          <span className="stat-number" style={{ color: 'var(--warning)' }}>
            {totalIssueRows.toLocaleString()}
          </span>
          <span className="stat-desc">Rows with Issues</span>
        </div>
        <div className="stat-divider-v" />
        <div className="stat-item">
          <span className="stat-number" style={{ color: 'var(--accent-secondary)' }}>
            {Object.keys(issues || {}).length}
          </span>
          <span className="stat-desc">Columns Analyzed</span>
        </div>
      </div>

      {/* Format Selection */}
      {!exported && (
        <div className="export-format-section">
          <h3 className="section-label">Export Format</h3>
          <div className="format-options">
            <label
              className={`format-option glass-card ${format === 'xlsx' ? 'selected' : ''}`}
              htmlFor="fmt-xlsx"
            >
              <input
                type="radio"
                name="format"
                id="fmt-xlsx"
                value="xlsx"
                checked={format === 'xlsx'}
                onChange={() => setFormat('xlsx')}
                className="format-radio"
              />
              <div className="format-icon">📊</div>
              <div className="format-details">
                <span className="format-name">Excel (.xlsx)</span>
                <span className="format-desc">Best for analysis and editing</span>
              </div>
              {format === 'xlsx' && <span className="format-check">✓</span>}
            </label>
            <label
              className={`format-option glass-card ${format === 'csv' ? 'selected' : ''}`}
              htmlFor="fmt-csv"
            >
              <input
                type="radio"
                name="format"
                id="fmt-csv"
                value="csv"
                checked={format === 'csv'}
                onChange={() => setFormat('csv')}
                className="format-radio"
              />
              <div className="format-icon">📄</div>
              <div className="format-details">
                <span className="format-name">CSV (.csv)</span>
                <span className="format-desc">Universal compatibility</span>
              </div>
              {format === 'csv' && <span className="format-check">✓</span>}
            </label>
          </div>
        </div>
      )}

      {/* Issue Status Column Preview */}
      <div className="status-preview glass-card-static">
        <h3 className="preview-title">
          <span className="preview-dot" />
          DataScrub_Issue_Status Column Preview
        </h3>
        <div className="preview-table-wrapper">
          <table className="preview-table">
            <thead>
              <tr>
                <th>Row</th>
                <th>First Column Value</th>
                <th>DataScrub_Issue_Status</th>
              </tr>
            </thead>
            <tbody>
              {issueStatusPreview.map((item) => (
                <tr key={item.row} className={item.hasIssues ? 'has-issues' : ''}>
                  <td className="cell-row">{item.row}</td>
                  <td className="cell-first">{String(item.firstCol).substring(0, 30)}</td>
                  <td className={`cell-status ${item.hasIssues ? 'error' : 'clean'}`}>
                    {item.status.substring(0, 80)}{item.status.length > 80 ? '...' : ''}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {totalRows > 8 && (
          <p className="preview-note">Showing first 8 of {totalRows.toLocaleString()} rows</p>
        )}
      </div>

      {/* Export Button */}
      <div className="export-action">
        {exported ? (
          <div className="export-done-actions">
            <button className="btn-primary" onClick={() => { setExported(false); }}>
              ↻ Export Again
            </button>
            <button className="btn-secondary" onClick={() => window.location.reload()}>
              🔄 Clean Another File
            </button>
          </div>
        ) : (
          <button
            className="btn-primary export-btn"
            onClick={handleExport}
            disabled={exporting}
            id="export-download-btn"
          >
            {exporting ? (
              <>
                <svg className="btn-spinner" width="18" height="18" viewBox="0 0 18 18">
                  <circle cx="9" cy="9" r="7" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="30 14" />
                </svg>
                Exporting...
              </>
            ) : (
              <>
                📥 Download {format.toUpperCase()} with Issue Status
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

export default ExportPanel;
