# Fabric POC — Hybrid Migration Execution Plan

## Architecture Overview

```
Users
  ├── Power BI Reports       → KPI Dashboard, Data Quality, Ontology View
  ├── Fabric Data Agent      → Natural language Q&A over Gold tables
  └── Teams / OneDrive       → Upload CSV files (auto-triggers pipeline)

Microsoft Fabric
  ├── Lakehouse              → Bronze / Silver / Gold (Delta tables)
  ├── Data Factory Pipeline  → Orchestrates notebooks + calls App Service API
  ├── Notebooks (PySpark)    → Bronze→Silver→Gold transforms
  ├── Semantic Model         → Business layer (measures, KPIs, relationships)
  └── Power BI Reports       → Dashboards

Azure App Service (FastAPI)
  └── AI Agent API (LangGraph)
       ├── POST /api/agents/discovery
       ├── POST /api/agents/quality
       ├── POST /api/agents/ontology
       ├── POST /api/agents/semantic
       └── POST /api/agents/kpi

Azure OpenAI
  └── gpt-4.1 deployment

Azure Key Vault
  └── Stores all secrets (API keys, connection strings)
```

---

## Prerequisites — What YOU Must Do (Manual / Portal)

These items **cannot be automated by an agent** and must be done by you in the Azure / Fabric portal.

| #   | Task                                         | Where                                                        | Details                                                                                        |
| --- | -------------------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| 1   | **Create Azure Resource Group**              | Azure Portal                                                 | e.g., `rg-fabric-poc` in your preferred region                                                 |
| 2   | **Create Microsoft Fabric Workspace**        | [app.fabric.microsoft.com](https://app.fabric.microsoft.com) | Name: `Fabric-Steel-Intelligence`. Requires Fabric capacity (F2+ for dev, F64+ for Data Agent) |
| 3   | **Create Fabric Lakehouse**                  | Fabric Portal → Workspace                                    | Name: `steel_lakehouse`. This creates OneLake storage automatically                            |
| 4   | **Create Azure Key Vault**                   | Azure Portal                                                 | Name: `kv-fabric-poc`. Add secrets: `AZURE-OPENAI-KEY`, `AZURE-OPENAI-ENDPOINT`                |
| 5   | **Create Azure App Service**                 | Azure Portal                                                 | Plan: B1 (dev) / P1v3 (prod). Runtime: Python 3.11. Name: `fabric-poc-api`                     |
| 6   | **Configure App Service → Key Vault access** | Azure Portal                                                 | Enable Managed Identity on App Service. Grant `Key Vault Secrets User` role                    |
| 7   | **Create Azure OpenAI resource**             | Azure Portal                                                 | Already exists: `chatbotvikram11x` with `gpt-4.1` deployment                                   |
| 8   | **Create Fabric Data Factory Pipeline**      | Fabric Portal                                                | Done in Phase 4 — detailed steps below                                                         |
| 9   | **Create Fabric Data Agent**                 | Fabric Portal                                                | Done in Phase 6 — requires F64+ capacity                                                       |
| 10  | **Create Power BI Semantic Model & Reports** | Fabric Portal / Power BI Desktop                             | Done in Phase 5                                                                                |

---

## Phase 1: Fabric Lakehouse Setup + Bronze Layer

**Goal:** Get raw CSV data into Fabric Lakehouse as a Delta table.

### What YOU Do:

1. Open Fabric Workspace → Lakehouse (`steel_lakehouse`)
2. Create folder structure: `Files/bronze/` in the Lakehouse file section
3. Upload `bronze_data.csv` to `Files/bronze/` (drag & drop)

### What the AGENT Does:

1. Create Fabric Notebook: `01_bronze_ingestion.py`

```python
# Fabric Notebook — 01_bronze_ingestion

from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Read raw CSV from Lakehouse Files
bronze_df = spark.read.csv(
    "Files/bronze/bronze_data.csv",
    header=True,
    inferSchema=True
)

# Write as Delta table
bronze_df.write.format("delta").mode("overwrite").saveAsTable("bronze_sales")

print(f"Bronze table created: {bronze_df.count()} rows, {len(bronze_df.columns)} columns")
bronze_df.printSchema()
```

### Testing — Phase 1:

| Test                      | Expected Result                           | How to Verify                                           |
| ------------------------- | ----------------------------------------- | ------------------------------------------------------- |
| CSV uploaded to Lakehouse | File visible in `Files/bronze/`           | Fabric Portal → Lakehouse → Files                       |
| Bronze notebook runs      | No errors, prints row count               | Run notebook, check output                              |
| Delta table created       | `bronze_sales` table appears in Lakehouse | Fabric Portal → Lakehouse → Tables                      |
| Row count matches         | Same as original CSV row count            | Run `SELECT COUNT(*) FROM bronze_sales` in SQL endpoint |
| Schema correct            | All columns present with inferred types   | Run `DESCRIBE bronze_sales` in SQL endpoint             |

---

## Phase 2: Silver Layer Transformation

**Goal:** Clean, rename, deduplicate Bronze data → Silver Delta table.

### What the AGENT Does:

1. Create Fabric Notebook: `02_silver_transformation.py`

```python
# Fabric Notebook — 02_silver_transformation

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, to_date, concat_ws, lit
from pyspark.sql.types import DoubleType, IntegerType

spark = SparkSession.builder.getOrCreate()

# Read Bronze
bronze_df = spark.table("bronze_sales")

# Column rename mapping (matches current pipeline/silver.py)
COLUMN_MAP = {
    "sales_doc": "order_id",
    "doc_date": "order_date",
    "customer_code": "customer_id",
    "customer_name": "customer_name",
    "material_code": "product_id",
    "material_name": "product_name",
    "plant": "plant_code",
    "sales_org": "sales_org",
    "order_qty": "quantity_tons",
    "net_value": "revenue",
    "currency": "currency",
    "doc_type": "order_type",
    "item_no": "order_item",
    "region": "region",
    "steel_type": "steel_type",
    "ingestion_timestamp": "ingestion_timestamp",
}

# Apply renames
silver_df = bronze_df
for old_name, new_name in COLUMN_MAP.items():
    if old_name in bronze_df.columns:
        silver_df = silver_df.withColumnRenamed(old_name, new_name)

# Type casting
silver_df = silver_df.withColumn("order_date",
    to_date(col("order_date").cast("string"), "yyyyMMdd")
)
silver_df = silver_df.withColumn("revenue", col("revenue").cast(DoubleType()))
silver_df = silver_df.withColumn("quantity_tons", col("quantity_tons").cast(DoubleType()))

# Dedup on (order_id, order_item)
silver_df = silver_df.dropDuplicates(["order_id", "order_item"])

# Trim string columns
for c in silver_df.columns:
    if silver_df.schema[c].dataType.simpleString() == "string":
        silver_df = silver_df.withColumn(c, trim(col(c)))

# Write Silver Delta table
silver_df.write.format("delta").mode("overwrite").saveAsTable("silver_sales")

print(f"Silver table created: {silver_df.count()} rows")
silver_df.printSchema()
```

### Testing — Phase 2:

| Test                      | Expected Result                             | How to Verify                                                                                                |
| ------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Silver notebook runs      | No errors                                   | Run notebook, check output                                                                                   |
| Columns renamed           | `order_id`, `revenue`, `customer_id`, etc.  | `DESCRIBE silver_sales`                                                                                      |
| `order_date` is Date type | Valid dates, no nulls from parse failures   | `SELECT order_date FROM silver_sales LIMIT 10`                                                               |
| `revenue` is Double       | Numeric values                              | `SELECT revenue FROM silver_sales WHERE revenue IS NOT NULL LIMIT 10`                                        |
| Dedup works               | No duplicate `(order_id, order_item)` pairs | `SELECT order_id, order_item, COUNT(*) c FROM silver_sales GROUP BY 1,2 HAVING c > 1` — should return 0 rows |
| Row count ≤ Bronze        | Dedup may reduce rows                       | Compare counts                                                                                               |

---

## Phase 3: Gold Layer — Star Schema

**Goal:** Build fact + dimension tables from Silver → Gold Delta tables.

### What the AGENT Does:

1. Create Fabric Notebook: `03_gold_star_schema.py`

```python
# Fabric Notebook — 03_gold_star_schema

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, monotonically_increasing_id, month, quarter, year,
    date_format, row_number
)
from pyspark.sql.window import Window

spark = SparkSession.builder.getOrCreate()

silver_df = spark.table("silver_sales")

# --- dim_customer ---
dim_customer = (
    silver_df
    .select("customer_id", "customer_name")
    .dropDuplicates(["customer_id"])
)
dim_customer.write.format("delta").mode("overwrite").saveAsTable("dim_customer")

# --- dim_product ---
dim_product = (
    silver_df
    .select("product_id", "product_name", "steel_type")
    .dropDuplicates(["product_id"])
)
dim_product.write.format("delta").mode("overwrite").saveAsTable("dim_product")

# --- dim_region ---
regions = silver_df.select("region").dropDuplicates()
w = Window.orderBy("region")
dim_region = regions.withColumn("region_id", row_number().over(w))
dim_region = dim_region.select("region_id", "region")
dim_region.write.format("delta").mode("overwrite").saveAsTable("dim_region")

# --- dim_time ---
dates = silver_df.select(col("order_date").alias("date")).dropDuplicates()
dim_time = (
    dates
    .withColumn("month", month("date"))
    .withColumn("quarter", quarter("date"))
    .withColumn("year", year("date"))
    .withColumn("month_name", date_format("date", "MMMM"))
)
dim_time.write.format("delta").mode("overwrite").saveAsTable("dim_time")

# --- fact_sales ---
# Map region → region_id
region_map = dim_region.select("region_id", "region")
fact_sales = silver_df.join(region_map, on="region", how="left")
fact_sales = fact_sales.select(
    "order_id", "order_item", "order_date",
    "customer_id", "product_id", "region_id",
    "quantity_tons", "revenue", "currency", "plant_code"
)
# Add unit_price
fact_sales = fact_sales.withColumn(
    "unit_price",
    col("revenue") / col("quantity_tons")
)
fact_sales.write.format("delta").mode("overwrite").saveAsTable("fact_sales")

# Summary
for table in ["dim_customer", "dim_product", "dim_region", "dim_time", "fact_sales"]:
    count = spark.table(table).count()
    print(f"  {table}: {count} rows")
```

### Testing — Phase 3:

| Test                      | Expected Result                                                       | How to Verify                                                                                                                           |
| ------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| All 5 tables created      | `fact_sales`, `dim_customer`, `dim_product`, `dim_region`, `dim_time` | Fabric Lakehouse → Tables section                                                                                                       |
| Referential integrity     | Every `customer_id` in fact exists in dim_customer                    | `SELECT f.customer_id FROM fact_sales f LEFT JOIN dim_customer d ON f.customer_id = d.customer_id WHERE d.customer_id IS NULL` → 0 rows |
| Referential integrity     | Every `product_id` in fact exists in dim_product                      | Same pattern as above                                                                                                                   |
| Referential integrity     | Every `region_id` in fact exists in dim_region                        | Same pattern as above                                                                                                                   |
| No null keys              | `region_id`, `customer_id`, `product_id` not null in fact             | `SELECT COUNT(*) FROM fact_sales WHERE region_id IS NULL OR customer_id IS NULL` → 0                                                    |
| Revenue totals match      | Sum of `fact_sales.revenue` = sum of `silver_sales.revenue`           | Compare `SELECT SUM(revenue)` from both tables                                                                                          |
| dim_time covers all dates | All `order_date` values from fact exist in dim_time                   | `SELECT DISTINCT order_date FROM fact_sales EXCEPT SELECT date FROM dim_time` → 0 rows                                                  |

---

## Phase 4: Azure App Service — AI Agent API

**Goal:** Deploy the LangGraph agent pipeline as a headless API on Azure App Service.

### What YOU Do:

1. Create App Service (Python 3.11, B1 plan) in Azure Portal
2. Enable Managed Identity
3. Grant Key Vault access to the App Service
4. Configure App Settings:
   - `AZURE_OPENAI_KEY` → Key Vault reference: `@Microsoft.KeyVault(SecretUri=https://kv-fabric-poc.vault.azure.net/secrets/AZURE-OPENAI-KEY)`
   - `AZURE_OPENAI_ENDPOINT` → Key Vault reference
   - `AZURE_OPENAI_API_VERSION` → `2024-12-01-preview`
   - `AZURE_OPENAI_DEPLOYMENT` → `gpt-4.1`
   - `FABRIC_LAKEHOUSE_ENDPOINT` → OneLake endpoint URL (from Fabric portal)

### What the AGENT Does:

1. **Refactor backend for headless API** — remove upload/frontend endpoints, add agent-specific endpoints that accept data as input (not read from local files):

```
POST /api/agents/discovery    — accepts CSV data summary → returns discovery report
POST /api/agents/quality      — accepts quality check results → returns AI analysis
POST /api/agents/ontology     — accepts schema info → returns JSON-LD ontology
POST /api/agents/semantic     — accepts ontology + gold schema → returns semantic model
POST /api/agents/kpi          — accepts computed metrics → returns KPI interpretation
GET  /health                  — health check
```

2. **Create deployment files:**
   - `Dockerfile` for containerized deployment
   - `startup.sh` for App Service
   - Updated `requirements.txt` with all dependencies

3. **Create `Dockerfile`:**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

4. **Create `startup.sh`:**

```bash
#!/bin/bash
cd /app
uvicorn api:app --host 0.0.0.0 --port 8000
```

5. **Update `requirements.txt`** (add missing dependencies):

```
openai>=1.14.0
pandas>=2.0.0
pyarrow>=14.0.0
fastapi>=0.110.0
uvicorn>=0.27.0
python-dotenv>=1.0.0
langchain-openai>=0.3.0
langchain-core>=0.3.0
langgraph>=0.2.0
```

### Testing — Phase 4:

| Test                     | Expected Result            | How to Verify                                            |
| ------------------------ | -------------------------- | -------------------------------------------------------- |
| Docker builds locally    | No errors                  | `docker build -t fabric-poc-api .`                       |
| API starts locally       | Server on port 8000        | `docker run -p 8000:8000 --env-file .env fabric-poc-api` |
| Health check passes      | `{"status": "ok"}`         | `GET http://localhost:8000/health`                       |
| Discovery agent endpoint | Returns valid JSON report  | `POST /api/agents/discovery` with sample CSV summary     |
| Quality agent endpoint   | Returns quality narrative  | `POST /api/agents/quality` with sample quality data      |
| Deploy to App Service    | App running in Azure       | Azure Portal → App Service → Browse URL                  |
| Key Vault secrets loaded | API responds (not 401/500) | Hit `/health` on deployed URL                            |
| All 5 agent endpoints    | Each returns valid JSON    | Test each endpoint with sample payloads                  |

---

## Phase 5: Power BI Semantic Model & Reports

**Goal:** Create enterprise dashboards replacing React frontend.

### What YOU Do:

1. **Create Semantic Model** in Fabric:
   - Open Lakehouse → `New Semantic Model`
   - Select tables: `fact_sales`, `dim_customer`, `dim_product`, `dim_region`, `dim_time`
   - Fabric auto-detects relationships (confirm star schema joins)

2. **Define DAX Measures** (in Semantic Model or Power BI Desktop):

```dax
Total Revenue = SUM(fact_sales[revenue])
Total Volume = SUM(fact_sales[quantity_tons])
Average Selling Price = DIVIDE([Total Revenue], [Total Volume], 0)
Order Count = DISTINCTCOUNT(fact_sales[order_id])
Total Customers = DISTINCTCOUNT(fact_sales[customer_id])
Repeat Customers = CALCULATE(
    DISTINCTCOUNT(fact_sales[customer_id]),
    FILTER(
        SUMMARIZE(fact_sales, fact_sales[customer_id], "Orders", DISTINCTCOUNT(fact_sales[order_id])),
        [Orders] > 1
    )
)
Customer Retention Rate = DIVIDE([Repeat Customers], [Total Customers], 0) * 100
```

3. **Create 3 Power BI Report Pages:**

| Page                    | Visuals                                                                                                                                       | Replaces           |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| **KPI Dashboard**       | 4 KPI cards (Revenue, ASP, Retention, Orders), Bar chart (revenue by region), Pie chart (revenue by product), Table (regional contribution %) | `KPIDashboard.tsx` |
| **Data Quality**        | Card (quality score), Table (rule pass/fail), Text box (AI narrative from quality_report), Risk/recommendation lists                          | `DataQuality.tsx`  |
| **Ontology & Semantic** | Table (entity definitions), Relationship diagram, Glossary table                                                                              | `OntologyView.tsx` |

4. **Publish** report to Fabric Workspace

### Testing — Phase 5:

| Test                      | Expected Result                             | How to Verify                                          |
| ------------------------- | ------------------------------------------- | ------------------------------------------------------ |
| Semantic model created    | 5 tables with relationships                 | Fabric Portal → Semantic Model → Model view            |
| Star schema relationships | fact_sales connects to all 4 dims           | Model diagram shows join lines                         |
| DAX measures calculate    | Revenue, ASP, Retention show correct values | Create a card visual, check against raw data           |
| KPI Dashboard page        | Revenue matches `SUM(revenue)` from SQL     | Cross-check with `SELECT SUM(revenue) FROM fact_sales` |
| Data loads in visuals     | All charts/tables populated                 | Open report, verify no blanks                          |
| Report published          | Accessible to workspace users               | Share link, open in browser                            |

---

## Phase 6: Data Factory Pipeline — End-to-End Orchestration

**Goal:** Automate: CSV upload → Bronze → Silver → Gold → AI Agents → Refresh Power BI.

### What YOU Do:

1. **Create Data Factory Pipeline** in Fabric Portal:

```
Pipeline: Steel_Sales_Intelligence

Activities (in order):
  1. [Notebook] Run 01_bronze_ingestion
  2. [Notebook] Run 02_silver_transformation
  3. [Notebook] Run 03_gold_star_schema
  4. [Web Activity] POST https://fabric-poc-api.azurewebsites.net/api/agents/discovery
  5. [Web Activity] POST https://fabric-poc-api.azurewebsites.net/api/agents/quality
  6. [Web Activity] POST https://fabric-poc-api.azurewebsites.net/api/agents/ontology
  7. [Web Activity] POST https://fabric-poc-api.azurewebsites.net/api/agents/semantic
  8. [Web Activity] POST https://fabric-poc-api.azurewebsites.net/api/agents/kpi
  9. [Dataflow] Store agent JSON outputs back to Lakehouse
  10. [Refresh] Refresh Semantic Model → Power BI auto-updates
```

2. **Configure trigger:**
   - **Manual:** Run pipeline on demand from Fabric Portal
   - **Scheduled:** Daily/weekly cron
   - **Event-based:** File dropped in Lakehouse `Files/bronze/` → auto-triggers pipeline

### Testing — Phase 6:

| Test                              | Expected Result                    | How to Verify                                       |
| --------------------------------- | ---------------------------------- | --------------------------------------------------- |
| Pipeline runs end-to-end          | All 10 activities succeed (green)  | Fabric Portal → Pipeline → Monitor                  |
| Bronze/Silver/Gold tables updated | Row counts correct                 | Query each table                                    |
| Agent API calls succeed           | HTTP 200 from all 5 Web Activities | Check activity output in pipeline monitor           |
| Agent outputs stored              | JSON files in Lakehouse            | Check `Files/agent_outputs/` in Lakehouse           |
| Semantic model refreshed          | Latest data in Power BI            | Open report, verify data timestamp                  |
| Full pipeline < 10 min            | Acceptable runtime for POC         | Check pipeline duration in monitor                  |
| Error handling                    | Failed activity retries / alerts   | Intentionally break one step, verify pipeline stops |

---

## Phase 7: Fabric Data Agent (Chat Q&A)

**Goal:** Enable natural language Q&A over Gold tables — replaces Chat Copilot.

### What YOU Do:

1. **Create Data Agent** in Fabric Portal:
   - Workspace → New → Data Agent
   - Select Lakehouse: `steel_lakehouse`
   - Select tables: `fact_sales`, `dim_customer`, `dim_product`, `dim_region`, `dim_time`
   - Add instructions:
     ```
     You are a Steel Sales Intelligence assistant.
     Answer questions about sales revenue, customer retention, product performance,
     and regional distribution using the Gold layer star schema.
     Always be precise with numbers. Use currency formatting for revenue.
     ```

2. **Test sample questions:**
   - "What is the total revenue?"
   - "Which region has the highest sales?"
   - "What is the customer retention rate?"
   - "Show me top 5 products by revenue"
   - "Compare Q1 vs Q2 revenue"

3. **Publish** Data Agent endpoint (available in Power BI Copilot or via API)

### Testing — Phase 7:

| Test               | Expected Result         | How to Verify                                                            |
| ------------------ | ----------------------- | ------------------------------------------------------------------------ |
| Data Agent created | Accessible in workspace | Fabric Portal → Data Agent                                               |
| Simple question    | Correct revenue number  | Ask "What is the total revenue?" — compare with SQL                      |
| Aggregation query  | Correct grouping        | Ask "Revenue by region" — compare with `SELECT region, SUM(revenue) ...` |
| Join query         | Resolves across tables  | Ask "Top 5 customers by revenue" — requires fact + dim_customer join     |
| Edge case          | Handles gracefully      | Ask about data not in tables — should say "not available"                |
| Concurrent users   | No errors               | Multiple users ask questions simultaneously                              |

---

## Phase 8: Cleanup & Production Hardening

### What the AGENT Does:

1. **Delete React frontend** from repo (no longer needed)
2. **Set up GitHub Actions CI/CD:**
   - On push to `main` → build Docker image → deploy to App Service
   - Run Python tests before deploy
3. **Add API authentication** to App Service (API key or Azure AD)
4. **Add monitoring:**
   - Application Insights on App Service
   - Pipeline alerts in Data Factory

### What YOU Do:

1. **Configure RBAC** in Fabric Workspace (who can view reports, trigger pipeline)
2. **Set up alerts** in Data Factory for pipeline failures
3. **Review Key Vault access policies** — principle of least privilege
4. **Delete `.env` file** from local machine (secrets now in Key Vault)
5. **Delete `OpenaiInfo.txt`** from local machine

### Testing — Phase 8:

| Test                   | Expected Result                       | How to Verify                                      |
| ---------------------- | ------------------------------------- | -------------------------------------------------- | --------------------------------------------------------------------- |
| CI/CD deploys on push  | App Service updated after git push    | Push a change, verify deployment                   |
| API auth enforced      | 401 without API key                   | `curl` without auth header → 401                   |
| Monitoring works       | Requests visible in App Insights      | Azure Portal → Application Insights → Live Metrics |
| Pipeline failure alert | Email/Teams notification              | Intentionally fail pipeline, check notification    |
| Old secrets removed    | No `.env` or `OpenaiInfo.txt` on disk | `ls` in project root                               |
| Git history clean      | No secrets in any commit              | `git log --all -p                                  | grep DD2m1` → should find nothing (requires history rewrite if found) |

---

## Execution Timeline

| Phase                           | Effort    | Dependencies                         |
| ------------------------------- | --------- | ------------------------------------ |
| Phase 1 — Bronze Lakehouse      | 1-2 hours | Fabric workspace + Lakehouse created |
| Phase 2 — Silver Transform      | 1-2 hours | Phase 1                              |
| Phase 3 — Gold Star Schema      | 2-3 hours | Phase 2                              |
| Phase 4 — App Service API       | 3-4 hours | Key Vault + App Service created      |
| Phase 5 — Power BI Reports      | 3-4 hours | Phase 3                              |
| Phase 6 — Data Factory Pipeline | 2-3 hours | Phase 3 + Phase 4                    |
| Phase 7 — Data Agent            | 1-2 hours | Phase 3 (F64+ required)              |
| Phase 8 — Hardening             | 2-3 hours | All phases                           |

---

## Cost Considerations

| Resource               | SKU                    | Approx. Monthly Cost         |
| ---------------------- | ---------------------- | ---------------------------- |
| Fabric Capacity        | F2 (dev/POC)           | ~$260/mo                     |
| Fabric Capacity        | F64 (prod, Data Agent) | ~$8,300/mo                   |
| Azure App Service      | B1 (dev)               | ~$13/mo                      |
| Azure App Service      | P1v3 (prod)            | ~$138/mo                     |
| Azure OpenAI (gpt-4.1) | Pay-per-token          | ~$5-50/mo (depends on usage) |
| Azure Key Vault        | Standard               | ~$0.03/mo                    |

**POC total: ~$280/mo** (F2 + B1 + OpenAI + Key Vault)

---

## Files to Create/Modify (Agent Tasks Summary)

| File                                           | Action                        | Phase |
| ---------------------------------------------- | ----------------------------- | ----- |
| `fabric_notebooks/01_bronze_ingestion.py`      | Create                        | 1     |
| `fabric_notebooks/02_silver_transformation.py` | Create                        | 2     |
| `fabric_notebooks/03_gold_star_schema.py`      | Create                        | 3     |
| `backend/api.py`                               | Refactor (headless agent API) | 4     |
| `backend/requirements.txt`                     | Update (add missing deps)     | 4     |
| `Dockerfile`                                   | Create                        | 4     |
| `startup.sh`                                   | Create                        | 4     |
| `.github/workflows/deploy.yml`                 | Create                        | 8     |
| `frontend/`                                    | Delete entire folder          | 8     |
