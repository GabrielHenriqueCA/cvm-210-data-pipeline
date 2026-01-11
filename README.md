# CVM 210 Data Pipeline

![Project Banner](assets/images/project_banner.png)

[![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20S3-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![Databricks](https://img.shields.io/badge/Databricks-Delta%20Lake-FF3621?style=for-the-badge&logo=databricks&logoColor=white)](https://databricks.com/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PySpark](https://img.shields.io/badge/PySpark-E25A1C?style=for-the-badge&logo=apache-spark&logoColor=white)](https://spark.apache.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black?style=for-the-badge)](https://github.com/psf/black)

## 📑 Índice

- [Visão Geral](#-visão-geral)
- [Objetivos do Projeto](#-objetivos-do-projeto)
- [Arquitetura da Solução](#%EF%B8%8F-arquitetura-da-solução)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Como Executar](#-como-executar)
- [Exemplos de Análises](#-exemplos-de-análises)
- [Governança e Qualidade](#-regras-de-negócio--governança)
- [Otimização de Custos](#-otimização-de-custos)
- [Métricas de Performance](#-métricas-de-performance)
- [Troubleshooting](#-troubleshooting)
- [Próximos Passos](#-próximos-passos)
- [Diferenciais do Projeto](#-diferenciais-do-projeto)
- [Sobre o Autor](#-sobre-o-autor)
- [Licença](#-licença)

---

## 📌 Visão Geral

Este projeto implementa uma **solução completa de engenharia de dados** para capturar, processar e analisar informações públicas da **CVM (Resolução CVM 210)**, simulando um cenário real de mercado onde não há API oficial disponível para consumo direto dos dados regulatórios.

> [!IMPORTANT]
> **Contexto Regulatório**: Embora a CVM disponibilize dados públicos em seu portal, **as informações da Resolução CVM 210 (portabilidade de investimentos) são de acesso restrito** e não estão disponíveis publicamente. Este projeto demonstra a capacidade de construir uma arquitetura robusta para captura e análise desses dados em um ambiente corporativo real.

A proposta foi resolver um problema real de negócio, desde a **ingestão automatizada** até a **análise estratégica**, utilizando uma arquitetura moderna em cloud (**AWS + Databricks**) e boas práticas de Data Engineering em produção.

---

## 🎯 Objetivos do Projeto

✅ **Automatizar a captura diária** dos dados publicados pela CVM  
✅ **Garantir persistência, histórico e rastreabilidade** das informações  
✅ **Transformar dados brutos em informação analítica confiável**  
✅ **Viabilizar análises de portabilidade e movimentação de fundos**  
✅ **Criar uma base escalável** para estratégias financeiras futuras

---

## 🏗️ Arquitetura da Solução

![Architecture Diagram](assets/images/architecture_diagram.png)

### Fluxo Completo de Dados

```mermaid
graph TB
    A[CVM Website<br/>inf_diario_fi_YYYYMM.zip] -->|HTTP Download| B[AWS Lambda<br/>Daily Trigger]
    B -->|Unzip + Upload| C[S3 Data Lake<br/>ano=YYYY/mes=MM/]
    C -->|PySpark Read| D{Databricks<br/>ELT Processing}
    D -->|Ingestion<br/>Schema on Read| E[(Bronze Layer<br/>Raw CSV Data)]
    E -->|Transformations<br/>Quality Checks| F[(Silver Layer<br/>Cleaned + Standardized)]
    F -->|Aggregations<br/>Business KPIs| G[(Gold Layer<br/>Analytics Ready)]
    G -->|SQL Queries| H[Portability Analysis<br/>Risk Detection]
    H -.->|Future: Alerts| I[CRM Integration<br/>Planned]
    I -.->|Future: Email| J[Investment Advisors<br/>Planned]
    
    style A fill:#e1f5ff,stroke:#0066cc,stroke-width:2px
    style B fill:#fff4e1,stroke:#ff9900,stroke-width:2px
    style C fill:#ffe1f5,stroke:#cc00cc,stroke-width:2px
    style D fill:#ffe1f5,stroke:#cc00cc,stroke-width:2px
    style E fill:#d4a574,stroke:#8b5a2b,stroke-width:2px
    style F fill:#c0c0c0,stroke:#666666,stroke-width:2px
    style G fill:#ffd700,stroke:#cc9900,stroke-width:2px
    style H fill:#c1f0c1,stroke:#00aa00,stroke-width:2px
    style I fill:#d4d4ff,stroke:#6666ff,stroke-width:2px,stroke-dasharray: 5 5
    style J fill:#f0e1ff,stroke:#9966cc,stroke-width:2px,stroke-dasharray: 5 5
```

> **Legenda**: Componentes com borda tracejada e setas pontilhadas representam funcionalidades planejadas (Future State).

### 🔹 Ingestão de Dados

- **Execução diária via AWS Lambda**, alinhada ao horário de publicação da CVM
- **Extração direta do site da CVM** (simulando ingestão via API de instituições autorizadas)
- **Geração de arquivos diários no Amazon S3** (Data Lake – Raw Zone)
- **Descompactação automática** de arquivos ZIP para CSV

### 🔹 Armazenamento

- **Organização dos dados no S3** com separação lógica por data (`ano=YYYY/mes=MM/`)
- **Persistência histórica** para auditoria e reprocessamento
- **Base preparada para schema evolution**

### 🔄 Processamento & Transformação (ELT)

**Arquitetura Medallion implementada no Databricks:**

![Medallion Flow](assets/images/medallion_flow.png)

#### **Bronze Layer** 🟤
- Dados brutos ingeridos diretamente do S3
- Schema on read
- Sem transformações
- Histórico completo preservado

#### **Silver Layer** ⚪
- **Limpeza e padronização** de dados
- **Tratamento de colunas** (compatibilidade CVM 175 vs formato antigo)
- **Validações de Data Quality** (valores válidos, campos obrigatórios)
- **Deduplicação** via merge (garantia de não duplicidade)
- **Schema evolution** automático
- **Z-Order optimization** por CNPJ_FUNDO

#### **Gold Layer** 🟡
- **Agregações por fundo e período**
- **KPIs de negócio calculados:**
  - Total de captações
  - Total de resgates
  - **Fluxo líquido** (captação - resgate)
  - Patrimônio médio
  - Variação de cota
  - **Indicadores de portabilidade**
- **Dados prontos para BI e análises**

### 🔧 Tecnologias Utilizadas

| Camada | Tecnologia | Propósito |
|--------|-----------|-----------|
| **Ingestão** | AWS Lambda + Python | Automação de captura diária |
| **Storage** | Amazon S3 | Data Lake (Raw Zone) |
| **Processing** | Databricks + PySpark | Processamento distribuído |
| **Data Format** | Delta Lake | Versionamento, ACID, Time Travel |
| **Orchestration** | AWS EventBridge (trigger diário) | Agendamento |
| **Governance** | Unity Catalog | Catálogo de metadados |

---

## 📂 Estrutura do Projeto

```
eng-dados-project/
│
├── assets/
│   └── images/                   # Imagens do projeto (banner, diagramas)
│       ├── project_banner.png
│       ├── architecture_diagram.png
│       └── medallion_flow.png
│
├── notebooks/                     # Jupyter Notebooks
│   ├── pipeline_principal.ipynb  # Pipeline completo (Bronze → Silver → Gold)
│   ├── data_processing.ipynb     # Processamento e transformações
│   └── analytics.ipynb           # Análises de portabilidade e insights
│
├── src/                          # Código Python reutilizável
│   ├── __init__.py
│   ├── utils.py                  # Funções utilitárias (formatação, validação)
│   └── s3_helper.py              # Helper para operações S3
│
├── docs/                         # Documentação técnica
│   ├── lambda_ingestion.md      # Detalhes da ingestão Lambda
│   ├── data_pipeline.md         # Detalhes do pipeline ELT
│   └── analytics_guide.md       # Guia de análises disponíveis
│
├── lambda_function.py            # Função Lambda para ingestão diária
│
├── .gitignore                    # Arquivos ignorados pelo Git
├── .env.example                  # Template de variáveis de ambiente
├── requirements.txt              # Dependências Python
├── LICENSE                       # Licença MIT
└── README.md                     # Este arquivo
```

---

## 🚀 Como Executar

### 1️⃣ Configuração da Ingestão (AWS Lambda)

```bash
# Deploy da função Lambda
aws lambda create-function \
  --function-name cvm210-daily-ingestion \
  --runtime python3.9 \
  --role <IAM_ROLE_ARN> \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda_function.zip

# Configurar trigger diário (EventBridge)
aws events put-rule \
  --name cvm210-daily-trigger \
  --schedule-expression "cron(0 20 * * ? *)"
```

### 2️⃣ Processamento no Databricks

1. **Configurar credenciais AWS** no Databricks (via Secrets ou IAM Role)
2. **Executar notebook `notebooks/pipeline_principal.ipynb`** para criar as camadas Bronze/Silver/Gold
3. **Executar notebook `notebooks/analytics.ipynb`** para análises de portabilidade

### 3️⃣ Consultar Dados Analíticos

```sql
-- Exemplo: Fundos com maior saída de capital (portabilidade)
SELECT 
  CNPJ_FUNDO,
  total_captacao,
  total_resgate,
  fluxo_liquido,
  patrimonio_medio
FROM cvm_p210.gold_cvm210_analytics
WHERE fluxo_liquido < 0
ORDER BY fluxo_liquido ASC
LIMIT 10;
```

---

## 📊 Exemplos de Análises

### Análise de Portabilidade

O projeto gera **insights acionáveis** para o time de negócios:

- **Fundos em risco** (com fluxo líquido negativo)
- **Volume total movimentado** por tipo de portabilidade
- **Tendências de captação vs resgate**

**Exemplo de output:**

| CNPJ_FUNDO | Total Captação | Total Resgate | Fluxo Líquido | Patrimônio Médio |
|------------|----------------|---------------|---------------|------------------|
| 12.345.678 | R$ 1.2M | R$ 2.5M | **-R$ 1.3M** | R$ 450M |
| 23.456.789 | R$ 800K | R$ 1.1M | **-R$ 300K** | R$ 120M |

---

## 🧠 Regras de Negócio & Governança

### Data Quality
- ✅ Validação de **campos obrigatórios** (CNPJ_FUNDO, DT_COMPTC)
- ✅ Filtro de **patrimônio líquido > 0**
- ✅ **Deduplicação automática** via merge

### Metadados e Rastreabilidade
- ✅ Timestamp de processamento em cada camada
- ✅ Particionamento por **ano/mês**
- ✅ Versionamento via **Delta Lake**

### Segurança & Governança
- 🔒 **Credenciais AWS**: IAM Roles via Instance Profile (production-ready)
- 🔒 **Armazenamento**: Unity Catalog para controle de acesso
- 🔒 **Auditoria**: Delta Lake transaction log para rastreabilidade completa
- 🔒 **Versionamento**: Time Travel habilitado para rollback
- 🔒 **Data Lineage**: Rastreamento automático de transformações

---

## 💰 Otimização de Custos (Resumo Executivo)

💰 **Estimated annual savings**: For 10,000 queries/year, savings of **~$137** (from $172 to $35).

Este ganho foi obtido principalmente através de:
- **Uso de formatos colunares (Parquet)**: Redução drástica na quantidade de dados lidos.
- **Compressão Snappy**: Equilíbrio perfeito entre taxa de compressão e velocidade de leitura.
- **Arquitetura Medallion**: Redução de scans desnecessários ao consultar camadas refinadas.
- **Processamento Serverless / Sob Demanda**: Uso eficiente de AWS Lambda e clusters Databricks com auto-termination.

---

## 📊 Métricas de Performance

### Pipeline de Ingestão (Lambda)
| Métrica | Valor Típico |
|---------|--------------|
| **Execution Time** | ~15-25 segundos |
| **Memory Used** | ~300-400 MB |
| **Data Downloaded** | ~800 MB - 1.2 GB |
| **Upload to S3** | ~5-8 segundos |

### Pipeline de Processamento (Databricks)
| Camada | Tempo Médio | Volume Processado |
|--------|-------------|-------------------|
| **Bronze** | ~2 min | 1.5M+ rows |
| **Silver** | ~3-5 min | 1.5M rows (após limpeza) |
| **Gold** | ~1-2 min | ~1K aggregations |
| **Total Pipeline** | **~10 min** | **~1.5M rows** |

---

## 🔍 Key Generated Insights

O pipeline demonstra como a arquitetura suporta análises complexas com baixo custo e alta performance, habilitando decisões estratégicas:

✅ **Portability Trends**: Detecção de fundos com tendência elevada de saída de capital para retenção preventiva.
✅ **Concentration Risk**: Identificação de ativos com alta concentração em poucos investidores, mitigando riscos sistêmicos.
✅ **Market Resilience**: Análise de como as cotas e o patrimônio reagiram a eventos de mercado específicos.
✅ **Regulatory Compliance**: Garantia de integridade e consistência dos dados conforme a Resolução CVM 210.
✅ **Economic Impact**: Correlação entre movimentações de mercado e variações no fluxo líquido de fundos específicos.

---

## 🧠 Technical Decisions

### Why Medallion Architecture?
| Layer | Purpose | Benefit |
|-------|---------|---------|
| **Bronze** | Immutable raw data | Audit and reprocessing |
| **Silver** | Clean and structured data | Quality and consistency |
| **Gold** | Business metrics | Query performance |

### Why Databricks instead of EMR or Glue?
- ✅ **Managed Service**: Facilidade de colaboração e menor overhead operacional.
- ✅ **Delta Lake Features**: ACID transactions, Time Travel e Schema Evolution nativos.
- ✅ **Cost-effective**: Auto-termination e Spot Instances reduzem custos significativamente.
- ✅ **Performance**: Photon engine otimiza o processamento distribuído.

### Why Parquet + Snappy?
- **Parquet**: Formato colunar (selective scan) que lê apenas as colunas necessárias para a query.
- **Snappy**: Velocidade de descompressão 2-3x mais rápida que GZIP, ideal para processamento em tempo real.
- **Cost-benefit**: Ocupa ~60% do tamanho de um CSV GZIP, mas permite queries muito mais rápidas e baratas.

---

## 👨‍💻 Autor

**Gabriel Henrique - Data Engineer**
🎓 Data Engineering Post-Graduate Student | **FIAP**
💼 Specialized in Modern Data Architectures on AWS (S3, Lambda, Databricks, PySpark)
🚀 Experience with ELT pipelines, Medallion Architecture, and performance optimization

� *Open to opportunities in Data Engineering, Analytics Engineering and Cloud Data Platforms.*

---

## 📝 Licença

Este projeto é parte de um trabalho acadêmico (**Tech Challenge - FIAP Post-Graduate Program**).  
Dados públicos fornecidos pela **CVM (Comissão de Valores Mobiliários)**.

---

## 🙏 Agradecimentos

- **CVM** por disponibilizar microdados financeiros públicos.
- **FIAP** pelo ambiente de aprendizado focado em desafios práticos do mercado.
- **AWS** pela documentação completa e ferramentas poderosas de Engenharia de Dados.

⭐ *If this project was useful, consider giving it a star on the repository!*

**Developed with ❤️ using AWS Lambda, S3, Databricks and PySpark.**
> [!NOTE]
> Este projeto foi desenvolvido em ambiente de laboratório AWS Academy para fins educacionais. 
> Os recursos demonstrados foram provisionados temporariamente e posteriormente removidos.

**Desenvolvido com ❤️ e ☕ por um Engenheiro de Dados apaixonado por resolver problemas reais.**
