# Pre-Commit Security Checklist

Use this checklist before committing code to GitHub.

## ✅ Quick Check

Run these commands before committing:

```bash
# 1. Check for .env files
git status | grep -E "\.env$|\.env\."

# 2. Check for hardcoded secrets
grep -r "password\s*=" . --exclude-dir=venv --exclude-dir=.git --exclude-dir=node_modules | grep -v ".example"
grep -r "api_key\s*=" . --exclude-dir=venv --exclude-dir=.git --exclude-dir=node_modules | grep -v ".example"
grep -r "secret\s*=" . --exclude-dir=venv --exclude-dir=.git --exclude-dir=node_modules | grep -v ".example"

# 3. Check for AWS credentials
grep -r "AKIA" . --exclude-dir=venv --exclude-dir=.git --exclude-dir=node_modules

# 4. Verify .gitignore is working
git status --ignored | grep -E "\.env|\.key|\.pem"
```

## 📋 Manual Checklist

- [ ] No `.env` files in staging area
- [ ] No hardcoded passwords or API keys
- [ ] No AWS credentials in code
- [ ] All secrets use environment variables
- [ ] `.env.example` updated (if needed)
- [ ] No database credentials in code
- [ ] No private keys (`.pem`, `.key`) committed
- [ ] Dockerfile doesn't contain secrets
- [ ] GitHub workflows use secrets (not hardcoded)
- [ ] README doesn't contain actual credentials

## 🚨 If You Find Secrets

1. **STOP** - Don't commit!
2. Move secrets to environment variables
3. Add to `.gitignore` if needed
4. Remove from Git history if already committed:
   ```bash
   git rm --cached .env
   git commit -m "Remove .env from tracking"
   ```

## 📝 Safe to Commit

- ✅ Code that reads from `os.environ.get()`
- ✅ `.env.example` (template file)
- ✅ Configuration files without secrets
- ✅ Documentation
- ✅ Tests

## 🔍 Automated Check Script

Save this as `check_secrets.sh`:

```bash
#!/bin/bash
echo "🔍 Checking for secrets..."

# Check for .env files
if git diff --cached --name-only | grep -E "\.env$|\.env\."; then
    echo "❌ ERROR: .env file detected in staging area!"
    exit 1
fi

# Check for common secret patterns
if git diff --cached | grep -E "(password|secret|api_key|aws_access)" | grep -v ".example" | grep -v "os.environ"; then
    echo "❌ WARNING: Potential secrets detected. Review before committing."
    exit 1
fi

echo "✅ No obvious secrets detected"
exit 0
```

Make it executable:
```bash
chmod +x check_secrets.sh
```

Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
./check_secrets.sh
```
