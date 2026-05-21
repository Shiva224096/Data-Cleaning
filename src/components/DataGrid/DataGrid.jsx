import { useMemo, useCallback, useRef, useState } from 'react';
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community';
import { AgGridReact } from 'ag-grid-react';
import './DataGrid.css';

// Register AG Grid Community modules
ModuleRegistry.registerModules([AllCommunityModule]);

function DataGrid({ data, issues, filterColumn, onCellEdit, onBack }) {
  const gridRef = useRef(null);
  const [quickFilter, setQuickFilter] = useState('');
  const [showOnlyIssues, setShowOnlyIssues] = useState(false);

  // Build column definitions from data
  const columnDefs = useMemo(() => {
    if (!data || data.length === 0) return [];

    const cols = Object.keys(data[0]).map(field => ({
      field,
      headerName: field,
      editable: true,
      sortable: true,
      filter: true,
      resizable: true,
      minWidth: 120,
      flex: 1,
      // Cell styling for issues
      cellStyle: (params) => {
        const rowIdx = params.node.rowIndex;
        const issue = issues?.[field]?.[rowIdx];
        if (issue && issue !== '') {
          return {
            backgroundColor: 'rgba(239, 68, 68, 0.12)',
            borderBottom: '2px solid rgba(239, 68, 68, 0.4)',
          };
        }
        return null;
      },
      // Tooltip showing issue
      tooltipValueGetter: (params) => {
        const rowIdx = params.node.rowIndex;
        const issue = issues?.[field]?.[rowIdx];
        if (issue && issue !== '') {
          return `⚠️ ${issue}`;
        }
        return null;
      },
      cellClass: (params) => {
        const rowIdx = params.node.rowIndex;
        const issue = issues?.[field]?.[rowIdx];
        if (issue && issue !== '') return 'cell-has-issue';
        return '';
      },
    }));

    // Add row number column
    cols.unshift({
      headerName: '#',
      valueGetter: 'node.rowIndex + 1',
      width: 60,
      pinned: 'left',
      sortable: false,
      filter: false,
      editable: false,
      cellStyle: { color: '#64748b', fontWeight: '500', fontSize: '12px' },
    });

    // Add issue status column
    cols.push({
      headerName: '🔍 Issues',
      field: '_issue_status',
      width: 200,
      editable: false,
      pinned: 'right',
      cellStyle: (params) => {
        if (params.value && params.value !== '') {
          return { color: '#ef4444', fontSize: '12px' };
        }
        return { color: '#10b981', fontSize: '12px' };
      },
      valueGetter: (params) => {
        if (!issues) return '✅ Clean';
        const rowIdx = params.node.rowIndex;
        const rowIssues = [];
        Object.entries(issues).forEach(([col, colIssues]) => {
          const issue = colIssues[rowIdx];
          if (issue && issue !== '') {
            rowIssues.push(`${col}: ${issue}`);
          }
        });
        return rowIssues.length > 0 ? rowIssues.join('; ') : '✅ Clean';
      },
    });

    return cols;
  }, [data, issues]);

  // Filter data for issues-only view
  const rowData = useMemo(() => {
    if (!data) return [];
    if (!showOnlyIssues) return data;

    return data.filter((_, rowIdx) => {
      return Object.values(issues || {}).some(colIssues => {
        const issue = colIssues[rowIdx];
        return issue && issue !== '';
      });
    });
  }, [data, issues, showOnlyIssues]);

  const defaultColDef = useMemo(() => ({
    flex: 1,
    minWidth: 100,
    sortable: true,
    filter: true,
    resizable: true,
    editable: true,
    enableCellChangeFlash: true,
  }), []);

  const onCellValueChanged = useCallback((params) => {
    if (params.oldValue !== params.newValue) {
      onCellEdit(params.node.rowIndex, params.column.getId(), params.newValue);
    }
  }, [onCellEdit]);

  const onGridReady = useCallback((params) => {
    // If drilling down to a specific column, apply filter
    if (filterColumn && params.api) {
      const filterInstance = params.api.getFilterInstance(filterColumn);
      if (filterInstance) {
        // Focus on that column
        params.api.ensureColumnVisible(filterColumn);
      }
    }
  }, [filterColumn]);

  const handleExportCsv = useCallback(() => {
    if (gridRef.current?.api) {
      gridRef.current.api.exportDataAsCsv({
        fileName: 'datascrub_preview.csv',
      });
    }
  }, []);

  const issueCount = useMemo(() => {
    if (!issues || !data) return 0;
    let count = 0;
    Object.values(issues).forEach(colIssues => {
      Object.values(colIssues).forEach(issue => {
        if (issue && issue !== '') count++;
      });
    });
    return count;
  }, [issues, data]);

  return (
    <div className="datagrid-container">
      <div className="datagrid-toolbar">
        <div className="toolbar-left">
          <button className="btn-secondary back-btn" onClick={onBack} id="back-to-dashboard">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M10 12L6 8l4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Dashboard
          </button>
          {filterColumn && (
            <span className="filter-indicator">
              Filtered: <strong>{filterColumn}</strong>
              <button className="clear-filter" onClick={() => {
                if (gridRef.current?.api) {
                  gridRef.current.api.setFilterModel(null);
                }
              }}>✕</button>
            </span>
          )}
        </div>
        <div className="toolbar-center">
          <div className="search-box-grid">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <circle cx="6" cy="6" r="4.5" stroke="currentColor" strokeWidth="1.5" />
              <path d="M10 10l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            <input
              type="text"
              placeholder="Quick search..."
              value={quickFilter}
              onChange={(e) => setQuickFilter(e.target.value)}
              className="input-field quick-search"
              id="grid-quick-search"
            />
          </div>
        </div>
        <div className="toolbar-right">
          <label className="toggle-label" htmlFor="issues-toggle">
            <input
              type="checkbox"
              id="issues-toggle"
              checked={showOnlyIssues}
              onChange={(e) => setShowOnlyIssues(e.target.checked)}
              className="toggle-checkbox"
            />
            <span className="toggle-switch" />
            Show issues only ({issueCount})
          </label>
          <button className="btn-secondary" onClick={handleExportCsv}>
            📋 Export CSV
          </button>
        </div>
      </div>

      <div className="grid-wrapper">
        <AgGridReact
          ref={gridRef}
          rowData={rowData}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          pagination={true}
          paginationPageSize={50}
          paginationPageSizeSelector={[25, 50, 100, 500]}
          animateRows={true}
          enableCellTextSelection={true}
          quickFilterText={quickFilter}
          tooltipShowDelay={300}
          onCellValueChanged={onCellValueChanged}
          onGridReady={onGridReady}
          rowSelection="multiple"
          theme="legacy"
        />
      </div>

      <div className="grid-footer">
        <span>{rowData.length.toLocaleString()} rows</span>
        <span>•</span>
        <span>{(columnDefs.length - 2).toLocaleString()} columns</span>
        <span>•</span>
        <span className="footer-hint">Double-click a cell to edit • Hover highlighted cells for issue details</span>
      </div>
    </div>
  );
}

export default DataGrid;
