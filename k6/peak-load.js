// Peak Load Test - 20K Users (Enrollment Hour)
// Simulates maximum stress during course enrollment period
// WARNING: This will generate significant load - ensure your AWS account can handle it

import { config } from './config.js';
import {
  browseAndSearchUser,
  reviewReaderUser,
  enrollmentRushUser,
  instructorComparisonUser,
  staticAssetLoad,
} from './scenarios.js';

export const options = {
  stages: [
    { duration: '5m', target: 2000 },    // Quick ramp to 2k
    { duration: '5m', target: 5000 },    // Ramp to 5k
    { duration: '5m', target: 10000 },   // Ramp to 10k
    { duration: '5m', target: 15000 },   // Ramp to 15k
    { duration: '5m', target: 20000 },   // Peak at 20k users
    { duration: '20m', target: 20000 },  // Sustain peak load
    { duration: '5m', target: 10000 },   // Start ramp down
    { duration: '5m', target: 2000 },    // Continue ramp down
    { duration: '3m', target: 0 },       // Complete ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<3000', 'p(99)<8000'], // More lenient during peak
    http_req_failed: ['rate<0.10'], // Allow up to 10% errors during extreme load
    http_reqs: ['rate>500'], // Expect at least 500 requests per second
  },
  ext: {
    loadimpact: {
      name: 'theCourseForum - PEAK LOAD Test (20K Users)',
      projectID: 3477348,
    },
  },
};

export default function () {
  // During enrollment, most users are in rush mode
  const rand = Math.random();
  
  if (rand < 0.6) {
    // 60% enrollment rush users (primary behavior)
    enrollmentRushUser();
  } else if (rand < 0.8) {
    // 20% quick browse and search
    browseAndSearchUser();
  } else if (rand < 0.9) {
    // 10% review readers
    reviewReaderUser();
  } else if (rand < 0.97) {
    // 7% instructor comparison
    instructorComparisonUser();
  } else {
    // 3% static asset load
    staticAssetLoad();
  }
}
