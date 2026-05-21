import { useState, useCallback } from 'react';
import WizardLayout from './components/Wizard/WizardLayout';
import FileUpload from './components/FileUpload/FileUpload';
import ProfilingLoader from './components/Profiling/ProfilingLoader';
import ColumnMapping from './components/ColumnMapping/ColumnMapping';
import CleaningProgress from './components/CleaningProgress/CleaningProgress';
import Dashboard from './components/Dashboard/Dashboard';
import DataGrid from './components/DataGrid/DataGrid';
import ExportPanel from './components/Export/ExportPanel';
import './App.css';

const STEPS = [
  { id: 'upload', label: 'Upload', icon: '📤' },
  { id: 'profile', label: 'Profile', icon: '🔍' },
  { id: 'map', label: 'Map Columns', icon: '🗺️' },
  { id: 'clean', label: 'Clean', icon: '🧹' },
  { id: 'review', label: 'Review', icon: '📊' },
  { id: 'export', label: 'Export', icon: '📥' },
];

function App() {
  const [currentStep, setCurrentStep] = useState(0);
  const [fileId, setFileId] = useState(null);
  const [fileName, setFileName] = useState('');
  const [profileData, setProfileData] = useState(null);
  const [columnMapping, setColumnMapping] = useState(null);
  const [cleaningResults, setCleaningResults] = useState(null);
  const [gridData, setGridData] = useState(null);
  const [issuesSummary, setIssuesSummary] = useState(null);
  const [drillDownColumn, setDrillDownColumn] = useState(null);
  const [showGrid, setShowGrid] = useState(false);

  const goToStep = useCallback((step) => {
    setCurrentStep(step);
  }, []);

  const handleFileUploaded = useCallback((id, name) => {
    setFileId(id);
    setFileName(name);
    setCurrentStep(1);
  }, []);

  const handleProfilingComplete = useCallback((data) => {
    setProfileData(data);
    setCurrentStep(2);
  }, []);

  const handleMappingConfirmed = useCallback((mapping) => {
    setColumnMapping(mapping);
    setCurrentStep(3);
  }, []);

  const handleCleaningComplete = useCallback((results) => {
    setCleaningResults(results);
    setGridData(results.data);
    setIssuesSummary(results.summary);
    setCurrentStep(4);
  }, []);

  const handleDrillDown = useCallback((column) => {
    setDrillDownColumn(column);
    setShowGrid(true);
  }, []);

  const handleBackToDashboard = useCallback(() => {
    setShowGrid(false);
    setDrillDownColumn(null);
  }, []);

  const handleGoToExport = useCallback(() => {
    setCurrentStep(5);
  }, []);

  const handleCellEdit = useCallback((rowIndex, field, newValue) => {
    setGridData(prev => {
      const updated = [...prev];
      updated[rowIndex] = { ...updated[rowIndex], [field]: newValue };
      return updated;
    });
  }, []);

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return <FileUpload onFileUploaded={handleFileUploaded} />;
      case 1:
        return (
          <ProfilingLoader
            fileId={fileId}
            onComplete={handleProfilingComplete}
          />
        );
      case 2:
        return (
          <ColumnMapping
            fileId={fileId}
            profileData={profileData}
            onConfirm={handleMappingConfirmed}
          />
        );
      case 3:
        return (
          <CleaningProgress
            fileId={fileId}
            columnMapping={columnMapping}
            onComplete={handleCleaningComplete}
          />
        );
      case 4:
        return showGrid ? (
          <DataGrid
            data={gridData}
            issues={cleaningResults?.issues}
            filterColumn={drillDownColumn}
            onCellEdit={handleCellEdit}
            onBack={handleBackToDashboard}
          />
        ) : (
          <Dashboard
            summary={issuesSummary}
            data={gridData}
            issues={cleaningResults?.issues}
            onDrillDown={handleDrillDown}
            onGoToExport={handleGoToExport}
            onViewGrid={() => setShowGrid(true)}
          />
        );
      case 5:
        return (
          <ExportPanel
            fileId={fileId}
            fileName={fileName}
            data={gridData}
            issues={cleaningResults?.issues}
            summary={issuesSummary}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-logo">
          <div className="logo-icon">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="url(#logoGrad)" />
              <path d="M8 16h16M12 11h8M10 21h12" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" />
              <path d="M22 8l2 3-2 3" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <defs>
                <linearGradient id="logoGrad" x1="0" y1="0" x2="32" y2="32">
                  <stop stopColor="#3b82f6" />
                  <stop offset="1" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div className="logo-text">
            <h1>DataScrub</h1>
            <span className="logo-tagline">Intelligent Data Cleaning</span>
          </div>
        </div>
        {fileName && (
          <div className="file-indicator">
            <span className="file-icon">📄</span>
            <span className="file-name">{fileName}</span>
          </div>
        )}
      </header>

      <WizardLayout
        steps={STEPS}
        currentStep={currentStep}
        onStepClick={goToStep}
      />

      <main className="app-main">
        <div className="step-content" key={`${currentStep}-${showGrid}`}>
          {renderStep()}
        </div>
      </main>
    </div>
  );
}

export default App;
