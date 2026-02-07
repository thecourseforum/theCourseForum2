// Smoke Test - Quick Validation
// Fast test with minimal load to verify everything works before full load tests

import { config } from './config.js';
import {
  browseAndSearchUser,
  reviewReaderUser,
  enrollmentRushUser,
} from './scenarios.js';

export const options = {
  vus: 5, // 5 virtual users
  duration: '2m', // 2 minutes
  thresholds: {
    http_req_duration: ['p(95)<1500'],
    http_req_failed: ['rate<0.01'], // Less than 1% errors
  },
};

export default function () {
  // Test each main scenario once
  const rand = Math.random();
  
  if (rand < 0.33) {
    browseAndSearchUser();
  } else if (rand < 0.67) {
    reviewReaderUser();
  } else {
    enrollmentRushUser();
  }
}
