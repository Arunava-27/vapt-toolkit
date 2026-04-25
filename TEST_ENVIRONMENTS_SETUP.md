# Test Environments Setup Guide

## Overview
This guide provides step-by-step instructions for setting up three vulnerable applications for manual testing of the VAPT toolkit.

---

## Quick Start

### Option 1: Docker Compose (Recommended)

Create `test-environments-compose.yml`:

```yaml
version: '3.8'

services:
  dvwa:
    image: vulnerables/web-dvwa
    ports:
      - "80:80"
      - "3306:3306"
    environment:
      MYSQL_PASS: "password"
    container_name: vapt-dvwa
    networks:
      - testing

  webgoat:
    image: webgoat/goatandwolf
    ports:
      - "8080:8080"
    container_name: vapt-webgoat
    networks:
      - testing

  juice-shop:
    image: bkimminich/juice-shop
    ports:
      - "3000:3000"
    container_name: vapt-juice-shop
    networks:
      - testing

networks:
  testing:
    driver: bridge
```

**Start all environments:**
```bash
docker-compose -f test-environments-compose.yml up -d
```

**Stop all environments:**
```bash
docker-compose -f test-environments-compose.yml down
```

**Check status:**
```bash
docker-compose -f test-environments-compose.yml ps
```

---

## Environment 1: DVWA

### Description
- **Name**: Damn Vulnerable Web Application
- **Purpose**: Classic web vulnerability testing platform
- **Language**: PHP + MySQL
- **Difficulty**: Beginner to Intermediate
- **Vulnerabilities**: 10+ common web vulnerabilities

### Access
- **URL**: http://localhost/DVWA/
- **Username**: admin
- **Password**: password
- **Database**: dvwa
- **DB User**: dvwa
- **DB Password**: p@ssw0rd

### Vulnerable Endpoints

#### 1. SQL Injection
- **Path**: `/vulnerabilities/sqli/`
- **Type**: GET parameter injection
- **Payload**: `' OR '1'='1' #`
- **Expected**: Database records displayed

#### 2. Command Injection
- **Path**: `/vulnerabilities/exec/`
- **Type**: Shell command execution
- **Payload**: `; ls -la /`
- **Expected**: Directory listing

#### 3. Cross-Site Scripting (XSS)
- **Reflected**: `/vulnerabilities/xss_r/`
- **Stored**: `/vulnerabilities/xss_s/`
- **DOM**: `/vulnerabilities/xss_d/`
- **Payload**: `<script>alert('XSS')</script>`

#### 4. CSRF
- **Path**: `/vulnerabilities/csrf/`
- **Function**: Allows unauthorized form submissions
- **Attack**: Cross-site request forgery forms

#### 5. File Upload
- **Path**: `/vulnerabilities/upload/`
- **Issue**: No file type validation
- **Attack**: Upload PHP shell

#### 6. File Inclusion
- **Local**: `/vulnerabilities/fi/?page=`
- **Remote**: `/vulnerabilities/rfi/?page=`
- **Payload**: `../../../etc/passwd`

#### 7. Insecure CAPTCHA
- **Path**: `/vulnerabilities/captcha/`
- **Issue**: CAPTCHA validation bypass

#### 8. Weak Session Management
- **Path**: Any authenticated page
- **Issue**: Predictable session tokens

#### 9. SQL Injection (Blind)
- **Path**: `/vulnerabilities/sqli_blind/`
- **Type**: Boolean-based or time-based
- **Payload**: `1' AND SLEEP(5) #`

#### 10. CSRF (Token Handling)
- **Path**: `/vulnerabilities/csrf/`
- **Test**: Token validation

### Configuration
After login, configure security level:
- **Low**: All vulnerabilities exposed
- **Medium**: Some protections
- **High**: Most protections

**For testing, use LOW level.**

### Reset Database
```bash
docker exec vapt-dvwa /bin/bash -c "mysql -u dvwa -pp@ssw0rd dvwa < /tmp/dvwa.sql"
```

---

## Environment 2: OWASP WebGoat

### Description
- **Name**: OWASP WebGoat
- **Purpose**: Security training and lessons
- **Language**: Java + Spring Boot
- **Difficulty**: Intermediate to Advanced
- **Lessons**: 20+ security topics

### Access
- **URL**: http://localhost:8080/WebGoat
- **Registration**: Create account or use default
- **Port**: 8080

### Available Lessons

#### A1: Broken Access Control
- Lesson: Understand access control
- Test: IDOR vulnerabilities
- Exercise: Manipulate user IDs

#### A2: Cryptographic Failures
- Lesson: Weak cryptography
- Test: Password storage
- Exercise: Crack weak encryption

#### A3: Injection
- Lesson: SQL injection, command injection
- Test: Various injection types
- Exercise: SQL injection practice

#### A4: Insecure Design
- Lesson: Design flaws
- Test: Logic vulnerabilities
- Exercise: Business logic bypass

#### A5: Security Misconfiguration
- Lesson: Configuration issues
- Test: Open endpoints
- Exercise: Information disclosure

#### A6: Vulnerable Components
- Lesson: Dependency vulnerabilities
- Test: Known CVEs
- Exercise: Component analysis

#### A7: Authentication
- Lesson: Broken authentication
- Test: Session issues
- Exercise: Password reset bypass

#### A8: Software Supply Chain
- Lesson: Third-party risks
- Test: Dependency tracking
- Exercise: Supply chain attacks

### Practice Exercises

1. **Navigate to Lesson**
2. **Read Instructions**
3. **Complete Exercise** (click "Complete Lesson")
4. **Verify Understanding** (answer questions)
5. **Proceed to Next Lesson**

### Key Testing Paths
```
http://localhost:8080/WebGoat/lessons
http://localhost:8080/WebGoat/api/lessons
http://localhost:8080/WebGoat/attack/lesson/
```

---

## Environment 3: OWASP Juice Shop

### Description
- **Name**: OWASP Juice Shop
- **Purpose**: Vulnerable web application for testing
- **Language**: Node.js + Express + Angular
- **Difficulty**: Beginner to Advanced
- **Vulnerabilities**: 30+ known vulnerabilities

### Access
- **URL**: http://localhost:3000
- **Port**: 3000
- **Default User**: demo@example.com / demo

### Built-in Vulnerabilities

#### 1. Authentication Bypass
- **Path**: `/rest/user/login`
- **Payload**: Inject username with quote: `admin'--`
- **Result**: Login without password

#### 2. SQL Injection
- **Path**: Product search
- **Payload**: `' OR '1'='1`
- **Result**: All products displayed

#### 3. Cross-Site Scripting (XSS)
- **Review Section**: Add review with `<script>alert('xss')</script>`
- **Admin Panel**: Search with XSS payload
- **Result**: Script execution

#### 4. CSRF
- **Update Profile**: Change user data
- **Issue**: No CSRF token validation
- **Attack**: Craft malicious form

#### 5. Insecure Direct Object Reference (IDOR)
- **User Data**: Access `/api/users/1`, `/api/users/2`
- **Orders**: Access `/api/orders/1`, `/api/orders/2`
- **Result**: Unauthorized data access

#### 6. Security Misconfiguration
- **API**: `/api/admin.php` or similar
- **Debug**: Enable debug mode
- **Info**: `/info`, `/api/version`

#### 7. Sensitive Data Exposure
- **Password**: Reset token in response
- **API Key**: Hardcoded in JavaScript
- **Payment**: Credit card validation bypass

#### 8. File Upload
- **Profile Picture**: Upload executable
- **Issue**: No file type validation
- **Result**: File execution possible

#### 9. Open Redirect
- **Login**: `?redirect=http://attacker.com`
- **Checkout**: Redirect to external URL
- **Result**: Phishing attacks possible

#### 10. Broken Access Control
- **Admin Panel**: Access with low privilege account
- **Pages**: Access restricted endpoints
- **Result**: Unauthorized access

### Known Vulnerabilities List
```
http://localhost:3000/score-board
```

Visit the Score Board to see all challenges and track completion.

### Default User Accounts
- **Admin**: admin@juice-sh.op / admin123
- **Demo**: demo@example.com / demo
- **Test**: test@example.com / test

### Password Reset Vulnerability
- **Path**: Password reset flow
- **Issue**: Predictable reset tokens
- **Attack**: Enumerate tokens

### API Endpoints
```
GET  /api/products
GET  /api/users
POST /api/users/login
GET  /api/baskets/{id}
POST /api/baskets/{id}/checkout
GET  /api/orders
```

---

## Network Configuration

### Local Network (Same Machine)
```
DVWA:      http://localhost (port 80)
WebGoat:   http://localhost:8080
Juice Shop: http://localhost:3000
```

### Remote Network (Different Machine)
Replace `localhost` with server IP:
```
DVWA:      http://192.168.1.100 (port 80)
WebGoat:   http://192.168.1.100:8080
Juice Shop: http://192.168.1.100:3000
```

### Docker Network
Environments can communicate:
```
DVWA:      http://dvwa (port 80)
WebGoat:   http://webgoat:8080
Juice Shop: http://juice-shop:3000
```

---

## Troubleshooting

### DVWA Won't Start
```bash
# Check logs
docker logs vapt-dvwa

# Rebuild
docker-compose down
docker-compose up -d --build

# Check MySQL
docker exec vapt-dvwa mysql -u dvwa -pp@ssw0rd dvwa -e "SELECT 1"
```

### WebGoat Port Already in Use
```bash
# Find process using port 8080
netstat -ano | findstr :8080

# Kill process (Windows)
taskkill /PID <PID> /F

# Or use different port
docker run -p 9090:8080 webgoat/goatandwolf
```

### Juice Shop Connection Refused
```bash
# Check if running
docker ps | grep juice-shop

# Check logs
docker logs vapt-juice-shop

# Restart
docker restart vapt-juice-shop
```

### Database Access Issues
```bash
# Reset DVWA DB
docker exec -it vapt-dvwa bash
mysql -u dvwa -pp@ssw0rd dvwa < /tmp/dvwa.sql

# Or reload container
docker rm vapt-dvwa
docker run -d --name vapt-dvwa ... (full command)
```

---

## Performance Considerations

### Resource Requirements
- **DVWA**: ~200MB
- **WebGoat**: ~500MB
- **Juice Shop**: ~300MB
- **Total**: ~1GB+ RAM recommended

### Optimization Tips
1. Run only needed environments
2. Stop when not testing
3. Use Docker networks (not port forwards)
4. Monitor CPU/Memory usage

### Monitoring
```bash
# Watch resources
docker stats

# Specific container
docker stats vapt-dvwa
```

---

## Security Notes

⚠️ **Warning**: These are intentionally vulnerable applications!

- **Never** deploy on production networks
- **Never** expose to internet
- Use only in isolated lab environments
- Reset after each test session
- Don't store sensitive data in these environments

---

## Cleanup

### Stop All Containers
```bash
docker-compose -f test-environments-compose.yml down
```

### Remove Containers
```bash
docker rm vapt-dvwa vapt-webgoat vapt-juice-shop
```

### Remove Images
```bash
docker rmi vulnerables/web-dvwa webgoat/goatandwolf bkimminich/juice-shop
```

### Full Cleanup
```bash
docker system prune -a
```

---

## Next Steps

1. ✅ Start all three environments
2. ✅ Verify each is accessible
3. ✅ Configure DVWA to LOW security level
4. ✅ Login to WebGoat and Juice Shop
5. ✅ Begin manual testing using MANUAL_TESTING_GUIDE.md

---

**Setup Guide Version**: 1.0
**Last Updated**: 2024-01-15
