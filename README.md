# SAP O2C Graph Explorer

A context-graph system with an LLM-powered query interface for exploring SAP Order-to-Cash data.

## Architecture

```
Frontend (single-page HTML + D3.js)
        │
        ▼
FastAPI backend (Python)
        ├── /graph   → builds node/edge graph from SQLite
        └── /query   → NL → SQL (Gemini) → execute → NL response
                 │
                 ▼
         SQLite database (real SAP JSONL data ingested on startup)
```

## Graph Model

Nodes: **Customer → Sales Order → Outbound Delivery → Billing Document → Journal Entry → Payment**

Edges are derived from referential keys in the SAP dataset:
- `outbound_delivery_items.referenceSdDocument = sales_order_headers.salesOrder`
- `billing_document_items.referenceSdDocument = outbound_delivery_items.deliveryDocument`
- `journal_entry_items.referenceDocument = billing_document_headers.billingDocument`
- `payments_accounts_receivable.invoiceReference = billing_document_headers.accountingDocument`

## Database Choice

**SQLite** — chosen because:
- Zero-config, file-based, ships with Python
- The dataset is small enough (~500 records across 19 tables)
- SQLAlchemy ORM makes it trivially swappable to Postgres for production
- Enables direct SQL execution from Gemini-generated queries

## LLM Prompting Strategy

Two-stage prompting with conversation memory:

1. **SQL Generation** — Full schema (all 19 tables + JOIN paths) injected into system prompt. Last 5 conversation exchanges are included as context so the LLM can resolve follow-up queries like "show more details". Gemini converts NL → SQLite SQL.
2. **Response Synthesis** — Raw JSON rows + original question fed back to Gemini to generate a natural language answer grounded in the data.

The schema prompt includes all table names, column names, primary keys, and the join paths between tables so Gemini can construct multi-hop queries (e.g., SO → Delivery → Billing → Payment).

## Guardrails

If the user's question is not related to the SAP O2C dataset, the SQL generation prompt instructs the model to reply with `REJECT:` prefix. The backend detects this and returns a safe message without executing any query. This prevents:
- General knowledge questions
- Creative writing requests
- Prompt injection attempts

## Bonus Features

- **Conversation Memory**: Last 5 Q&A exchanges are preserved and injected as context, enabling follow-up queries.
- **Node Highlighting**: When a query returns results referencing specific entities (sales orders, customers, etc.), the corresponding graph nodes pulse with a glow animation.
- **NL → SQL Translation**: Every response shows the generated SQL query with a toggle button, making the system fully transparent.

## Running Locally

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # add your GEMINI_API_KEY
uvicorn main:app --reload --port 8000
# Open http://localhost:8000
```

The database is auto-created and data is auto-ingested from the `data/` folder on first startup.

## Dataset Tables

| Table | Rows | Description |
|---|---|---|
| sales_order_headers | 100 | SAP sales orders |
| sales_order_items | 167 | Line items per order |
| sales_order_schedule_lines | — | Schedule lines per item |
| outbound_delivery_headers | 86 | Delivery documents |
| outbound_delivery_items | 137 | Delivery line items (links to SO) |
| billing_document_headers | 163 | Billing/invoice headers |
| billing_document_items | 245 | Billing line items (links to delivery) |
| billing_document_cancellations | 80 | Cancelled billing docs |
| journal_entry_items | 123 | Accounting entries (links to billing) |
| payments_accounts_receivable | 120 | Payments (links to billing) |
| business_partners | 8 | Customers |
| business_partner_addresses | — | Customer addresses |
| products | 69 | Materials/products |
| product_descriptions | — | Product names (multi-language) |
| plants | 44 | Plant master data |
| customer_company_assignments | — | Customer ↔ company code mapping |
| customer_sales_area_assignments | — | Customer ↔ sales area mapping |
| product_plants | — | Product ↔ plant mapping |
| product_storage_locations | — | Product ↔ storage location mapping |

## Example Queries

- "Which products are associated with the highest number of billing documents?"
- "Trace the full flow for sales order 740506"
- "Show sales orders that have been delivered but not billed"
- "Top 10 customers by total billing amount"
- "List all cancelled billing documents"
- "What is the capital of France?" → *Rejected (guardrail)*
