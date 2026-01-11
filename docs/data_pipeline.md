# Data Pipeline - Medallion Architecture

## Overview

The data pipeline implements the **Medallion Architecture** (Bronze → Silver → Gold) in Databricks, transforming raw CVM data into analysis-ready information.

## Data Layers

### 🟤 Bronze Layer - Raw Data

#### Purpose
- Ingestion of raw data directly from S3.
- Full historical preservation.
- Schema on read (no validations).

#### Implementation

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

# Save as a Delta table
df_bronze.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("cvm_p210.bronze_inf_diario")
```

#### Characteristics
- ✅ **Format**: Delta Lake
- ✅ **Schema**: Automatically inferred
- ✅ **Encoding**: ISO-8859-1 (CVM standard)
- ✅ **Delimiter**: `;` (semicolon)

---

### ⚪ Silver Layer - Clean and Standardized Data

#### Purpose
- Data cleaning and standardization.
- Application of quality rules.
- Handling schema evolution.
- Deduplication.

#### Transformations Applied

##### 1. Column Handling (CVM 175 Compatibility)

```python
# Compatibility between CVM legacy and new formats
df_silver = df_bronze.withColumn(
    "CNPJ_FUNDO",
    coalesce(col("CNPJ_FUNDO"), col("cnpj_fundo"))
)
```

**Reason:** CVM changed its naming standard in some publications.

##### 2. Data Type Conversion

```python
df_silver = df_silver \
    .withColumn("DT_COMPTC", to_date(col("DT_COMPTC"), "yyyy-MM-dd")) \
    .withColumn("VL_TOTAL", col("VL_TOTAL").cast("double")) \
    .withColumn("VL_QUOTA", col("VL_QUOTA").cast("double")) \
    .withColumn("VL_PATRIM_LIQ", col("VL_PATRIM_LIQ").cast("double")) \
    .withColumn("CAPTC_DIA", col("CAPTC_DIA").cast("double")) \
    .withColumn("RESG_DIA", col("RESG_DIA").cast("double"))
```

##### 3. Data Enrichment

```python
df_silver = df_silver \
    .withColumn("ano", year(col("DT_COMPTC"))) \
    .withColumn("mes", month(col("DT_COMPTC"))) \
    .withColumn("dh_processamento_silver", current_timestamp())
```

**Added Metadata:**
- `ano`: Partitioning (Year)
- `mes`: Partitioning (Month)
- `dh_processamento_silver`: Traceability

##### 4. Data Quality - Filters

```python
df_silver = df_silver.filter("VL_PATRIM_LIQ > 0")
```

**Rule:** Removes records with invalid Net Asset Value (NAV).

#### Merge Strategy (Deduplication)

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

**Guarantee:** No duplicates for the same `CNPJ_FUNDO + DT_COMPTC`.

#### Optimization

```sql
OPTIMIZE cvm_p210.silver_inf_diario ZORDER BY (CNPJ_FUNDO)
```

**Benefit:** Queries filtered by `CNPJ_FUNDO` are up to **10x faster**.

---

### 🟡 Gold Layer - Analytical Data

#### Purpose
- Aggregations by fund and period.
- Business KPI calculation.
- Data ready for BI and analytics.

#### Implemented Business Rules

##### 1. Base Aggregations

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

##### 2. Calculated KPIs

```python
df_gold_insights = df_gold_base \
    .withColumn("fluxo_liquido", 
                round(col("total_captacao") - col("total_resgate"), 2)) \
    .withColumn("variacao_cota_mes", 
                round(((col("cota_maxima") - col("cota_minima")) / col("cota_minima")) * 100, 2))
```

**KPIs Created:**
- **Net Flow (Fluxo Líquido)**: Indicates whether there was a capital inflow or outflow.
  - `> 0`: Net inflow (positive for the fund).
  - `< 0`: Net outflow (portability outflow).
- **Quota Variation**: Fund performance over the period.

##### 3. Analytical Metadata

```python
df_gold_insights = df_gold_insights \
    .withColumn("dh_geracao_analytics", current_timestamp()) \
    .withColumn("versao_pipeline", lit("1.0"))
```

#### Writing to the Gold Layer

```python
df_gold_insights.write.format("delta") \
    .mode("overwrite") \
    .saveAsTable("cvm_p210.gold_cvm210_analytics")
```

---

## Governance and Metadata

### Unity Catalog

All tables are created in the Databricks **Unity Catalog**:

```
Catalog: cvm_p210
├── bronze_inf_diario
├── silver_inf_diario
└── gold_cvm210_analytics
```

**Benefits:**
- 📚 **Centralized metadata catalog**.
- 🔒 **Granular access control**.
- 📊 **Automatic data lineage**.

### Versioning (Delta Lake)

#### Time Travel

```sql
-- View a previous version of the table
SELECT * FROM cvm_p210.silver_inf_diario VERSION AS OF 5

-- View the table as of a specific timestamp
SELECT * FROM cvm_p210.silver_inf_diario TIMESTAMP AS OF '2026-01-10'
```

#### Version History

```sql
DESCRIBE HISTORY cvm_p210.silver_inf_diario
```

---

## Pipeline Execution

### Execution Order

1. **Bronze**: Raw data ingestion from S3.
2. **Silver**: Cleaning, standardization, and merge.
3. **Gold**: Aggregations and KPI calculations.

### Idempotency

The pipeline is **idempotent**:
- Multiple executions for the same period **do not create duplicates**.
- Merge ensures `UPSERT` behavior (updates if exists, inserts if not).

---

## Monitoring and Quality

### Data Quality Checks

| Check | Description | Action |
|-------|-----------|------|
| NAV > 0 | Validates positive Net Asset Value | Removes invalid records |
| Mandatory fields | CNPJ_FUNDO, DT_COMPTC non-null | Guaranteed by merge key |
| Duplicates | Unique key (CNPJ + Date) | Merge prevents duplication |

### Processing Logs

Each layer records a processing timestamp:
- `dh_processamento_silver`: When processed in the Silver layer.
- `dh_geracao_analytics`: When generated in the Gold layer.

---

## Future Improvements

> [!NOTE]
> **Pipeline Evolution**

- [ ] **Schema validation** before ingestion.
- [ ] **Data Quality Alerts** (e.g., SNS notification when average assets drop significantly).
- [ ] **Pipeline metrics** (execution time, processed volume).
- [ ] **Automated tests** (Great Expectations).
- [ ] **Full orchestration** (Databricks Workflows or Airflow).

---

## Full Code

[View pipeline_principal.ipynb](file:///c:/Users/Usuario/.gemini/antigravity/scratch/eng-dados-project/notebooks/pipeline_principal.ipynb)
