# 🔧 How to Use Environment Variables in the Project

This guide explains how to configure and use environment variables securely.

---

## 📋 Initial Setup (One-Time)

### 1️⃣ Copy the Template

```bash
# In the project root directory
cp .env.example .env
```

### 2️⃣ Fill with Your Credentials

Edit the `.env` file and replace the values:

```bash
# .env (your private file)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
S3_BUCKET_NAME=your-s3-bucket
# ... etc
```

> [!WARNING]
> **IMPORTANT**: The `.env` file is already in `.gitignore` and WILL NOT be committed!

---

## 🐍 Python Usage (Local Scripts)

### Installation

```bash
pip install python-dotenv
```

### Example Code

```python
# local_script.py
import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Use the variables
aws_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
bucket_name = os.getenv('S3_BUCKET_NAME')

print(f"Using bucket: {bucket_name}")
```

---

## ☁️ AWS Lambda Usage

### Configuration

**DO NOT** use a `.env` file in Lambda. Configure via **AWS Console**:

1. AWS Lambda Console → Your function.
2. Configuration → Environment variables.
3. Add variables:
   - `S3_BUCKET` = `your-bucket-name`
   - `S3_PREFIX` = `cvm-transactions-daily`

### Lambda Code

```python
# lambda_function.py
import os

# Lambda automatically loads environment variables
S3_BUCKET = os.environ.get('S3_BUCKET')
if not S3_BUCKET:
    raise ValueError("S3_BUCKET environment variable is required!")

# Use normally
print(f"Using bucket: {S3_BUCKET}")
```

---

## 📊 Databricks Usage

### ⚠️ DO NOT use .env in Databricks!

Use **Databricks Secrets** instead.

### Databricks Secrets Setup

```bash
# Create scope
databricks secrets create-scope --scope aws-credentials

# Add secrets
databricks secrets put --scope aws-credentials --key access-key
databricks secrets put --scope aws-credentials --key bucket-name
```

### Notebook Code

```python
# In a Databricks Notebook
access_key = dbutils.secrets.get(scope="aws-credentials", key="access-key")
bucket_name = dbutils.secrets.get(scope="aws-credentials", key="bucket-name")

# Configure Spark
spark.conf.set("fs.s3a.access.key", access_key)
```

---

## 🔍 Verification

### Check if .env is being ignored

```bash
git status

# .env SHOULD NOT appear in the list
# If it does, check your .gitignore
```

### Check if variables are loaded

```python
from dotenv import load_dotenv
import os

load_dotenv()
print(os.getenv('S3_BUCKET_NAME'))  # Should show your bucket name
```

---

## 🛡️ Security Checklist

- [ ] `.env.example` has only placeholders (no real credentials).
- [ ] `.env` is in `.gitignore`.
- [ ] `.env` does not appear in `git status`.
- [ ] Real credentials only in the local `.env` (never commit).
- [ ] Lambda uses environment variables via Console.
- [ ] Databricks uses Secrets (not .env).

---

## 📁 Recommended Structure

```
project/
├── .env.example          # ✅ Template (committed to Git)
├── .env                  # ❌ Private (NOT committed)
├── .gitignore            # ✅ Contains ".env"
└── your_script.py        # ✅ Uses load_dotenv()
```

---

## 🚨 If You Committed .env by Mistake

### Remove from Git history

```bash
# Remove file from cache
git rm --cached .env

# Commit the removal
git commit -m "Remove .env file"

# Clean history (if you already pushed)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (CAUTION!)
git push origin --force --all
```

### Revoke Credentials

If credentials were exposed, **revoke them immediately**:

1. AWS IAM Console → Users → Security Credentials.
2. Delete Access Key.
3. Generate new credentials.
4. Update your local `.env`.

---

## 📚 References

- [python-dotenv Documentation](https://github.com/theskumar/python-dotenv)
- [AWS Lambda Environment Variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)
- [Databricks Secrets Guide](docs/databricks_secrets_guide.md)
