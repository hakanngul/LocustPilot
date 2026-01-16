# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability in Locust Web Manager, please report it to us responsibly. Please do not:

- Create a public issue
- Discuss the vulnerability in public forums
- Exploit the vulnerability

Instead, please:

1. Send an email to: security@example.com (replace with actual contact)
2. Include details about:
   - The vulnerability description
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes

## Response Timeline

We will:

- Acknowledge receipt of your report within 48 hours
- Provide a detailed response within 7 days
- Fix the vulnerability within a reasonable timeframe based on severity
- Publicly disclose the vulnerability after it's fixed

## Severity Levels

- **Critical**: System compromise, data theft, etc.
- **High**: Significant impact on integrity or availability
- **Medium**: Limited impact, mitigating factors
- **Low**: Minor impact, difficult to exploit

## Supported Versions

Only the latest version of Locust Web Manager is actively supported for security updates.

## Security Best Practices

When deploying Locust Web Manager:

1. **Change default password**: Set `APP_PASSWORD` environment variable
2. **Use HTTPS**: Configure TLS/SSL for all connections
3. **Limit access**: Use network policies and firewall rules
4. **Secure ReportPortal**: Use API tokens with limited permissions
5. **Keep updated**: Always use the latest version
6. **Audit logs**: Regularly review access and execution logs

## Data Protection

- Test results are stored locally in `runs/` directory
- ReportPortal credentials are stored in environment variables
- No personal data is collected by the application
- Ensure proper backup of test results and configuration

## Environment Variables Security

Never commit `.env` file to version control. Always use `.env.example` as a template.

Sensitive variables:
- `APP_PASSWORD` - UI authentication password
- `RP_TOKEN` - ReportPortal API token
- `RP_ENDPOINT` - ReportPortal endpoint URL

## Third-Party Dependencies

We regularly update dependencies to address security vulnerabilities. Review:
- [Locust](https://github.com/locustio/locust/security)
- [Streamlit](https://github.com/streamlit/streamlit/security)
- [ReportPortal Client](https://github.com/reportportal/client-Python/security)
