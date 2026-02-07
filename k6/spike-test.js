// Spike Test - Sudden Traffic Surge
// Tests system resilience to sudden traffic spikes (e.g., when enrollment opens)

import { config } from './config.js';
import { enrollmentRushUser, browseAndSearchUser } from './scenarios.js';

export const options = {
  stages: [
    { duration: '1m', target: 500 },     // Normal load
    { duration: '30s', target: 15000 },  // SUDDEN SPIKE (enrollment opens!)
    { duration: '3m', target: 15000 },   // Sustain spike
    { duration: '30s', target: 500 },    // Quick drop
    { duration: '2m', target: 500 },     // Back to normal
    { duration: '30s', target: 12000 },  // Another spike
    { duration: '2m', target: 12000 },   // Sustain
    { duration: '1m', target: 0 },       // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<4000'],
    http_req_failed: ['rate<0.10'],
    http_reqs: ['rate>200'],
  },
  ext: {
    loadimpact: {
      name: 'theCourseForum - SPIKE Test (Sudden Traffic Surge)',
      projectID: 3477348,
    },
  },
};

export default function () {
  // During spikes, users are frantic
  if (Math.random() < 0.8) {
    enrollmentRushUser();
  } else {
    browseAndSearchUser();
  }
}
