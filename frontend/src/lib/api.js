import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

export const api = {
    getRTC: () => axios.get(`${API_BASE}/rtc`),
    captureFingerprint: () => axios.post(`${API_BASE}/fingerprint`),
    captureCamera: () => axios.get(`${API_BASE}/camera`),
    getGPS: () => axios.get(`${API_BASE}/gps`),
    captureSignature: (imageData) => axios.post(`${API_BASE}/signature`, { image: imageData }),
};
