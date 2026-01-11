# 🚀 Guia de Publicação no GitHub - CVM 210 Project

## ✅ Passo 1: Adicionar Arquivos ao Git

```bash
# Adicionar todos os arquivos ao staging
git add .

# Verificar o que será commitado
git status
```

**Importante**: Verifique se `.env` ou `.env.example` com credenciais NÃO aparecem!

---

## ✅ Passo 2: Fazer o Primeiro Commit

```bash
git commit -m "feat: Initial commit - CVM 210 Data Pipeline

- Implementação completa de pipeline de dados CVM 210
- Arquitetura Medallion (Bronze, Silver, Gold) no Databricks
- Ingestão automatizada via AWS Lambda
- Documentação técnica completa e profissional
- Otimização de custos e performance
- Guias de troubleshooting e segurança"
```

---

## ✅ Passo 3: Criar Repositório no GitHub

### Opção A: Via GitHub Web

1. Acesse: https://github.com/new
2. **Repository name**: `cvm210-data-pipeline`
3. **Description**: `Production-ready data engineering solution for CVM 210 regulatory data using AWS + Databricks`
4. **Public** ou **Private**: Escolha conforme preferência
5. ⚠️ **NÃO** marque "Initialize with README" (você já tem!)
6. Clique em **Create repository**

### Opção B: Via GitHub CLI

```bash
# Se tiver GitHub CLI instalado
gh repo create cvm210-data-pipeline --public --source=. --remote=origin
```

---

## ✅ Passo 4: Conectar ao Repositório Remoto

Após criar o repo no GitHub, copie a URL e execute:

```bash
# Adicionar origem remota (substitua YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/cvm210-data-pipeline.git

# Ou com SSH (se configurado)
git remote add origin git@github.com:YOUR_USERNAME/cvm210-data-pipeline.git
```

---

## ✅ Passo 5: Renomear Branch para 'main'

```bash
# GitHub usa 'main' como padrão agora
git branch -M main
```

---

## ✅ Passo 6: Fazer o Push

```bash
# Push inicial
git push -u origin main
```

**Se pedir autenticação**:
- Username: seu username do GitHub
- Password: use um **Personal Access Token** (não a senha!)
  - Gere em: https://github.com/settings/tokens

---

## 🔒 CHECKLIST DE SEGURANÇA (ANTES DO PUSH!)

### ⚠️ IMPORTANTE: Verificações Obrigatórias

```bash
# 1. Verificar se .env está ignorado
git status | grep ".env"
# ❌ Se aparecer ".env" na lista = PARE! remova-o

# 2. Verificar se .gitignore está funcionando
cat .gitignore | grep ".env"
# ✅ Deve mostrar ".env" na lista

# 3. Verificar se há credenciais hardcoded
git grep -i "ASIAW3MEFFE7"
# ❌ Se encontrar = REMOVA antes de continuar!
```

### Arquivos que NÃO devem ser commitados:
- ❌ `.env` (com credenciais reais)
- ❌ Notebooks com outputs executados (contêm dados sensíveis)
- ❌ `__pycache__/`
- ❌ Credenciais AWS hardcoded

---

## 📋 Após o Push (GitHub)

### 1. Adicionar Informações no Repositório

- **About**: Adicione descrição e tags
  - Tags sugeridas: `aws`, `databricks`, `data-engineering`, `pyspark`, `delta-lake`

### 2. Configurar GitHub Pages (Opcional)

Se quiser hospedar a documentação:
- Settings > Pages > Source: `main branch` / `docs folder`

### 3. Adicionar Topics/Tags

```
aws, databricks, data-engineering, etl, medallion-architecture,
pyspark, delta-lake, data-pipeline, cvm, python
```

---

## 🔄 Comandos Úteis Futuros

### Fazer novos commits

```bash
# Ver mudanças
git status

# Adicionar arquivos específicos
git add README.md lambda_function.py

# Ou adicionar tudo
git add .

# Commit
git commit -m "tipo: descrição breve

Detalhes opcionais"

# Push
git push
```

### Tipos de commit (convenção)

- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Mudanças na documentação
- `refactor:` - Refatoração de código
- `perf:` - Melhorias de performance
- `test:` - Adição/correção de testes
- `chore:` - Tarefas de manutenção

---

## 📊 Exemplo de Workflow Completo

```bash
# 1. Adicionar arquivos
git add .

# 2. Verificar status
git status

# 3. Commit
git commit -m "feat: Add cost optimization documentation"

# 4. Push
git push

# 5. Verificar no GitHub
# Acesse: https://github.com/YOUR_USERNAME/cvm210-data-pipeline
```

---

## 🆘 Troubleshooting

### Erro: "remote origin already exists"

```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/cvm210-data-pipeline.git
```

### Erro: "Authentication failed"

Use **Personal Access Token** ao invés de senha:
1. GitHub > Settings > Developer settings > Personal access tokens
2. Generate new token (classic)
3. Selecione `repo` permissions
4. Use o token como senha

### Erro: "Updates were rejected"

```bash
# Forçar push (cuidado! somente se tiver certeza)
git push -f origin main
```

### Limpar cache do Git (se commitou arquivo sensível)

```bash
git rm --cached .env
git commit -m "chore: Remove .env from tracking"
git push
```

---

## 🎯 Próximos Passos Após Publicação

1. ⭐ Adicionar **README badges** (build status, etc)
2. 📝 Criar **GitHub Releases** para versões
3. 🔒 Configurar **Dependabot** para segurança
4. 📊 Habilitar **GitHub Actions** (CI/CD futuro)
5. 💬 Compartilhar no LinkedIn com o link do repo!

---

## 📺 Comando Resumido (Copy & Paste)

```bash
# Setup completo
git add .
git commit -m "feat: Initial commit - CVM 210 Data Pipeline"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/cvm210-data-pipeline.git
git push -u origin main
```

**Substitua `YOUR_USERNAME` pelo seu username do GitHub!**

---

Boa sorte com a publicação! 🚀
