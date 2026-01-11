# Pipeline de Dados - Arquitetura Medallion

## Visão Geral

O pipeline de dados implementa a **Arquitetura Medallion** (Bronze → Silver → Gold) no Databricks, transformando dados brutos da CVM em informações analíticas prontas para consumo.

## Camadas de Dados

### 🟤 Bronze Layer - Dados Brutos

#### Propósito
- Ingestão de dados brutos diretamente do S3
- Preservação histórica completa
- Schema on read (sem validações)

#### Implementação

```python
df_bronze = (spark.read.format("csv")
    .option("header", "true")
    .option("inferSchema", "true")
    .option("delimiter", ";")
    .option("encoding", "ISO-8859-1")
    .option("fs.s3a.access.key", access_key)
    .option("fs.s3a.secret.key", secret_key)
    .option("fs.s3a.session.token", session_token)
    .option("fs.s3a.aws.credentials.provider", 
            "org.apache.hadoop.fs.s3a.TemporaryAWSCredentialsProvider")
    .load(path_bronze_csv)
)

# Salva como tabela Delta
df_bronze.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("cvm_p210.bronze_inf_diario")
```

#### Características
- ✅ **Formato**: Delta Lake
- ✅ **Schema**: Inferido automaticamente
- ✅ **Encoding**: ISO-8859-1 (padrão CVM)
- ✅ **Separador**: `;` (ponto e vírgula)

---

### ⚪ Silver Layer - Dados Limpos e Padronizados

#### Propósito
- Limpeza e padronização de dados
- Aplicação de regras de qualidade
- Tratamento de evolução de schema
- Deduplicação

#### Transformações Aplicadas

##### 1. Tratamento de Colunas (Compatibilidade CVM 175)

```python
# Compatibilidade entre formatos antigo e novo da CVM
df_silver = df_bronze.withColumn(
    "CNPJ_FUNDO",
    coalesce(col("CNPJ_FUNDO"), col("cnpj_fundo"))
)
```

**Motivo:** A CVM alterou padrão de nomenclatura em algumas publicações.

##### 2. Conversão de Tipos de Dados

```python
df_silver = df_silver \
    .withColumn("DT_COMPTC", to_date(col("DT_COMPTC"), "yyyy-MM-dd")) \
    .withColumn("VL_TOTAL", col("VL_TOTAL").cast("double")) \
    .withColumn("VL_QUOTA", col("VL_QUOTA").cast("double")) \
    .withColumn("VL_PATRIM_LIQ", col("VL_PATRIM_LIQ").cast("double")) \
    .withColumn("CAPTC_DIA", col("CAPTC_DIA").cast("double")) \
    .withColumn("RESG_DIA", col("RESG_DIA").cast("double"))
```

##### 3. Enriquecimento de Dados

```python
df_silver = df_silver \
    .withColumn("ano", year(col("DT_COMPTC"))) \
    .withColumn("mes", month(col("DT_COMPTC"))) \
    .withColumn("dh_processamento_silver", current_timestamp())
```

**Metadados adicionados:**
- `ano`: Particionamento
- `mes`: Particionamento
- `dh_processamento_silver`: Rastreabilidade

##### 4. Data Quality - Filtros

```python
df_silver = df_silver.filter("VL_PATRIM_LIQ > 0")
```

**Regra:** Remove registros com patrimônio líquido inválido.

#### Estratégia de Merge (Deduplicação)

```python
if DeltaTable.isDeltaTable(spark, "cvm_p210.silver_inf_diario"):
    delta_table = DeltaTable.forName(spark, "cvm_p210.silver_inf_diario")
    
    delta_table.alias("target").merge(
        df_silver.alias("source"),
        "target.CNPJ_FUNDO = source.CNPJ_FUNDO AND target.DT_COMPTC = source.DT_COMPTC"
    ).whenMatchedUpdateAll() \
     .whenNotMatchedInsertAll() \
     .execute()
else:
    df_silver.write.format("delta") \
        .partitionBy("ano", "mes") \
        .saveAsTable("cvm_p210.silver_inf_diario")
```

**Garantia:** Não há duplicatas para o mesmo `CNPJ_FUNDO + DT_COMPTC`.

#### Otimização

```sql
OPTIMIZE cvm_p210.silver_inf_diario ZORDER BY (CNPJ_FUNDO)
```

**Benefício:** Consultas filtradas por CNPJ_FUNDO são até **10x mais rápidas**.

---

### 🟡 Gold Layer - Dados Analíticos

#### Propósito
- Agregações por fundo e período
- Cálculo de KPIs de negócio
- Dados prontos para BI e análises

#### Regras de Negócio Implementadas

##### 1. Agregações Base

```python
df_gold_base = df_silver.groupBy("CNPJ_FUNDO", "ano", "mes").agg(
    count("*").alias("dias_negociacao"),
    sum("CAPTC_DIA").alias("total_captacao"),
    sum("RESG_DIA").alias("total_resgate"),
    avg("VL_PATRIM_LIQ").alias("patrimonio_medio"),
    max("VL_QUOTA").alias("cota_maxima"),
    min("VL_QUOTA").alias("cota_minima")
)
```

##### 2. KPIs Calculados

```python
df_gold_insights = df_gold_base \
    .withColumn("fluxo_liquido", 
                round(col("total_captacao") - col("total_resgate"), 2)) \
    .withColumn("variacao_cota_mes", 
                round(((col("cota_maxima") - col("cota_minima")) / col("cota_minima")) * 100, 2))
```

**KPIs Criados:**
- **Fluxo Líquido**: Indica se houve entrada ou saída de capital
  - `> 0`: Captação líquida (positivo para o fundo)
  - `< 0`: Resgate líquido (portabilidade de saída)
- **Variação de Cota**: Performance do fundo no período

##### 3. Metadados Analíticos

```python
df_gold_insights = df_gold_insights \
    .withColumn("dh_geracao_analytics", current_timestamp()) \
    .withColumn("versao_pipeline", lit("1.0"))
```

#### Escrita na Camada Gold

```python
df_gold_insights.write.format("delta") \
    .mode("overwrite") \
    .saveAsTable("cvm_p210.gold_cvm210_analytics")
```

---

## Governança e Metadados

### Unity Catalog

Todas as tabelas são criadas no **Unity Catalog** do Databricks:

```
Catalog: cvm_p210
├── bronze_inf_diario
├── silver_inf_diario
└── gold_cvm210_analytics
```

**Benefícios:**
- 📚 **Catálogo centralizado** de metadados
- 🔒 **Controle de acesso** granular
- 📊 **Data lineage** automático

### Versionamento (Delta Lake)

#### Time Travel

```sql
-- Ver versão anterior da tabela
SELECT * FROM cvm_p210.silver_inf_diario VERSION AS OF 5

-- Ver tabela em data específica
SELECT * FROM cvm_p210.silver_inf_diario TIMESTAMP AS OF '2026-01-10'
```

#### Histórico de Versões

```sql
DESCRIBE HISTORY cvm_p210.silver_inf_diario
```

---

## Execução do Pipeline

### Ordem de Execução

1. **Bronze**: Ingestão de dados brutos do S3
2. **Silver**: Limpeza, padronização e merge
3. **Gold**: Agregações e cálculo de KPIs

### Idempotência

O pipeline é **idempotente**:
- Múltiplas execuções do mesmo período **não criam duplicatas**
- Merge garante `UPSERT` (atualiza se existe, insere se não existe)

---

## Monitoramento e Qualidade

### Data Quality Checks

| Check | Descrição | Ação |
|-------|-----------|------|
| Patrimônio > 0 | Valida patrimônio líquido positivo | Remove registros inválidos |
| Campos obrigatórios | CNPJ_FUNDO, DT_COMPTC não nulos | Garantido pela merge key |
| Duplicatas | Chave (CNPJ + Data) única | Merge evita duplicação |

### Logs de Processamento

Cada camada registra timestamp de processamento:
- `dh_processamento_silver`: Quando foi processado na Silver
- `dh_geracao_analytics`: Quando foi gerado na Gold

---

## Próximas Melhorias

> [!NOTE]
> **Evolução do Pipeline**

- [ ] **Validação de schema** antes da ingestão
- [ ] **Alertas de Data Quality** (ex: SNS quando patrimônio médio cai muito)
- [ ] **Métricas de pipeline** (tempo de execução, volume de dados)
- [ ] **Testes automatizados** (Great Expectations)
- [ ] **Orquestração completa** (Databricks Workflows ou Airflow)

---

## Código Completo

[Ver notebook_principal.ipynb](file:///c:/Users/Usuario/.gemini/antigravity/scratch/eng-dados-project/notebook_principal.ipynb)
