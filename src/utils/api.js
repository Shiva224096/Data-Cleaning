import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? 'https://datascrub-backend.onrender.com' : 'http://localhost:8000');

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 300000, // 5 min timeout for large files
});

// File Upload
export const uploadFile = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    },
  });
  return response.data;
};

// Profiling
export const startProfiling = async (fileId) => {
  const response = await api.post(`/profile/${fileId}`);
  return response.data;
};

export const getProfilingStatus = async (fileId) => {
  const response = await api.get(`/profile/${fileId}/status`);
  return response.data;
};

export const getProfilingResults = async (fileId) => {
  const response = await api.get(`/profile/${fileId}/results`);
  return response.data;
};

// Cleaning
export const startCleaning = async (fileId, mapping, options = {}) => {
  // Transform frontend mapping object into backend's expected format.
  // Frontend: { "col_name": { profile: "email", region: "US", fuzzy_threshold: 85 } }
  // Backend:  { file_id, column_mappings: [{ column: "col_name", type: "email", params: { region: "US" } }] }
  const columnMappings = Object.entries(mapping)
    .filter(([, val]) => val.profile !== 'skip')
    .map(([colName, val]) => {
      const params = {};
      if (val.region) params.region = val.region;
      if (val.fuzzy_threshold) params.fuzzy_threshold = val.fuzzy_threshold;
      return {
        column: colName,
        type: val.profile || 'text',
        params,
      };
    });

  const response = await api.post(`/clean/start`, {
    file_id: fileId,
    column_mappings: columnMappings,
  });
  return response.data;
};

export const getCleaningResults = async (fileId) => {
  const response = await api.get(`/clean/${fileId}/results`);
  return response.data;
};

// WebSocket for cleaning progress
export const createCleaningSocket = (fileId) => {
  const wsBase = API_BASE.replace('http', 'ws');
  return new WebSocket(`${wsBase}/ws/cleaning/${fileId}`);
};

// Export
export const exportFile = async (fileId, format = 'xlsx', data = null) => {
  const response = await api.post(`/export/${fileId}`, 
    { format, data },
    { responseType: 'blob' }
  );
  return response.data;
};

// Save cell edits
export const saveCellEdit = async (fileId, rowIndex, column, value) => {
  const response = await api.post(`/clean/${fileId}/edit`, {
    row_index: rowIndex,
    column,
    value,
  });
  return response.data;
};

export default api;
