// k6 Load Testing Configuration
// Update BASE_URL with your CloudFront distribution domain or ALB DNS

export const config = {
  // Replace with your actual CloudFront domain from Terraform output
  // Run: terraform output cloudfront_domain
  BASE_URL: __ENV.BASE_URL || 'https://your-cloudfront-domain.cloudfront.net',
  
  // Test data - adjust these based on your actual data
  TEST_DATA: {
    departments: [1, 2, 3, 4, 5, 10, 15, 20], // Department IDs
    courses: [
      { mnemonic: 'CS', number: 1110 },
      { mnemonic: 'CS', number: 2150 },
      { mnemonic: 'MATH', number: 1320 },
      { mnemonic: 'ECON', number: 2010 },
    ],
    instructors: [1, 2, 3, 5, 10, 15, 20], // Instructor IDs
  },
  
  // Rate limiting and throttling
  THRESHOLDS: {
    http_req_duration: ['p(95)<2000', 'p(99)<5000'], // 95% under 2s, 99% under 5s
    http_req_failed: ['rate<0.05'], // Less than 5% errors
    http_reqs: ['rate>100'], // At least 100 requests per second
  },
};
