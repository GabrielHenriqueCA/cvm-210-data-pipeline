# 🔧 Como Usar Variáveis de Ambiente no Projeto

Este guia explica como configurar e usar variáveis de ambiente de forma segura.

---

## 📋 Setup Inicial (Uma Vez)

### 1️⃣ Copiar o Template

```bash
# No diretório raiz do projeto
cp .env.example .env
```

### 2️⃣ Preencher com Suas Credenciais

Edite o arquivo `.env` e substitua os valores:

```bash
# .env (seu arquivo privado)
AWS_ACCESS_KEY_ID=sua_access_key_aqui
AWS_SECRET_ACCESS_KEY=sua_secret_key_aqui
S3_BUCKET_NAME=seu-bucket-s3
# ... etc
```

⚠️ **IMPORTANTE**: O arquivo `.env` já está no `.gitignore` e NÃO será commitado!

---

## 🐍 Uso em Python (Scripts Locais)

### Instalação

```bash
pip install python-dotenv
```

### Código de Exemplo

```python
# local_script.py
import os
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

# Usar as variáveis
aws_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
bucket_name = os.getenv('S3_BUCKET_NAME')

print(f"Usando bucket: {bucket_name}")
```

---

## ☁️ Uso em AWS Lambda

### Configuração

**NÃO** use arquivo `.env` na Lambda. Configure via **AWS Console**:

1. AWS Lambda Console → Sua função
2. Configuration → Environment variables
3. Adicionar variáveis:
   - `S3_BUCKET` = `seu-bucket-name`
   - `S3_PREFIX` = `cvm-transactions-daily`

### Código Lambda

```python
# lambda_function.py
import os

# Lambda automaticamente carrega variáveis de ambiente
S3_BUCKET = os.environ.get('S3_BUCKET')
if not S3_BUCKET:
    raise ValueError("S3_BUCKET environment variable is required!")

# Use normalmente
print(f"Usando bucket: {S3_BUCKET}")
```

---

## 📊 Uso em Databricks

### ⚠️ NÃO use .env no Databricks!

Use **Databricks Secrets** ao invés disso.

### Setup Databricks Secrets

```bash
# Criar scope
databricks secrets create-scope --scope aws-credentials

# Adicionar secrets
databricks secrets put --scope aws-credentials --key access-key
databricks secrets put --scope aws-credentials --key bucket-name
```

### Código Notebook

```python
# No Databricks Notebook
access_key = dbutils.secrets.get(scope="aws-credentials", key="access-key")
bucket_name = dbutils.secrets.get(scope="aws-credentials", key="bucket-name")

# Configurar Spark
spark.conf.set("fs.s3a.access.key", access_key)
```

---

## 🔍 Verificação

### Verificar se .env está sendo ignorado

```bash
git status

# .env NÃO deve aparecer na lista
# Se aparecer, verifique seu .gitignore
```

### Verificar se variáveis carregaram

```python
from dotenv import load_dotenv
import os

load_dotenv()
print(os.getenv('S3_BUCKET_NAME'))  # Deve mostrar seu bucket
```

---

## 🛡️ Checklist de Segurança

- [ ] `.env.example` tem apenas placeholders (sem credenciais reais)
- [ ] `.env` está no `.gitignore`
- [ ] `.env` não aparece no `git status`
- [ ] Credenciais reais apenas no `.env` local (nunca commit)
- [ ] Lambda usa variáveis de ambiente via Console
- [ ] Databricks usa Secrets (não .env)

---

## 📁 Estrutura Recomendada

```
projeto/
├── .env.example          # ✅ Template (commitado no Git)
├── .env                  # ❌ Privado (NÃO commitado)
├── .gitignore            # ✅ Contém ".env"
└── seu_script.py         # ✅ Usa load_dotenv()
```

---

## 🚨 Se Você Commitou .env Por Engano

### Remover do histórico Git

```bash
# Remover arquivo
git rm --cached .env

# Commit a remoção
git commit -m "Remove .env file"

# Limpar histórico (se já deu push)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (CUIDADO!)
git push origin --force --all
```

### Revogar Credenciais

Se credenciais foram expostas, **revogue imediatamente**:

1. AWS IAM Console → Users → Security Credentials
2. Delete Access Key
3. Gere novas credenciais
4. Atualize seu `.env` local

---

## 📚 Referências

- [python-dotenv Documentation](https://github.com/theskumar/python-dotenv)
- [AWS Lambda Environment Variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)
- [Databricks Secrets Guide](docs/databricks_secrets_guide.md)
