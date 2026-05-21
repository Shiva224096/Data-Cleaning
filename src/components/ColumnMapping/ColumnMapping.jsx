import { useState, useMemo } from 'react';
import './ColumnMapping.css';

const FIELD_PROFILES = {
  'Personal & Contact': [
    { value: 'email', label: 'Email Address' },
    { value: 'mobile_phone', label: 'Mobile Number (International)' },
    { value: 'landline', label: 'Telephone / Landline' },
    { value: 'first_name', label: 'First Name' },
    { value: 'last_name', label: 'Last Name' },
    { value: 'zip_code', label: 'Zip / Postal Code' },
  ],
  'Business & Financial': [
    { value: 'company_name', label: 'Company Name (Fuzzy Match)' },
    { value: 'iban', label: 'IBAN' },
    { value: 'credit_card', label: 'Credit Card Number' },
    { value: 'currency', label: 'Currency / Amount' },
    { value: 'pan', label: 'Indian PAN Number' },
    { value: 'gst', label: 'Indian GST Number' },
    { value: 'ssn', label: 'US Social Security Number' },
  ],
  'Web & Technology': [
    { value: 'url', label: 'URL / Domain Name' },
    { value: 'ipv4', label: 'IP Address (IPv4)' },
    { value: 'ipv6', label: 'IP Address (IPv6)' },
    { value: 'mac_address', label: 'MAC Address' },
    { value: 'hex_color', label: 'Hex Color Code' },
  ],
  'General Identifiers': [
    { value: 'uuid', label: 'UUID / GUID' },
    { value: 'isbn', label: 'ISBN (Books)' },
    { value: 'vin', label: 'VIN (Vehicles)' },
    { value: 'string', label: 'String (Text)' },
    { value: 'integer', label: 'Integer' },
    { value: 'float', label: 'Float / Decimal' },
    { value: 'date', label: 'Date' },
    { value: 'datetime', label: 'Date & Time' },
    { value: 'skip', label: '⏭️ Skip this column' },
  ],
};

const COUNTRY_CODES = [
  { code: 'US', label: '🇺🇸 United States (+1)' },
  { code: 'GB', label: '🇬🇧 United Kingdom (+44)' },
  { code: 'IN', label: '🇮🇳 India (+91)' },
  { code: 'DE', label: '🇩🇪 Germany (+49)' },
  { code: 'FR', label: '🇫🇷 France (+33)' },
  { code: 'JP', label: '🇯🇵 Japan (+81)' },
  { code: 'AU', label: '🇦🇺 Australia (+61)' },
  { code: 'CA', label: '🇨🇦 Canada (+1)' },
  { code: 'BR', label: '🇧🇷 Brazil (+55)' },
  { code: 'CN', label: '🇨🇳 China (+86)' },
  { code: 'AE', label: '🇦🇪 UAE (+971)' },
  { code: 'SG', label: '🇸🇬 Singapore (+65)' },
  { code: 'ZA', label: '🇿🇦 South Africa (+27)' },
  { code: 'MX', label: '🇲🇽 Mexico (+52)' },
  { code: 'KR', label: '🇰🇷 South Korea (+82)' },
];

function ColumnMapping({ fileId, profileData, onConfirm }) {
  const [mapping, setMapping] = useState(() => {
    if (!profileData?.columns) return {};
    const initial = {};
    profileData.columns.forEach(col => {
      initial[col.name] = {
        profile: col.suggested_profile || 'string',
        confidence: col.confidence || 0,
        region: 'US',
        fuzzy_threshold: 85,
      };
    });
    return initial;
  });

  const [searchFilter, setSearchFilter] = useState('');

  const filteredColumns = useMemo(() => {
    if (!profileData?.columns) return [];
    if (!searchFilter) return profileData.columns;
    return profileData.columns.filter(col =>
      col.name.toLowerCase().includes(searchFilter.toLowerCase())
    );
  }, [profileData, searchFilter]);

  const handleProfileChange = (columnName, profile) => {
    setMapping(prev => ({
      ...prev,
      [columnName]: { ...prev[columnName], profile },
    }));
  };

  const handleRegionChange = (columnName, region) => {
    setMapping(prev => ({
      ...prev,
      [columnName]: { ...prev[columnName], region },
    }));
  };

  const handleThresholdChange = (columnName, threshold) => {
    setMapping(prev => ({
      ...prev,
      [columnName]: { ...prev[columnName], fuzzy_threshold: Number(threshold) },
    }));
  };

  const handleConfirm = () => {
    onConfirm(mapping);
  };

  const getConfidenceBadge = (confidence) => {
    if (confidence >= 0.8) return <span className="badge badge-success">High</span>;
    if (confidence >= 0.5) return <span className="badge badge-warning">Medium</span>;
    return <span className="badge badge-error">Low</span>;
  };

  const isPhoneProfile = (profile) => ['mobile_phone', 'landline'].includes(profile);
  const isCompanyProfile = (profile) => profile === 'company_name';

  if (!profileData?.columns) {
    return <div className="mapping-loading">Loading column data...</div>;
  }

  return (
    <div className="column-mapping-container">
      <div className="mapping-header">
        <div>
          <h2 className="mapping-title">
            Map Your <span className="gradient-text">Columns</span>
          </h2>
          <p className="mapping-subtitle">
            We detected {profileData.columns.length} columns. Review and confirm the data type for each column.
          </p>
        </div>
        <div className="mapping-actions">
          <div className="search-box">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
              <path d="M11 11l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            <input
              type="text"
              placeholder="Search columns..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="input-field search-input"
              id="column-search"
            />
          </div>
        </div>
      </div>

      <div className="mapping-table-wrapper glass-card-static">
        <table className="mapping-table">
          <thead>
            <tr>
              <th className="th-index">#</th>
              <th className="th-column">Column Name</th>
              <th className="th-samples">Sample Values</th>
              <th className="th-suggested">ML Suggestion</th>
              <th className="th-confidence">Confidence</th>
              <th className="th-profile">Assigned Profile</th>
              <th className="th-options">Options</th>
            </tr>
          </thead>
          <tbody>
            {filteredColumns.map((col, index) => {
              const colMapping = mapping[col.name] || {};
              return (
                <tr key={col.name} className="mapping-row" style={{ animationDelay: `${index * 0.04}s` }}>
                  <td className="cell-index">{index + 1}</td>
                  <td className="cell-column">
                    <span className="column-name">{col.name}</span>
                    <span className="column-dtype">{col.dtype}</span>
                  </td>
                  <td className="cell-samples">
                    <div className="samples-list">
                      {(col.sample_values || []).slice(0, 3).map((val, i) => (
                        <code key={i} className="sample-value">{String(val).substring(0, 30)}</code>
                      ))}
                    </div>
                  </td>
                  <td className="cell-suggested">
                    <span className="suggested-label">{col.suggested_label || 'Text'}</span>
                  </td>
                  <td className="cell-confidence">
                    {getConfidenceBadge(col.confidence || 0)}
                  </td>
                  <td className="cell-profile">
                    <select
                      value={colMapping.profile || 'string'}
                      onChange={(e) => handleProfileChange(col.name, e.target.value)}
                      className="select-field profile-select"
                      id={`profile-select-${col.name}`}
                    >
                      {Object.entries(FIELD_PROFILES).map(([group, profiles]) => (
                        <optgroup key={group} label={group}>
                          {profiles.map(p => (
                            <option key={p.value} value={p.value}>{p.label}</option>
                          ))}
                        </optgroup>
                      ))}
                    </select>
                  </td>
                  <td className="cell-options">
                    {isPhoneProfile(colMapping.profile) && (
                      <select
                        value={colMapping.region || 'US'}
                        onChange={(e) => handleRegionChange(col.name, e.target.value)}
                        className="select-field option-select"
                        id={`region-select-${col.name}`}
                        title="Default country code"
                      >
                        {COUNTRY_CODES.map(c => (
                          <option key={c.code} value={c.code}>{c.label}</option>
                        ))}
                      </select>
                    )}
                    {isCompanyProfile(colMapping.profile) && (
                      <div className="threshold-control">
                        <label className="threshold-label">
                          Match: {colMapping.fuzzy_threshold || 85}%
                        </label>
                        <input
                          type="range"
                          min="50"
                          max="100"
                          value={colMapping.fuzzy_threshold || 85}
                          onChange={(e) => handleThresholdChange(col.name, e.target.value)}
                          className="threshold-slider"
                          id={`threshold-${col.name}`}
                        />
                      </div>
                    )}
                    {!isPhoneProfile(colMapping.profile) && !isCompanyProfile(colMapping.profile) && (
                      <span className="no-options">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mapping-footer">
        <div className="mapping-stats">
          <span>{Object.values(mapping).filter(m => m.profile !== 'skip').length} columns mapped</span>
          <span className="stat-divider">•</span>
          <span>{Object.values(mapping).filter(m => m.profile === 'skip').length} skipped</span>
        </div>
        <button
          className="btn-primary confirm-btn"
          onClick={handleConfirm}
          id="confirm-mapping-btn"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M4 9l4 4 6-8" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Confirm & Start Cleaning
        </button>
      </div>
    </div>
  );
}

export default ColumnMapping;
