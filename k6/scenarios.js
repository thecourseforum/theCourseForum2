// k6 Load Testing Scenarios
// Different user behavior patterns for realistic load testing

import { sleep } from 'k6';
import http from 'k6/http';
import { check } from 'k6';
import { config } from './config.js';

const BASE_URL = config.BASE_URL;
const TEST_DATA = config.TEST_DATA;

// Realistic think time between actions (in seconds)
function thinkTime(min = 1, max = 5) {
  sleep(min + Math.random() * (max - min));
}

// Random selection helper
function randomChoice(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

/**
 * Scenario 1: Browse and Search User
 * User browses courses, searches, and views details
 */
export function browseAndSearchUser() {
  const responses = {};
  
  // 1. Visit homepage
  responses.home = http.get(`${BASE_URL}/`);
  check(responses.home, {
    'homepage loaded': (r) => r.status === 200,
  });
  thinkTime(2, 4);
  
  // 2. Browse courses
  responses.browse = http.get(`${BASE_URL}/browse/`);
  check(responses.browse, {
    'browse page loaded': (r) => r.status === 200,
  });
  thinkTime(3, 6);
  
  // 3. Search for a course
  const searchQuery = randomChoice(['CS', 'MATH', 'ECON', 'APMA', 'PSYC']);
  responses.search = http.get(`${BASE_URL}/search/?q=${searchQuery}`);
  check(responses.search, {
    'search completed': (r) => r.status === 200,
  });
  thinkTime(2, 5);
  
  // 4. View a department
  const dept = randomChoice(TEST_DATA.departments);
  responses.dept = http.get(`${BASE_URL}/department/${dept}/`);
  check(responses.dept, {
    'department page loaded': (r) => r.status === 200,
  });
  thinkTime(2, 4);
  
  // 5. View a course
  const course = randomChoice(TEST_DATA.courses);
  responses.course = http.get(`${BASE_URL}/course/${course.mnemonic}/${course.number}/`);
  check(responses.course, {
    'course page loaded': (r) => r.status === 200,
  });
  thinkTime(3, 7);
  
  return responses;
}

/**
 * Scenario 2: Review Reader
 * User specifically looks for course reviews
 */
export function reviewReaderUser() {
  const responses = {};
  
  // 1. Direct to course page (e.g., from bookmark or Google)
  const course = randomChoice(TEST_DATA.courses);
  responses.course = http.get(`${BASE_URL}/course/${course.mnemonic}/${course.number}/`);
  check(responses.course, {
    'course page loaded': (r) => r.status === 200,
  });
  thinkTime(5, 10); // Reading reviews takes time
  
  // 2. View course with specific instructor
  const instructor = randomChoice(TEST_DATA.instructors);
  responses.instructor = http.get(`${BASE_URL}/course/${course.mnemonic}/${course.number}/${instructor}/`);
  check(responses.instructor, {
    'course-instructor page loaded': (r) => r.status === 200 || r.status === 404,
  });
  thinkTime(4, 8);
  
  // 3. Check reviews page
  responses.reviews = http.get(`${BASE_URL}/reviews/`);
  check(responses.reviews, {
    'reviews page loaded': (r) => r.status === 200,
  });
  thinkTime(2, 5);
  
  return responses;
}

/**
 * Scenario 3: Enrollment Rush User (Critical Path)
 * User quickly checks courses and builds schedule during enrollment
 */
export function enrollmentRushUser() {
  const responses = {};
  
  // 1. Quick homepage check
  responses.home = http.get(`${BASE_URL}/`);
  check(responses.home, {
    'homepage loaded': (r) => r.status === 200,
  });
  thinkTime(0.5, 1); // Very quick during enrollment rush
  
  // 2. Search for specific course
  const searchQuery = randomChoice(['CS 1110', 'CS 2150', 'MATH 1320', 'ECON 2010']);
  responses.search = http.get(`${BASE_URL}/search/?q=${encodeURIComponent(searchQuery)}`);
  check(responses.search, {
    'search completed': (r) => r.status === 200,
  });
  thinkTime(0.5, 1);
  
  // 3. Rapid course checking (3-5 courses)
  const numCourses = 3 + Math.floor(Math.random() * 3);
  for (let i = 0; i < numCourses; i++) {
    const course = randomChoice(TEST_DATA.courses);
    const resp = http.get(`${BASE_URL}/course/${course.mnemonic}/${course.number}/`);
    check(resp, {
      [`course ${i + 1} loaded`]: (r) => r.status === 200,
    });
    thinkTime(0.3, 1); // Very short think time during enrollment
  }
  
  // 4. Check schedule page (most critical during enrollment)
  responses.schedule = http.get(`${BASE_URL}/schedule/`);
  check(responses.schedule, {
    'schedule page loaded': (r) => r.status === 200 || r.status === 302, // May redirect to login
  });
  thinkTime(1, 2);
  
  return responses;
}

/**
 * Scenario 4: Instructor Comparison
 * User compares instructors for the same course
 */
export function instructorComparisonUser() {
  const responses = {};
  const course = randomChoice(TEST_DATA.courses);
  
  // 1. Visit course page
  responses.course = http.get(`${BASE_URL}/course/${course.mnemonic}/${course.number}/`);
  check(responses.course, {
    'course page loaded': (r) => r.status === 200,
  });
  thinkTime(3, 5);
  
  // 2. Check multiple instructors
  for (let i = 0; i < 3; i++) {
    const instructor = randomChoice(TEST_DATA.instructors);
    const resp = http.get(`${BASE_URL}/instructor/${instructor}/`);
    check(resp, {
      [`instructor ${i + 1} loaded`]: (r) => r.status === 200 || r.status === 404,
    });
    thinkTime(2, 4);
  }
  
  return responses;
}

/**
 * Scenario 5: Static Asset Load
 * Simulates loading of CSS, JS, images
 */
export function staticAssetLoad() {
  const responses = {};
  
  // Homepage with all its assets
  responses.home = http.get(`${BASE_URL}/`);
  
  // Common static assets (CloudFront should cache these)
  const staticAssets = [
    '/static/base/base.css',
    '/static/base/navbar.css',
    '/static/landing/landing.css',
    '/static/common/form.js',
  ];
  
  staticAssets.forEach(asset => {
    http.get(`${BASE_URL}${asset}`);
  });
  
  return responses;
}
