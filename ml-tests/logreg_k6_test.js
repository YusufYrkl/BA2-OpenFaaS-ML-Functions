import http from "k6/http";
import { check, sleep } from "k6";
import { SharedArray } from "k6/data";

// Konfiguration für den Load Test
const FUNCTION_NAME = "logreg-inference";
const BASE_URL = "http://127.0.0.1:8080"; // OpenFaaS Gateway URL
const PAYLOAD_FILE = "payloads/logreg-payloads.json"; // Pfad zu den Testdaten

// SharedArray für bessere Performance bei vielen VUs
const payloads = new SharedArray("logreg-data", function () {
  try {
    return JSON.parse(open(`./${PAYLOAD_FILE}`));
  } catch (e) {
    console.error(`Fehler beim Laden der Payload-Datei ${PAYLOAD_FILE}: ${e}`);
    return []; // Fallback bei Fehler
  }
});

// Test-Szenarien für verschiedene Lastprofile
// Nur ein Szenario sollte aktiv sein, andere auskommentieren

// Baseline Test - Grundlegende Funktionalität prüfen
// export let options = {
//   vus: 1,
//   iterations: 5,
//   thresholds: {
//     http_req_failed: ["rate<0.01"], // Max 1% Fehlerrate
//     http_req_duration: ["p(95)<500"], // 95% der Requests unter 500ms
//   },
//   tags: { test_type: "smoke" },
// };

// Ramp-Up Test - Lastverteilung testen
// export let options = {
//   stages: [
//     // Warmup
//     { duration: "30s", target: 3 }, // Initiale Last für Cold Start
//     { duration: "1m", target: 3 }, // Warm halten

//     { duration: "30s", target: 5 }, // Steigerung auf 5 VUs
//     { duration: "1m", target: 5 }, // Konstante Last
//     { duration: "30s", target: 10 }, // Steigerung auf 10 VUs
//     { duration: "1m", target: 10 }, // Konstante Last
//     { duration: "30s", target: 0 }, // Cleanup
//   ],
//   thresholds: {
//     http_req_failed: ["rate<0.02"], // Max 2% Fehlerrate
//   },
//   tags: { test_type: "ramp-up" },
// };

// Burst Test - Spitzenlast testen
// export let options = {
//   stages: [
//     // Warmup
//     { duration: "30s", target: 3 }, // Initiale Last
//     { duration: "1m", target: 3 }, // Warm halten

//     { duration: "30s", target: 5 }, // Baseline
//     { duration: "10s", target: 20 }, // Erster Burst
//     { duration: "1m", target: 5 }, // Recovery
//     { duration: "10s", target: 25 }, // Zweiter Burst
//     { duration: "30s", target: 0 }, // Cleanup
//   ],
//   thresholds: {
//     http_req_failed: ["rate<0.05"], // Höhere Fehlertoleranz für Bursts
//   },
//   tags: { test_type: "burst-spike" },
// };

// Realistischer Lasttest mit variabler Auslastung
// export let options = {
//   stages: [
//     // Warmup
//     { duration: "30s", target: 3 }, // Initiale Last
//     { duration: "1m", target: 3 }, // Warm halten

//     { duration: "2m", target: 8 }, // Mittlere Last
//     { duration: "5m", target: 8 }, // Konstante Last
//     { duration: "1m", target: 12 }, // Lastspitze
//     { duration: "3m", target: 12 }, // Konstante Last
//     { duration: "1m", target: 5 }, // Lastreduktion
//     { duration: "2m", target: 5 }, // Konstante Last
//     { duration: "30s", target: 0 }, // Cleanup
//   ],
//   thresholds: {
//     http_req_failed: ["rate<0.02"],
//   },
//   tags: { test_type: "realistic-soak" },
//   // timeout: '90s', // Optional: Request Timeout anpassen
// };

// Test Logik
export default function () {
  if (payloads.length === 0) {
    console.error("Keine Payloads geladen, überspringe Iteration.");
    return;
  }

  // Zufälligen Payload für Request auswählen
  const randomPayload = payloads[Math.floor(Math.random() * payloads.length)];
  const payloadString = JSON.stringify(randomPayload);

  const url = `${BASE_URL}/function/${FUNCTION_NAME}`;
  const params = {
    headers: {
      "Content-Type": "application/json",
    },
  };

  const res = http.post(url, payloadString, params);

  // Response Validierung
  check(res, {
    "status is 200": (r) => r.status === 200,
    "response contains prediction": (r) => {
      try {
        const body = r.json();
        return body && typeof body.prediction !== "undefined";
      } catch (e) {
        return false;
      }
    },
  });

  sleep(1); // Request Cooldown
}
