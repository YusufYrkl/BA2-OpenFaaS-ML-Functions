import http from "k6/http";
import { check, sleep } from "k6";
import { SharedArray } from "k6/data";

// Konfigurationsparameter für den Load Test
const FUNCTION_NAME = "yolov5s-inference";
const BASE_URL = "http://127.0.0.1:8080"; // OpenFaaS Gateway Endpoint
const PAYLOAD_FILE = "payloads/base64_payload.json"; // Pfad zum Test-Dataset

const payloads = new SharedArray("yolo-data", function () {
  try {
    return JSON.parse(open(`./${PAYLOAD_FILE}`));
  } catch (e) {
    console.error(`Fehler beim Laden der Payload-Datei ${PAYLOAD_FILE}: ${e}`);
    return [];
  }
});

// Test-Szenarien für verschiedene Lastprofile
// Nur ein Szenario sollte aktiv sein, andere auskommentieren

// Szenario 1: Baseline Test für Funktionalität und Performance
// export let options = {
//   vus: 1,
//   iterations: 5, // Alternativ: duration: '30s'
//   thresholds: {
//     http_req_failed: ["rate<0.01"], // Max. 1% Fehlerrate
//     http_req_duration: ["p(95)<500"], // 95. Perzentil unter 500ms
//   },
//   tags: { test_type: "smoke" },
// };

// Szenario 2: Gradueller Lastanstieg für Skalierungstest
// export let options = {
//   stages: [
//     // Warmup Phase für Container-Startup
//     { duration: "30s", target: 3 }, // Initiale Last für Container-Provisioning
//     { duration: "1m", target: 3 }, // Warmup-Phase

//     { duration: "30s", target: 5 }, // Erhöhung auf mittlere Last
//     { duration: "1m", target: 5 }, // Stabilisierung
//     { duration: "30s", target: 10 }, // Erhöhung auf hohe Last
//     { duration: "1m", target: 10 }, // Stabilisierung
//     { duration: "30s", target: 0 }, // Cleanup
//   ],
//   thresholds: {
//     http_req_failed: ["rate<0.02"], // Max. 2% Fehlerrate
//   },
//   tags: { test_type: "ramp-up" },
// };

// Szenario 3: Burst Test für Spitzenlastverhalten
// export let options = {
//   stages: [
//     // Warmup Phase
//     { duration: "30s", target: 3 }, // Container-Provisioning
//     { duration: "1m", target: 3 }, // Warmup

//     { duration: "30s", target: 5 }, // Baseline
//     { duration: "10s", target: 20 }, // Erster Burst
//     { duration: "1m", target: 5 }, // Recovery
//     { duration: "10s", target: 25 }, // Zweiter Burst
//     { duration: "30s", target: 0 }, // Cleanup
//   ],
//   thresholds: {
//     http_req_failed: ["rate<0.05"], // Höhere Fehlertoleranz für Burst
//   },
//   tags: { test_type: "burst-spike" },
// };

// Szenario 4: Realistisches Lastprofil mit variabler Auslastung
export let options = {
  stages: [
    // Warmup Phase
    { duration: "30s", target: 3 }, // Container-Provisioning
    { duration: "1m", target: 3 }, // Warmup

    { duration: "2m", target: 8 }, // Mittlere Last
    { duration: "5m", target: 8 }, // Stabile Phase
    { duration: "1m", target: 12 }, // Lastspitze
    { duration: "3m", target: 12 }, // Stabile Phase
    { duration: "1m", target: 5 }, // Lastreduktion
    { duration: "2m", target: 5 }, // Stabile Phase
    { duration: "30s", target: 0 }, // Cleanup
  ],
  thresholds: {
    http_req_failed: ["rate<0.02"], // Max. 2% Fehlerrate
  },
  tags: { test_type: "realistic-soak" },
  // timeout: '90s', // Optional: Request-Timeout anpassen
};

// Test-Implementierung
export default function () {
  if (payloads.length === 0) {
    console.error("Keine Payloads geladen, überspringe Iteration.");
    return;
  }

  const randomPayload = payloads[Math.floor(Math.random() * payloads.length)];
  const payloadString = JSON.stringify(randomPayload);

  const url = `${BASE_URL}/function/${FUNCTION_NAME}`;
  const params = {
    headers: {
      "Content-Type": "application/json",
    },
    // Timeout für YOLO-Inferenz anpassen
    // timeout: '290s', // Sollte unter exec_timeout der Funktion liegen
  };

  const res = http.post(url, payloadString, params);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "response contains detections": (r) => {
      try {
        const body = r.json();
        return (
          body &&
          typeof body.detections !== "undefined" &&
          Array.isArray(body.detections)
        );
      } catch (e) {
        return false;
      }
    },
  });

  sleep(1); // Think Time zwischen Requests
}
