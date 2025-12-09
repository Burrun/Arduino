import axios from 'axios';
import { get } from 'svelte/store';
import { logId } from './store';

// Use relative URL so it works with any port
const API_BASE = '/api';

export const api = {
    // Sensor APIs (local)
    getRTC: () => axios.get(`${API_BASE}/rtc`),
    captureFingerprint: () => axios.post(`${API_BASE}/fingerprint`),
    captureCamera: () => axios.get(`${API_BASE}/camera`),
    getGPS: () => axios.get(`${API_BASE}/gps`),

    // Legacy signature endpoint (local storage only)
    captureSignature: (imageData) => axios.post(`${API_BASE}/signature`, { image: imageData }),

    // AuthBox verification APIs
    login: (id, password) => axios.post(`${API_BASE}/user/login`, { id, password }),
    startVerification: (userId) => axios.post(`${API_BASE}/verification/start`, { userId }),
    verifyGPS: (lat, lon) => {
        const currentLogId = get(logId);
        return axios.post(`${API_BASE}/verification/${currentLogId}/gps`, { latitude: lat, longitude: lon });
    },
    verifyOTP: (userReporter) => {
        const currentLogId = get(logId);
        return axios.post(`${API_BASE}/verification/${currentLogId}/otp`, { userReporter });
    },
    verifyFace: () => {
        const currentLogId = get(logId);
        return axios.post(`${API_BASE}/verification/${currentLogId}/face`);
    },
    verifyFingerprint: () => {
        const currentLogId = get(logId);
        return axios.post(`${API_BASE}/verification/${currentLogId}/fingerprint`);
    },
    verifySignature: (imageData) => {
        const currentLogId = get(logId);
        return axios.post(`${API_BASE}/verification/${currentLogId}/signature`, { image: imageData });
    },
    sendMail: (senderEmail) => {
        const currentLogId = get(logId);
        return axios.post(`${API_BASE}/verification/${currentLogId}/mail`, { senderEmail });
    },
};
