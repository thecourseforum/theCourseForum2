// Regular Load Test - Few Hundred Users
// Simulates typical daily usage outside of enrollment periods

import { config } from './config.js';
import {
  browseAndSearchUser,
  reviewReaderUser,
  instructorComparisonUser,
  staticAssetLoad,
} from './scenarios.js';

export const options = {
  stages: [
    { duration: '2m', target: 50 },    // Ramp up to 50 users
    { duration: '5m', target: 100 },   // Ramp up to 100 users
    { duration: '10m', target: 100 },  // Stay at 100 users
    { duration: '5m', target: 200 },   // Increase to 200 users
    { duration: '10m', target: 200 },  // Stay at 200 users
    { duration: '3m', target: 0 },     // Ramp down
  ],
  thresholds: config.THRESHOLDS,
  ext: {
    loadimpact: {
      name: 'theCourseForum - Regular Load Test',
      projectID: 3477348,
    },
  },
};

export default function () {
  // Distribute user behaviors
  const rand = Math.random();
  
  if (rand < 0.4) {
    // 40% browse and search
    browseAndSearchUser();
  } else if (rand < 0.7) {
    // 30% review readers
    reviewReaderUser();
  } else if (rand < 0.9) {
    // 20% instructor comparison
    instructorComparisonUser();
  } else {
    // 10% static asset load
    staticAssetLoad();
  }
}
