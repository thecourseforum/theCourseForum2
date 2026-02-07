// Stress Test - Find Breaking Point
// Gradually increases load to find system limits

import { config } from './config.js';
import { enrollmentRushUser, browseAndSearchUser } from './scenarios.js';

export const options = {
  stages: [
    { duration: '2m', target: 1000 },    // Warm up
    { duration: '3m', target: 5000 },    // Scale up
    { duration: '3m', target: 10000 },   // Push further
    { duration: '3m', target: 15000 },   // Keep pushing
    { duration: '3m', target: 20000 },   // Target peak
    { duration: '3m', target: 25000 },   // Beyond peak
    { duration: '3m', target: 30000 },   // Find breaking point
    { duration: '5m', target: 30000 },   // Sustain to see impact
    { duration: '3m', target: 0 },       // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'],
    http_req_failed: ['rate<0.15'], // Allow up to 15% errors
    http_reqs: ['rate>300'],
  },
  ext: {
    loadimpact: {
      name: 'theCourseForum - STRESS Test (Find Breaking Point)',
      projectID: 3477348,
    },
  },
};

export default function () {
  // Mix of behaviors with emphasis on high-load scenarios
  if (Math.random() < 0.7) {
    enrollmentRushUser();
  } else {
    browseAndSearchUser();
  }
}
