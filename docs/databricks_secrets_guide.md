# 🔒 Guia de Segurança: Configurando Databricks Secrets

## Visão Geral

Este guia explica como configurar credenciais AWS de forma segura no Databricks usando **Secrets** ao invés de hardcoding.

---

## ⚠️ Por Que Não Hardcodar Credenciais?

**Riscos de credenciais hardcoded:**
- ❌ Exposição em commits Git
- ❌ Vazamento no histórico do GitHub
- ❌ Acesso indevido se repositório vazar
- ❌ Difícil rotação de credenciais
- ❌ Violação de compliance (SOC 2, ISO 27001)

**Solução: Databricks Secrets**
- ✅ Credenciais criptografadas
- ✅ Controle de acesso granular
- ✅ Auditoria de uso
- ✅ Fácil rotação
- ✅ Sem risco de commit acidental

---

## 🔧 Configuração Passo a Passo

### 1️⃣ Instalar Databricks CLI

```bash
pip install databricks-cli
```

### 2️⃣ Configurar Autenticação

```bash
databricks configure --token
```

Você precisará fornecer:
- **Databricks Host**: `https://seu-workspace.cloud.databricks.com`
- **Token**: Gere em User Settings > Access Tokens

### 3️⃣ Criar Escopo de Secrets

```bash
databricks secrets create-scope --scope aws-credentials
```

**Tipos de escopos:**
- `DATABRICKS` (padrão): Gerenciado pelo Databricks
- `AZURE_KEYVAULT`: Integrado com Azure Key Vault

### 4️⃣ Adicionar Secrets

```bash
# Access Key AWS
databricks secrets put --scope aws-credentials --key access-key

# Secret Key AWS
databricks secrets put --scope aws-credentials --key secret-key

# Session Token (se usar credenciais temporárias)
databricks secrets put --scope aws-credentials --key session-token

# Bucket Name
databricks secrets put --scope aws-credentials --key bucket-name
```

**Notas:**
- Cada comando abrirá um editor para você colar o valor secreto
- Os valores NÃO são exibidos após salvos
- Use `--string-value` para valores curtos: `databricks secrets put --scope aws-credentials --key bucket-name --string-value "my-bucket"`

### 5️⃣ Verificar Secrets Criados

```bash
# Listar escopos
databricks secrets list-scopes

# Listar secrets em um escopo
databricks secrets list --scope aws-credentials
```

**Output esperado:**
```
Key name         Last updated
---------------  --------------
access-key       2026-01-11
secret-key       2026-01-11
session-token    2026-01-11
bucket-name      2026-01-11
```

---

## 📝 Usando Secrets nos Notebooks

### Código Python Seguro

```python
# 🔒 Buscar credenciais do Databricks Secrets
access_key = dbutils.secrets.get(scope="aws-credentials", key="access-key")
secret_key = dbutils.secrets.get(scope="aws-credentials", key="secret-key")
session_token = dbutils.secrets.get(scope="aws-credentials", key="session-token")
bucket_name = dbutils.secrets.get(scope="aws-credentials", key="bucket-name")

# Configurar Spark
spark.conf.set("fs.s3a.access.key", access_key)
spark.conf.set("fs.s3a.secret.key", secret_key)
spark.conf.set("fs.s3a.session.token", session_token)
spark.conf.set("fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.TemporaryAWSCredentialsProvider")

# Usar dinamicamente nos paths
path = f"s3a://{bucket_name}/cvm-transactions-daily/"
df = spark.read.csv(path)
```

### Código Scala Seguro

```scala
val accessKey = dbutils.secrets.get(scope = "aws-credentials", key = "access-key")
val secretKey = dbutils.secrets.get(scope = "aws-credentials", key = "secret-key")

spark.conf.set("fs.s3a.access.key", accessKey)
spark.conf.set("fs.s3a.secret.key", secretKey)
```

---

## 🛡️ Boas Práticas

### 1. Controle de Acesso

Criar scopes separados por ambiente:

```bash
databricks secrets create-scope --scope aws-credentials-dev
databricks secrets create-scope --scope aws-credentials-prod
```

### 2. Princípio do Menor Privilégio

Conceda acesso apenas aos usuários necessários:

```bash
databricks secrets put-acl --scope aws-credentials --principal user@company.com --permission READ
```

**Níveis de permissão:**
- `MANAGE`: Pode adicionar/remover secrets
- `WRITE`: Pode adicionar secrets
- `READ`: Pode apenas ler secrets

### 3. Rotação Regular

Atualize credenciais periodicamente:

```bash
# Deletar secret antigo
databricks secrets delete --scope aws-credentials --key access-key

# Adicionar novo
databricks secrets put --scope aws-credentials --key access-key
```

### 4. Auditoria

Monitore uso de secrets via logs do Databricks:
- Workspace Admin > Audit Logs
- Filtrar por `secretsAccess`

---

## 🚀 Alternativa: IAM Roles (Recomendado para Produção)

Ao invés de Access Keys, use **IAM Roles** anexadas ao cluster:

### Vantagens:
- ✅ Sem necessidade de gerenciar credenciais
- ✅ Rotação automática
- ✅ Mais seguro
- ✅ Auditoria via AWS CloudTrail

### Configuração:

1. **Criar IAM Role com permissões S3**:

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

2. **Anexar Role ao Instance Profile do Cluster**
   - Databricks Admin Console
   - Clusters > Edit > Advanced Options > AWS IAM Role

3. **Configurar Spark**:

```python
spark.conf.set("fs.s3a.aws.credentials.provider", 
               "com.amazonaws.auth.InstanceProfileCredentialsProvider")

# Não precisa mais de access_key/secret_key!
bucket_name = dbutils.secrets.get(scope="aws-credentials", key="bucket-name")
path = f"s3a://{bucket_name}/data/"
```

---

## 🔍 Troubleshooting

### Erro: "SecretNotFoundException"

**Causa**: Secret não existe  
**Solução**:
```bash
databricks secrets list --scope aws-credentials
databricks secrets put --scope aws-credentials --key <missing-key>
```

### Erro: "PermissionDenied"

**Causa**: Usuário não tem permissão no scope  
**Solução**:
```bash
databricks secrets put-acl --scope aws-credentials --principal <user> --permission READ
```

### Erro: "Authentication failed"

**Causa**: Credenciais AWS inválidas ou expiradas  
**Solução**: Renovar credenciais e atualizar secrets

---

## 📚 Referências

- [Databricks Secrets - Official Docs](https://docs.databricks.com/security/secrets/index.html)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Databricks CLI Reference](https://docs.databricks.com/dev-tools/cli/index.html)
