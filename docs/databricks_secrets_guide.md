# 🔒 Security Guide: Configuring Databricks Secrets

## Overview

This guide explains how to securely configure AWS credentials in Databricks using **Secrets** instead of hardcoding.

---

## ⚠️ Why You Shouldn't Hardcode Credentials

**Risks of hardcoded credentials:**
- ❌ Exposure in Git commits.
- ❌ Leaks in GitHub history.
- ❌ Unauthorized access if the repository is leaked.
- ❌ Difficult credential rotation.
- ❌ Compliance violations (SOC 2, ISO 27001).

**Solution: Databricks Secrets**
- ✅ Encrypted credentials.
- ✅ Granular access control.
- ✅ Usage auditing.
- ✅ Easy rotation.
- ✅ No risk of accidental commits.

---

## 🔧 Step-by-Step Configuration

### 1️⃣ Install Databricks CLI

```bash
pip install databricks-cli
```

### 2️⃣ Configure Authentication

```bash
databricks configure --token
```

You will need to provide:
- **Databricks Host**: `https://your-workspace.cloud.databricks.com`
- **Token**: Generate in User Settings > Access Tokens.

### 3️⃣ Create a Secret Scope

```bash
databricks secrets create-scope --scope aws-credentials
```

**Scope Types:**
- `DATABRICKS` (default): Managed by Databricks.
- `AZURE_KEYVAULT`: Integrated with Azure Key Vault.

### 4️⃣ Add Secrets

```bash
# AWS Access Key
databricks secrets put --scope aws-credentials --key access-key

# AWS Secret Key
databricks secrets put --scope aws-credentials --key secret-key

# Session Token (if using temporary credentials)
databricks secrets put --scope aws-credentials --key session-token

# Bucket Name
databricks secrets put --scope aws-credentials --key bucket-name
```

**Notes:**
- Each command will open an editor for you to paste the secret value.
- Values are NOT displayed after being saved.
- Use `--string-value` for short values: `databricks secrets put --scope aws-credentials --key bucket-name --string-value "my-bucket"`

### 5️⃣ Verify Created Secrets

```bash
# List scopes
databricks secrets list-scopes

# List secrets in a scope
databricks secrets list --scope aws-credentials
```

**Expected Output:**
```
Key name         Last updated
---------------  --------------
access-key       2026-01-11
secret-key       2026-01-11
session-token    2026-01-11
bucket-name      2026-01-11
```

---

## 📝 Using Secrets in Notebooks

### Secure Python Code

```python
# 🔒 Fetch credentials from Databricks Secrets
access_key = dbutils.secrets.get(scope="aws-credentials", key="access-key")
secret_key = dbutils.secrets.get(scope="aws-credentials", key="secret-key")
session_token = dbutils.secrets.get(scope="aws-credentials", key="session-token")
bucket_name = dbutils.secrets.get(scope="aws-credentials", key="bucket-name")

# Configure Spark
spark.conf.set("fs.s3a.access.key", access_key)
spark.conf.set("fs.s3a.secret.key", secret_key)
spark.conf.set("fs.s3a.session.token", session_token)
spark.conf.set("fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.TemporaryAWSCredentialsProvider")

# Use dynamically in paths
path = f"s3a://{bucket_name}/cvm-transactions-daily/"
df = spark.read.csv(path)
```

### Secure Scala Code

```scala
val accessKey = dbutils.secrets.get(scope = "aws-credentials", key = "access-key")
val secretKey = dbutils.secrets.get(scope = "aws-credentials", key = "secret-key")

spark.conf.set("fs.s3a.access.key", accessKey)
spark.conf.set("fs.s3a.secret.key", secretKey)
```

---

## 🛡️ Best Practices

### 1. Access Control

Create separate scopes per environment:

```bash
databricks secrets create-scope --scope aws-credentials-dev
databricks secrets create-scope --scope aws-credentials-prod
```

### 2. Principle of Least Privilege

Grant access only to necessary users:

```bash
databricks secrets put-acl --scope aws-credentials --principal user@company.com --permission READ
```

**Permission Levels:**
- `MANAGE`: Can add/remove secrets and change permissions.
- `WRITE`: Can add secrets.
- `READ`: Can only read secrets.

### 3. Regular Rotation

Update credentials periodically:

```bash
# Delete old secret
databricks secrets delete --scope aws-credentials --key access-key

# Add new one
databricks secrets put --scope aws-credentials --key access-key
```

### 4. Auditing

Monitor secret usage via Databricks logs:
- Workspace Admin > Audit Logs.
- Filter by `secretsAccess`.

---

## 🚀 Alternative: IAM Roles (Recommended for Production)

Instead of Access Keys, use **IAM Roles** attached to the cluster.

### Advantages:
- ✅ No need to manage credentials.
- ✅ Automatic rotation.
- ✅ More secure.
- ✅ Auditing via AWS CloudTrail.

### Configuration:

1. **Create IAM Role with S3 permissions**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name/*",
        "arn:aws:s3:::your-bucket-name"
      ]
    }
  ]
}
```

2. **Attach Role to Cluster Instance Profile**
    - Databricks Admin Console.
    - Clusters > Edit > Advanced Options > AWS IAM Role.

3. **Configure Spark**:

```python
spark.conf.set("fs.s3a.aws.credentials.provider", 
               "com.amazonaws.auth.InstanceProfileCredentialsProvider")

# No more need for access_key/secret_key!
bucket_name = dbutils.secrets.get(scope="aws-credentials", key="bucket-name")
path = f"s3a://{bucket_name}/data/"
```

---

## 🔍 Troubleshooting

### Error: "SecretNotFoundException"

**Cause**: Secret does not exist.  
**Solution**:
```bash
databricks secrets list --scope aws-credentials
databricks secrets put --scope aws-credentials --key <missing-key>
```

### Error: "PermissionDenied"

**Cause**: User lacks permission on the scope.  
**Solution**:
```bash
databricks secrets put-acl --scope aws-credentials --principal <user> --permission READ
```

### Error: "Authentication failed"

**Cause**: Invalid or expired AWS credentials.  
**Solution**: Renew credentials and update secrets.

---

## 📚 References

- [Databricks Secrets - Official Docs](https://docs.databricks.com/security/secrets/index.html)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Databricks CLI Reference](https://docs.databricks.com/dev-tools/cli/index.html)
