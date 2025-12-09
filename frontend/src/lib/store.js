import { writable } from 'svelte/store';

export const currentStep = writable(0);

export const authData = writable({
  logId: null,           // Server-issued verification session ID
  userId: '',            // User input ID for verification
  timestamp: '',
  fingerprint: null,
  camera: null,
  gps: null,
  signature: null,
  otpResult: null,       // OTP quiz result
  email: ''              // Email for result notification
});

export const sensorStatus = writable({
  fingerprint: false,
  camera: false,
  gps: false,
  rtc: false,
  signature: false,
  oled: false
});

export const otpData = writable({
  question: '',
  options: [],
  newsTitle: '',
  selectedAnswer: null
});

export const logs = writable([]);

export function addLog(message) {
  logs.update(l => [...l, `[${new Date().toLocaleTimeString()}] ${message}`]);
}

export function resetAuthData() {
  authData.set({
    logId: null,
    userId: '',
    timestamp: '',
    fingerprint: null,
    camera: null,
    gps: null,
    signature: null,
    otpResult: null,
    email: ''
  });
  otpData.set({
    question: '',
    options: [],
    newsTitle: '',
    selectedAnswer: null
  });
  logs.set([]);
}
