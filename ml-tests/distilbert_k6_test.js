import http from "k6/http";
import { check, sleep } from "k6";
import { SharedArray } from "k6/data";

// --- Konfiguration ---
const FUNCTION_NAME = "distilbert-finetuned-inference";
const BASE_URL = "http://127.0.0.1:8080"; // OpenFaaS Gateway URL
const PAYLOAD_FILE = "payloads/distilbert_payloads.json"; // Pfad zu den Testdaten

const payloads = new SharedArray("distilbert-data", function () {
  try {
    return JSON.parse(open(`./${PAYLOAD_FILE}`));
  } catch (e) {
    console.error(`Fehler beim Laden der Payload-Datei ${PAYLOAD_FILE}: ${e}`);
    return [];
  }
});

// Test-Szenarien für verschiedene Lastprofile
// Nur ein Szenario sollte aktiv sein, andere auskommentieren

// Szenario: Baseline / Smoke Test
// Einfacher Test mit minimaler Last um grundlegende Funktionalität zu prüfen

// export let options = {
//   vus: 1,
//   iterations: 5, // Alternativ: duration: '30s'
//   thresholds: {
//     http_req_failed: ["rate<0.01"], // Max 1% Fehlerrate
//     http_req_duration: ["p(95)<500"], // 95% der Requests unter 500ms
//   },
//   tags: { test_type: "smoke" },
// };

// Szenario: Ramp-Up Test
// Testet das Verhalten bei schrittweise steigender Last

// export let options = {
//   stages: [
//     // Warmup Phase
//     { duration: "30s", target: 3 }, // Start mit 3 VUs für 30s
//     { duration: "1m", target: 3 }, // Halte 3 VUs für 1 Minute

//     { duration: "30s", target: 5 }, // Steigere auf 5 VUs
//     { duration: "1m", target: 5 }, // Halte 5 VUs
//     { duration: "30s", target: 10 }, // Steigere auf 10 VUs
//     { duration: "1m", target: 10 }, // Halte 10 VUs
//     { duration: "30s", target: 0 }, // Fahre runter
//   ],
//   thresholds: {
//     http_req_failed: ["rate<0.02"], // Max 2% Fehlerrate
//   },
//   tags: { test_type: "ramp-up" },
// };

// Szenario: Burst / Spike Test
// Testet das Systemverhalten bei plötzlichen Lastspitzen

export let options = {
  stages: [
    // Warmup Phase
    { duration: "30s", target: 3 }, // Start mit 3 VUs
    { duration: "1m", target: 3 }, // Halte 3 VUs

    { duration: "30s", target: 5 }, // Normallast
    { duration: "10s", target: 20 }, // Erste Lastspitze
    { duration: "1m", target: 5 }, // Erholung
    { duration: "10s", target: 25 }, // Zweite, höhere Lastspitze
    { duration: "30s", target: 0 }, // Runterfahren
  ],
  thresholds: {
    http_req_failed: ["rate<0.05"], // Höhere Fehlertoleranz für Spikes
  },
  tags: { test_type: "burst-spike" },
};

// Szenario: Realistischer Lasttest
// Simuliert realistische Lastprofile mit natürlichen Schwankungen

// export let options = {
//   stages: [
//     // Warmup Phase
//     { duration: "30s", target: 3 }, // Start mit 3 VUs
//     { duration: "1m", target: 3 }, // Halte 3 VUs

//     { duration: "2m", target: 8 }, // Steigere auf moderates Niveau
//     { duration: "5m", target: 8 }, // Halte moderates Niveau
//     { duration: "1m", target: 12 }, // Leichte Erhöhung
//     { duration: "3m", target: 12 }, // Halte erhöhtes Niveau
//     { duration: "1m", target: 5 }, // Reduziere Last
//     { duration: "2m", target: 5 }, // Halte reduziertes Niveau
//     { duration: "30s", target: 0 }, // Fahre runter
//   ],
//   thresholds: {
//     http_req_failed: ["rate<0.02"], // Max 2% Fehlerrate
//   },
//   tags: { test_type: "realistic-soak" },
//   // timeout: '90s', // Optional: Request-Timeout anpassen
// };

// --- Test Logik ---
export default function () {
  if (payloads.length === 0) {
    console.error("Keine Payloads geladen, überspringe Iteration.");
    return;
  }

  const randomPayload = payloads[Math.floor(Math.random() * payloads.length)];
  const payloadString = JSON.stringify(randomPayload);

  const url = `${BASE_URL}/async-function/${FUNCTION_NAME}`; // Oder /function/, je nachdem ob synchron oder asynchron
  // Basierend auf deinen Handlern scheinen sie synchron zu sein, also /function/
  // const url = `${BASE_URL}/function/${FUNCTION_NAME}`;

  const params = {
    headers: {
      "Content-Type": "application/json",
    },
  };

  const res = http.post(url, payloadString, params);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "response contains label and score": (r) => {
      try {
        const body = r.json();
        return (
          body &&
          typeof body.label !== "undefined" &&
          typeof body.score !== "undefined"
        );
      } catch (e) {
        return false;
      }
    },
  });

  sleep(1);
}
