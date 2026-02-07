// Medium Load Test - Few Thousand Users
// Simulates moderate peak usage (e.g., week before enrollment)

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
    { duration: '3m', target: 500 },    // Ramp up to 500 users
    { duration: '5m', target: 1500 },   // Ramp up to 1500 users
    { duration: '10m', target: 1500 },  // Stay at 1500 users
    { duration: '5m', target: 3000 },   // Increase to 3000 users
    { duration: '15m', target: 3000 },  // Stay at 3000 users
    { duration: '5m', target: 1000 },   // Ramp down
    { duration: '2m', target: 0 },      // Complete ramp down
  ],
  thresholds: config.THRESHOLDS,
  ext: {
    loadimpact: {
      name: 'theCourseForum - Medium Load Test',
      projectID: 3477348,
    },
  },
};

export default function () {
  // Distribute user behaviors
  const rand = Math.random();
  
  if (rand < 0.3) {
    // 30% browse and search
    browseAndSearchUser();
  } else if (rand < 0.55) {
    // 25% review readers
    reviewReaderUser();
  } else if (rand < 0.8) {
    // 25% enrollment rush (planning ahead)
    enrollmentRushUser();
  } else if (rand < 0.95) {
    // 15% instructor comparison
    instructorComparisonUser();
  } else {
    // 5% static asset load
    staticAssetLoad();
  }
}
