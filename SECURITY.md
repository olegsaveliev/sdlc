# Security Guidelines

## 🔒 Security Best Practices

This document outlines security measures for the Calculator API project.

## ✅ Security Checklist

### Before Committing to GitHub

- [x] No hardcoded passwords, API keys, or secrets
- [x] All sensitive data in environment variables
- [x] `.env` file in `.gitignore`
- [x] `.env.example` provided (without real values)
- [x] No AWS credentials in code
- [x] No database credentials in code
- [x] No API keys in code
- [x] Dockerfile doesn't expose secrets
- [x] GitHub workflows use secrets (not hardcoded values)

## 🔐 Secrets Management

### Local Development

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your values in `.env` (never commit this file)

3. The application automatically loads from `.env`

### AWS Deployment

#### Option 1: ECS Task Definition Environment Variables
Set environment variables in your ECS Task Definition:
- Go to ECS → Task Definitions → Your Task → Container Definitions
- Add environment variables in the "Environment" section

#### Option 2: AWS Systems Manager Parameter Store
Store secrets in AWS Systems Manager Parameter Store:
```bash
aws ssm put-parameter \
  --name "/calculator-api/environment" \
  --value "Production" \
  --type "String"
```

#### Option 3: AWS Secrets Manager
For sensitive data, use AWS Secrets Manager:
```bash
aws secretsmanager create-secret \
  --name calculator-api/config \
  --secret-string '{"ENVIRONMENT":"Production","API_TITLE":"Calculator API"}'
```

### GitHub Actions / CI/CD

Use GitHub Secrets for sensitive values:
1. Go to Repository → Settings → Secrets and variables → Actions
2. Add secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`
   - `EC2_HOST` (if using EC2)
   - `EC2_SSH_KEY` (if using EC2)

Reference in workflows:
```yaml
- name: Configure AWS
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: ${{ secrets.AWS_REGION }}
```

## 🚫 What NOT to Commit

### Never Commit:
- `.env` files
- AWS credentials
- API keys
- Passwords
- Private keys (`.pem`, `.key` files)
- Database connection strings with passwords
- GitHub tokens
- Any file containing actual secrets

### Safe to Commit:
- `.env.example` (template without real values)
- Configuration files (without secrets)
- Code that reads from environment variables
- Documentation

## 🔍 Security Audit Commands

### Check for hardcoded secrets:
```bash
# Search for common secret patterns
grep -r "password\s*=" . --exclude-dir=venv --exclude-dir=.git
grep -r "api_key\s*=" . --exclude-dir=venv --exclude-dir=.git
grep -r "secret\s*=" . --exclude-dir=venv --exclude-dir=.git
```

### Check for AWS credentials:
```bash
grep -r "AKIA" . --exclude-dir=venv --exclude-dir=.git
grep -r "aws_access_key" . --exclude-dir=venv --exclude-dir=.git
```

### Verify .gitignore is working:
```bash
git status --ignored
```

## 🐳 Docker Security

### Current Security Measures:
- ✅ Non-root user in container
- ✅ No secrets in Dockerfile
- ✅ Environment variables for configuration
- ✅ Health checks enabled

### Best Practices:
1. Use Docker secrets for sensitive data in production
2. Scan images for vulnerabilities:
   ```bash
   docker scan calculator-api
   ```
3. Keep base images updated
4. Use minimal base images (slim variants)

## 🌐 AWS Security

### IAM Best Practices:
1. **Least Privilege**: Grant minimum required permissions
2. **Use IAM Roles**: Prefer roles over access keys when possible
3. **Rotate Credentials**: Regularly rotate access keys
4. **Monitor Access**: Enable CloudTrail logging

### ECS Security:
1. Use ECS Task Roles instead of hardcoded credentials
2. Enable encryption at rest and in transit
3. Use VPC for network isolation
4. Enable CloudWatch logging

### Example IAM Policy (minimal):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    }
  ]
}
```

## 📋 Pre-Deployment Checklist

Before deploying to AWS:

- [ ] All secrets moved to AWS Secrets Manager or Parameter Store
- [ ] IAM roles configured with least privilege
- [ ] Environment variables set in ECS Task Definition
- [ ] Security groups configured correctly
- [ ] VPC and networking configured
- [ ] CloudWatch logging enabled
- [ ] Health checks configured
- [ ] No secrets in Docker image
- [ ] Image scanned for vulnerabilities
- [ ] HTTPS/TLS configured (if using ALB)

## 🆘 If Secrets Are Exposed

If you accidentally commit secrets:

1. **Immediately rotate/revoke** the exposed credentials
2. **Remove from Git history**:
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   ```
3. **Force push** (coordinate with team first!)
4. **Notify team** if shared repository
5. **Review access logs** for any unauthorized access

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [AWS Security Best Practices](https://aws.amazon.com/security/security-resources/)
- [GitHub Security](https://docs.github.com/en/code-security)
- [Docker Security](https://docs.docker.com/engine/security/)

---

**Remember**: Security is an ongoing process. Regularly review and update your security practices.
