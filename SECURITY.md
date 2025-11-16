# Security Policy

## Supported Versions

We release patches for security vulnerabilities. The following versions are currently being supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them to the security team by sending an email to the project maintainers. Include the following details:

1. **Type of vulnerability** (e.g., XSS, SQL Injection, etc.)
2. **Location** of the vulnerability in the code (file and line number if possible)
3. **Description** of how the vulnerability could be exploited
4. **Proof of concept** (if available)
5. **Impact** of the vulnerability (severity level)
6. **Suggested fix** (if you have one)

Please allow adequate time for the team to address the issue before public disclosure. We generally aim to:

* Acknowledge receipt of your report within 5 business days
* Provide an estimated timeline for a fix within 10 business days
* Release a patched version as soon as possible

## Security Best Practices

When using PDF Form Filler, please follow these security best practices:

### Input Validation

* Always validate and sanitize user inputs before processing
* Use secure file upload mechanisms with proper file type validation
* Implement rate limiting on upload endpoints
* Set reasonable file size limits

### PDF Handling

* Verify PDF files come from trusted sources
* Be cautious with encrypted PDFs from unknown sources
* Consider scanning uploaded files with antivirus software
* Don't process PDFs from untrusted users in production without additional safeguards

### Database Security

* Use strong database passwords
* Enable database encryption if handling sensitive data
* Restrict database access to necessary services only
* Regularly backup the database
* Use environment variables for database credentials (never hardcode)

### Web Application Security

* Enable CSRF protection (already implemented via Flask-WTF)
* Use HTTPS in production
* Set secure headers (Content-Security-Policy, X-Frame-Options, etc.)
* Implement proper authentication and authorization
* Keep all dependencies up to date
* Use environment variables for sensitive configuration

### Environment Variables

Store the following securely:

```
SESSION_SECRET=your-secure-random-secret-key
LOG_LEVEL=INFO  # Set to DEBUG only in development
```

Never commit these values to version control.

## Dependency Security

We regularly update dependencies to patch known vulnerabilities. To check for vulnerable dependencies:

```bash
pip install safety
safety check
```

## Code Review

All code changes go through review to catch potential security issues. Please ensure your contributions:

1. Follow secure coding practices
2. Include proper error handling
3. Don't introduce new vulnerabilities
4. Are tested for security implications

## Security Improvements

If you have suggestions for improving security (without disclosing vulnerabilities), please:

1. Open an issue labeled as "security"
2. Describe the improvement and its benefits
3. Provide examples if possible

## Compliance

This project aims to follow OWASP Top 10 security best practices and uses industry-standard libraries for PDF handling and encryption.

## Contact

For security-related inquiries, please reach out to the project maintainers through:

* Email: [maintainer-email]
* Security Advisory: GitHub Security Advisory

## Acknowledgments

We appreciate the security research community and thank those who report vulnerabilities responsibly.
