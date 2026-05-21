import { useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';
import './Dashboard.css';

const CHART_COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#ef4444', '#6366f1'];

function Dashboard({ summary, data, issues, onDrillDown, onGoToExport, onViewGrid }) {
  const columnIssues = useMemo(() => {
    if (!issues) return [];
    const counts = {};
    Object.entries(issues).forEach(([col, colIssues]) => {
      const errorCount = Object.values(colIssues).filter(issue => issue && issue !== '').length;
      if (errorCount > 0) {
        counts[col] = errorCount;
      }
    });
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count, percentage: ((count / (data?.length || 1)) * 100).toFixed(1) }))
      .sort((a, b) => b.count - a.count);
  }, [issues, data]);

  const issueTypeCounts = useMemo(() => {
    if (!issues) return [];
    const types = {};
    Object.entries(issues).forEach(([col, colIssues]) => {
      Object.values(colIssues).forEach(issue => {
        if (issue && issue !== '') {
          // Extract issue type from description
          const type = issue.split(':')[0] || issue.split(';')[0] || 'Other';
          types[type] = (types[type] || 0) + 1;
        }
      });
    });
    return Object.entries(types)
      .map(([name, value]) => ({ name: name.substring(0, 25), value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8);
  }, [issues]);

  const totalRows = data?.length || 0;
  const totalIssues = useMemo(() => {
    if (!issues) return 0;
    let count = 0;
    Object.values(issues).forEach(colIssues => {
      Object.values(colIssues).forEach(issue => {
        if (issue && issue !== '') count++;
      });
    });
    return count;
  }, [issues]);

  const cleanPercentage = totalRows > 0
    ? (((totalRows * Object.keys(issues || {}).length - totalIssues) / (totalRows * Object.keys(issues || {}).length)) * 100).toFixed(1)
    : 100;

  const rowsWithIssues = useMemo(() => {
    if (!issues || !data) return 0;
    let count = 0;
    data.forEach((_, rowIdx) => {
      const hasIssue = Object.values(issues).some(colIssues => {
        const issue = colIssues[rowIdx];
        return issue && issue !== '';
      });
      if (hasIssue) count++;
    });
    return count;
  }, [issues, data]);

  const missingValues = useMemo(() => {
    if (!data) return 0;
    let count = 0;
    data.forEach(row => {
      Object.values(row).forEach(val => {
        if (val === null || val === undefined || val === '' || val === 'NaN') count++;
      });
    });
    return count;
  }, [data]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="chart-tooltip">
          <p className="tooltip-label">{label}</p>
          <p className="tooltip-value">{payload[0].value} issues</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div>
          <h2 className="dashboard-title">
            Data Quality <span className="gradient-text">Report</span>
          </h2>
          <p className="dashboard-subtitle">{totalRows.toLocaleString()} rows analyzed across {Object.keys(issues || {}).length} columns</p>
        </div>
        <div className="dashboard-actions">
          <button className="btn-secondary" onClick={onViewGrid} id="view-grid-btn">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <rect x="1" y="1" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.5" />
              <rect x="9" y="1" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.5" />
              <rect x="1" y="9" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.5" />
              <rect x="9" y="9" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.5" />
            </svg>
            View All Data
          </button>
          <button className="btn-primary" onClick={onGoToExport} id="go-to-export-btn">
            📥 Export Clean Data
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card glass-card">
          <div className="card-icon" style={{ background: 'rgba(59,130,246,0.1)' }}>📊</div>
          <div className="card-content">
            <span className="card-value">{totalRows.toLocaleString()}</span>
            <span className="card-label">Total Rows</span>
          </div>
        </div>
        <div className="summary-card glass-card" style={{ cursor: 'pointer' }} onClick={onViewGrid}>
          <div className="card-icon" style={{ background: 'rgba(239,68,68,0.1)' }}>⚠️</div>
          <div className="card-content">
            <span className="card-value" style={{ color: 'var(--error)' }}>{totalIssues.toLocaleString()}</span>
            <span className="card-label">Total Issues</span>
          </div>
        </div>
        <div className="summary-card glass-card">
          <div className="card-icon" style={{ background: 'rgba(16,185,129,0.1)' }}>✅</div>
          <div className="card-content">
            <span className="card-value" style={{ color: 'var(--success)' }}>{cleanPercentage}%</span>
            <span className="card-label">Clean Score</span>
          </div>
          <div className="clean-score-bar">
            <div className="clean-score-fill" style={{ width: `${cleanPercentage}%` }} />
          </div>
        </div>
        <div className="summary-card glass-card">
          <div className="card-icon" style={{ background: 'rgba(245,158,11,0.1)' }}>🔍</div>
          <div className="card-content">
            <span className="card-value" style={{ color: 'var(--warning)' }}>{missingValues.toLocaleString()}</span>
            <span className="card-label">Missing Values</span>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="charts-row">
        {/* Issues by Column */}
        <div className="chart-card glass-card-static">
          <h3 className="chart-title">Issues by Column</h3>
          <p className="chart-subtitle">Click a bar to drill down into that column</p>
          <div className="chart-wrapper">
            {columnIssues.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={columnIssues.slice(0, 10)} margin={{ top: 5, right: 20, bottom: 60, left: 0 }}>
                  <XAxis
                    dataKey="name"
                    tick={{ fill: '#94a3b8', fontSize: 11 }}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar
                    dataKey="count"
                    radius={[6, 6, 0, 0]}
                    cursor="pointer"
                    onClick={(data) => onDrillDown(data.name)}
                  >
                    {columnIssues.slice(0, 10).map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="no-issues-message">🎉 No issues found! Your data is clean.</div>
            )}
          </div>
        </div>

        {/* Issue Types */}
        <div className="chart-card glass-card-static">
          <h3 className="chart-title">Issue Types</h3>
          <p className="chart-subtitle">Distribution of error categories</p>
          <div className="chart-wrapper">
            {issueTypeCounts.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={issueTypeCounts}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {issueTypeCounts.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend
                    wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="no-issues-message">🎉 All clear!</div>
            )}
          </div>
        </div>
      </div>

      {/* Column Issue Cards */}
      {columnIssues.length > 0 && (
        <div className="column-issues-section">
          <h3 className="section-title">Column Details</h3>
          <div className="column-cards-grid">
            {columnIssues.map((col, i) => (
              <div
                key={col.name}
                className="column-issue-card glass-card"
                onClick={() => onDrillDown(col.name)}
                style={{ animationDelay: `${i * 0.05}s`, cursor: 'pointer' }}
              >
                <div className="issue-card-header">
                  <span className="issue-column-name">{col.name}</span>
                  <span className="badge badge-error">{col.count} issues</span>
                </div>
                <div className="issue-card-bar">
                  <div
                    className="issue-card-bar-fill"
                    style={{
                      width: `${col.percentage}%`,
                      background: CHART_COLORS[i % CHART_COLORS.length],
                    }}
                  />
                </div>
                <span className="issue-card-percentage">{col.percentage}% of rows affected</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
