import { writable } from 'svelte/store';

export const currentStep = writable(0);

export const authData = writable({
  sessionId: 'SESSION-001',
  timestamp: '',
  fingerprint: null,
  camera: null,
  gps: null,
  signature: null,
  quizResult: null
});

export const sensorStatus = writable({
  fingerprint: false,
  camera: false,
  gps: false,
  rtc: false,
  signature: false,
  oled: false
});

export const logs = writable([]);

export function addLog(message) {
  logs.update(l => [...l, `[${new Date().toLocaleTimeString()}] ${message}`]);
}
