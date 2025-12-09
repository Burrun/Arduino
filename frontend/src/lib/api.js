import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

export const api = {
    // Session management
    startVerification: (userId) => axios.post(`${API_BASE}/start`, { userId }),

    // System info
    getRTC: () => axios.get(`${API_BASE}/rtc`),
    getSensorStatus: () => axios.get(`${API_BASE}/sensors/status`),

    // Biometric authentication
    captureFingerprint: () => axios.post(`${API_BASE}/fingerprint`),
    captureCamera: () => axios.get(`${API_BASE}/camera`),

    // OTP (News-based quiz)
    getOTP: () => axios.get(`${API_BASE}/otp`),
    submitOTP: (answer) => axios.post(`${API_BASE}/otp`, { answer }),

    // Location
    getGPS: () => axios.get(`${API_BASE}/gps`),

    // Signature
    captureSignature: (imageData) => axios.post(`${API_BASE}/signature`, { image: imageData }),

    // Mail notification
    sendMail: (senderEmail) => axios.post(`${API_BASE}/mail`, { senderEmail }),
};
