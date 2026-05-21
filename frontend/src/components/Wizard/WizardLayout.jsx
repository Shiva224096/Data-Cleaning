import './WizardLayout.css';

function WizardLayout({ steps, currentStep, onStepClick }) {
  const progress = ((currentStep) / (steps.length - 1)) * 100;

  return (
    <div className="wizard-container">
      <div className="wizard-track">
        <div className="wizard-progress-bg" />
        <div
          className="wizard-progress-fill"
          style={{ width: `${progress}%` }}
        />
        <div className="wizard-steps">
          {steps.map((step, index) => {
            const isCompleted = index < currentStep;
            const isActive = index === currentStep;
            const isClickable = index <= currentStep;

            return (
              <button
                key={step.id}
                className={`wizard-step ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''} ${isClickable ? 'clickable' : ''}`}
                onClick={() => isClickable && onStepClick(index)}
                disabled={!isClickable}
                aria-label={`Step ${index + 1}: ${step.label}`}
              >
                <div className="step-circle">
                  {isCompleted ? (
                    <svg className="step-check" width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M4 8l3 3 5-6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  ) : (
                    <span className="step-icon">{step.icon}</span>
                  )}
                  {isActive && <div className="step-pulse" />}
                </div>
                <span className="step-label">{step.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default WizardLayout;
