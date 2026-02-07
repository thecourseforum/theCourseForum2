# k6 Load Testing for theCourseForum

This directory contains k6 load testing scripts to test the performance and scalability of theCourseForum application deployed on AWS.

## 📋 Prerequisites

1. **Install k6**
   ```bash
   # macOS
   brew install k6
   
   # Linux
   sudo gpg -k
   sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
   echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
   sudo apt-get update
   sudo apt-get install k6
   
   # Windows
   choco install k6
   ```

2. **Get your CloudFront URL**
   ```bash
   cd iac/
   terraform output cloudfront_domain
   ```

3. **Update config.js**
   - Edit `k6/config.js` and set `BASE_URL` to your CloudFront domain
   - Update test data (department IDs, course mnemonics, etc.) based on your actual data

## 🧪 Test Scripts

### 1. **smoke-test.js** - Quick Validation (START HERE)
- **Purpose**: Verify everything works before full tests
- **Load**: 5 virtual users for 2 minutes
- **Use**: Before every major test session
```bash
k6 run k6/smoke-test.js
```

### 2. **regular-load.js** - Daily Usage Pattern
- **Purpose**: Simulate typical daily traffic (few hundred users)
- **Load**: Ramp up to 200 concurrent users over 35 minutes
- **Use**: Test normal operating conditions
```bash
k6 run k6/regular-load.js
```

### 3. **medium-load.js** - Moderate Peak (FEW THOUSAND USERS)
- **Purpose**: Simulate moderate peak usage (pre-enrollment activity)
- **Load**: Up to 3,000 concurrent users
- **Duration**: ~45 minutes
- **Use**: Test system under moderate stress
```bash
k6 run k6/medium-load.js
```

### 4. **peak-load.js** - Maximum Load (20K USERS)
- **Purpose**: Simulate enrollment hour peak with 20,000 users
- **Load**: Up to 20,000 concurrent users
- **Duration**: ~60 minutes
- **Use**: Test true peak capacity
- **⚠️ WARNING**: This generates significant load and AWS costs!
```bash
k6 run k6/peak-load.js
```

### 5. **stress-test.js** - Find Breaking Point
- **Purpose**: Push system beyond expected limits to find failure point
- **Load**: Up to 30,000 concurrent users
- **Use**: Determine maximum capacity
```bash
k6 run k6/stress-test.js
```

### 6. **spike-test.js** - Sudden Traffic Surge
- **Purpose**: Test resilience to sudden traffic spikes
- **Load**: Sudden jumps to 15k users in 30 seconds
- **Use**: Simulate enrollment opening moment
```bash
k6 run k6/spike-test.js
```

## 🎯 Recommended Testing Path

1. **First Time Setup**
   ```bash
   # 1. Update config.js with your CloudFront URL
   # 2. Run smoke test
   k6 run k6/smoke-test.js
   ```

2. **Start Small** (Few Thousand Users as requested)
   ```bash
   # Test with increasing load
   k6 run k6/regular-load.js
   k6 run k6/medium-load.js
   ```

3. **Build Up to Peak** (Eventually test 20K users)
   ```bash
   # Only run after validating medium load
   k6 run k6/peak-load.js
   ```

4. **Find Limits**
   ```bash
   k6 run k6/stress-test.js
   k6 run k6/spike-test.js
   ```

## 🔍 Monitoring During Tests

### CloudWatch Dashboards
Monitor your AWS resources during tests:
- ECS Task CPU/Memory utilization
- ALB request count and latency
- RDS connections and CPU
- CloudFront cache hit ratio

### Real-time k6 Output
k6 provides real-time metrics:
- `http_req_duration`: Response time
- `http_req_failed`: Error rate
- `http_reqs`: Requests per second
- `iterations`: Completed user sessions

### Key Metrics to Watch
```
✓ http_req_duration..........: avg=XXXms min=XXms med=XXms max=XXXms p(95)=XXXms
✓ http_req_failed............: XX.XX% 
✓ http_reqs..................: XXX/s
```

## ⚙️ Customization

### Environment Variables
Override config without editing files:
```bash
BASE_URL=https://your-domain.com k6 run k6/medium-load.js
```

### Adjust Test Data
Edit `k6/config.js`:
- Add actual department IDs from your database
- Add real course mnemonics and numbers
- Add valid instructor IDs

### Modify Scenarios
Edit `k6/scenarios.js` to:
- Add authentication (if needed)
- Test specific API endpoints
- Simulate logged-in user behavior

## 📊 Understanding Results

### Successful Test
```
✓ http_req_duration..........: p(95)=1500ms (below 2000ms threshold)
✓ http_req_failed............: 2.5% (below 5% threshold)
✓ http_reqs..................: 250/s (above 100/s threshold)
```

### Warning Signs
- `http_req_duration` p(95) > 2000ms: Slow responses
- `http_req_failed` > 5%: Too many errors
- `http_reqs` < 100/s: Not generating enough load

### Critical Issues
- `http_req_failed` > 10%: System is struggling
- `http_req_duration` p(95) > 5000ms: Severe performance degradation
- ECS tasks crashing or auto-scaling not working

## 💡 Tips & Best Practices

1. **Start Small**: Always run smoke test first
2. **Monitor Costs**: Peak load tests can be expensive - watch your AWS bill
3. **Incremental Load**: Don't jump straight to 20k users
4. **Off-Peak Testing**: Run major tests during low-traffic hours
5. **Auto-Scaling**: Ensure ECS auto-scaling is configured before large tests
6. **Database**: Monitor RDS connections - this is often the bottleneck
7. **Cache**: CloudFront caching significantly reduces load on origin

## 🚨 Troubleshooting

### High Error Rates
- Check ECS task health
- Verify database connections aren't maxed out
- Check ALB target group health

### Slow Response Times
- Check RDS CPU utilization
- Verify ECS tasks have enough CPU/memory
- Check if CloudFront caching is working

### Tests Won't Run
- Verify BASE_URL is correct
- Check network connectivity
- Ensure CloudFront distribution is deployed

## 📈 Next Steps After Testing

1. **Analyze Bottlenecks** from test results
2. **Optimize** database queries, caching, etc.
3. **Adjust** ECS auto-scaling thresholds
4. **Increase** RDS instance size if needed
5. **Re-test** with optimizations applied

## ⚠️ Important Notes

- **Costs**: Running 20k users test will incur AWS charges (ECS, ALB, data transfer)
- **Rate Limits**: Be aware of any API rate limits
- **Data**: Tests use read-only operations to avoid polluting your database
- **Authentication**: Current tests don't authenticate - add if testing protected routes
- **Realistic Data**: Update test data to match your actual course/dept IDs for accurate results

## 🔗 Resources

- [k6 Documentation](https://k6.io/docs/)
- [k6 Cloud for Advanced Analytics](https://k6.io/cloud/)
- [AWS CloudWatch](https://console.aws.amazon.com/cloudwatch/)
