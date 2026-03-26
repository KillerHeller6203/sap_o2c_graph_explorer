import os
import sqlite3
import pandas as pd
from google import genai
from dotenv import load_dotenv
from collections import deque

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

# ── Conversation memory (last 5 exchanges) ──────────────────────────────
conversation_history = deque(maxlen=5)

DB_SCHEMA = """
SQLite database: SAP Order-to-Cash (O2C). Tables:

business_partners(businessPartner PK, customer, businessPartnerFullName, organizationBpName1, industry, businessPartnerCategory, creationDate)
business_partner_addresses(businessPartner PK, cityName, country, region, streetName, postalCode)
products(product PK, productType, productGroup, baseUnit, grossWeight, netWeight, division, industrySector)
product_descriptions(product PK, language PK, productDescription)
plants(plant PK, plantName, salesOrganization, distributionChannel, division, plantCategory)
customer_company_assignments(customer PK, companyCode PK, accountingClerk, paymentBlockingReason, paymentMethodsList, paymentTerms, reconciliationAccount, deletionIndicator, customerAccountGroup)
customer_sales_area_assignments(customer PK, salesOrganization PK, distributionChannel PK, division PK, billingIsBlockedForCustomer, supplyingPlant, salesDistrict, salesOffice, shippingCondition)
product_plants(product PK, plant PK, countryOfOrigin, regionOfOrigin, availabilityCheckType, fiscalYearVariant, profitCenter, mrpType)
product_storage_locations(product PK, plant PK, storageLocation PK, physicalInventoryBlockInd)
sales_order_headers(salesOrder PK, salesOrderType, soldToParty, creationDate, totalNetAmount, transactionCurrency, overallDeliveryStatus, overallOrdReltdBillgStatus, requestedDeliveryDate, customerPaymentTerms, salesOrganization)
sales_order_items(salesOrder PK, salesOrderItem PK, material, requestedQuantity, requestedQuantityUnit, netAmount, transactionCurrency, productionPlant, storageLocation, salesDocumentRjcnReason)
sales_order_schedule_lines(salesOrder PK, salesOrderItem PK, scheduleLineNumber PK, scheduledQuantity, requestedDeliveryDate, confirmedDeliveryDate)
outbound_delivery_headers(deliveryDocument PK, shippingPoint, actualGoodsMovementDate, creationDate, overallGoodsMovementStatus, overallPickingStatus, headerBillingBlockReason)
outbound_delivery_items(deliveryDocument PK, deliveryDocumentItem PK, referenceSdDocument, referenceSdDocumentItem, plant, storageLocation, actualDeliveryQuantity, deliveryQuantityUnit)
billing_document_headers(billingDocument PK, billingDocumentType, soldToParty, billingDocumentDate, creationDate, totalNetAmount, transactionCurrency, companyCode, fiscalYear, accountingDocument, billingDocumentIsCancelled)
billing_document_items(billingDocument PK, billingDocumentItem PK, material, billingQuantity, netAmount, transactionCurrency, referenceSdDocument, referenceSdDocumentItem)
billing_document_cancellations(billingDocument PK, cancelledBillingDocument, cancellationDate, companyCode)
journal_entry_items(companyCode PK, fiscalYear PK, accountingDocument PK, accountingDocumentItem PK, referenceDocument, customer, glAccount, amountInTransactionCurrency, transactionCurrency, postingDate, clearingDate, clearingAccountingDocument, financialAccountType, profitCenter)
payments_accounts_receivable(companyCode PK, fiscalYear PK, accountingDocument PK, accountingDocumentItem PK, customer, invoiceReference, salesDocument, amountInTransactionCurrency, transactionCurrency, clearingDate, postingDate)

KEY JOIN PATHS:
- SO->Delivery:   outbound_delivery_items.referenceSdDocument = sales_order_headers.salesOrder
- Delivery->Billing: billing_document_items.referenceSdDocument = outbound_delivery_items.deliveryDocument
- Billing->JournalEntry: journal_entry_items.referenceDocument = billing_document_headers.billingDocument
- Billing->Payment: payments_accounts_receivable.accountingDocument = billing_document_headers.accountingDocument
- Customer: sales_order_headers.soldToParty = business_partners.customer
- Product name: JOIN product_descriptions ON material=product AND language='EN'
- Customer->CompanyAssignment: customer_company_assignments.customer = business_partners.customer
- Customer->SalesArea: customer_sales_area_assignments.customer = business_partners.customer
- Product->Plant: product_plants.product = products.product AND product_plants.plant = plants.plant
- Product->StorageLocation: product_storage_locations.product = products.product

FULL FLOW TEMPLATE:
  sales_order_headers soh
  JOIN outbound_delivery_items odi ON odi.referenceSdDocument = soh.salesOrder
  JOIN billing_document_items bdi ON bdi.referenceSdDocument = odi.deliveryDocument
  JOIN billing_document_headers bdh ON bdh.billingDocument = bdi.billingDocument
  LEFT JOIN journal_entry_items jei ON jei.referenceDocument = bdh.billingDocument
  LEFT JOIN payments_accounts_receivable p ON p.accountingDocument = bdh.accountingDocument
"""

SYSTEM_PROMPT = f"""You are an expert SAP SQL analyst for an Order-to-Cash dataset.

{DB_SCHEMA}

STRICT RULES:
1. If the user's question is completely unrelated to SAP, O2C, or this dataset (e.g. general knowledge, creative writing, coding help), respond EXACTLY:
   REJECT: This system only answers questions about the SAP Order-to-Cash dataset.
2. Otherwise output ONLY a valid SQLite SELECT query. No markdown, no backticks, no explanation.
3. LIMIT to 100 rows unless aggregation.
4. Use product_descriptions with language='EN' for product names.
5. Use conversation history for context (e.g. "show more details" refers to the previous query).
"""

SYNTHESIS_PROMPT = """You are a helpful SAP O2C analyst.
User asked: "{user_query}"
Database returned: {data}

Write a clear natural language answer based ONLY on this data. Cite specific IDs, amounts, counts. No invented facts."""


def _call_gemini(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text.strip()


def _build_history_context() -> str:
    if not conversation_history:
        return ""
    lines = ["Previous conversation:"]
    for entry in conversation_history:
        lines.append(f"  User: {entry['user']}")
        lines.append(f"  SQL: {entry.get('sql', 'N/A')}")
    return "\n".join(lines) + "\n\n"


def generate_sql(user_query: str) -> str:
    history_ctx = _build_history_context()
    prompt = f'{SYSTEM_PROMPT}\n\n{history_ctx}User Query: "{user_query}"'
    return _call_gemini(prompt)


def execute_query(sql: str):
    conn = sqlite3.connect("graph_llm.db")
    try:
        df = pd.read_sql_query(sql, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


def generate_natural_response(user_query: str, data) -> str:
    return _call_gemini(
        SYNTHESIS_PROMPT.format(user_query=user_query, data=str(data)[:5000])
    )


def _extract_highlight_ids(data_results: list) -> list:
    """Extract entity IDs from query results to highlight on the graph."""
    ids = set()
    if not isinstance(data_results, list):
        return []
    key_mappings = {
        "salesOrder": "SO_",
        "deliveryDocument": "DEL_",
        "billingDocument": "BD_",
        "accountingDocument": "JE_",
        "soldToParty": "BP_",
        "customer": "BP_",
    }
    for row in data_results:
        for col, prefix in key_mappings.items():
            val = row.get(col)
            if val and str(val).strip():
                ids.add(f"{prefix}{val}")
    return list(ids)


def process_nl_query(user_query: str) -> dict:
    sql_text = generate_sql(user_query)

    if sql_text.upper().startswith("REJECT:"):
        return {"response": "This system only answers questions about the SAP Order-to-Cash dataset.", "sql": None, "data": [], "highlightIds": []}

    for fence in ("```sql", "```"):
        sql_text = sql_text.replace(fence, "")
    sql_text = sql_text.strip()

    data_results = execute_query(sql_text)

    if isinstance(data_results, dict) and "error" in data_results:
        return {"response": f"Query error: {data_results['error']}", "sql": sql_text, "data": [], "highlightIds": []}

    if not data_results:
        return {"response": "No results found for that query.", "sql": sql_text, "data": [], "highlightIds": []}

    # Save to conversation memory
    conversation_history.append({"user": user_query, "sql": sql_text})

    highlight_ids = _extract_highlight_ids(data_results)

    return {
        "response": generate_natural_response(user_query, data_results),
        "sql": sql_text,
        "data": data_results,
        "highlightIds": highlight_ids,
    }


def get_graph_data(limit: int = 30) -> dict:
    conn = sqlite3.connect("graph_llm.db")
    cur = conn.cursor()
    nodes, edges, node_ids = [], [], set()

    def add_node(nid, label, ntype, meta=None):
        if nid not in node_ids:
            node_ids.add(nid)
            nodes.append({"id": nid, "label": label, "type": ntype, "meta": meta or {}})

    try:
        # Sales Orders + Customers
        rows = cur.execute(f"SELECT salesOrder, soldToParty, totalNetAmount, transactionCurrency, overallDeliveryStatus, overallOrdReltdBillgStatus FROM sales_order_headers LIMIT {limit}").fetchall()
        so_ids = []
        for so, sold_to, amt, curr, del_st, bill_st in rows:
            add_node(f"SO_{so}", so, "SalesOrder", {"amount": amt, "currency": curr, "deliveryStatus": del_st, "billingStatus": bill_st})
            add_node(f"BP_{sold_to}", sold_to, "Customer", {"customerId": sold_to})
            edges.append({"source": f"BP_{sold_to}", "target": f"SO_{so}", "label": "placed"})
            so_ids.append(so)

        if not so_ids:
            return {"nodes": nodes, "edges": edges}

        # Deliveries
        ph = ",".join(["?" for _ in so_ids])
        rows = cur.execute(f"SELECT DISTINCT deliveryDocument, referenceSdDocument FROM outbound_delivery_items WHERE referenceSdDocument IN ({ph}) LIMIT {limit}", so_ids).fetchall()
        del_ids = []
        for del_doc, ref_so in rows:
            add_node(f"DEL_{del_doc}", del_doc, "Delivery", {})
            edges.append({"source": f"SO_{ref_so}", "target": f"DEL_{del_doc}", "label": "delivered_via"})
            if del_doc not in del_ids:
                del_ids.append(del_doc)

        if not del_ids:
            return {"nodes": nodes, "edges": edges}

        # Billing docs
        ph2 = ",".join(["?" for _ in del_ids])
        rows = cur.execute(f"SELECT DISTINCT bdi.billingDocument, bdi.referenceSdDocument, bdh.totalNetAmount, bdh.transactionCurrency, bdh.accountingDocument FROM billing_document_items bdi JOIN billing_document_headers bdh ON bdi.billingDocument=bdh.billingDocument WHERE bdi.referenceSdDocument IN ({ph2}) LIMIT {limit}", del_ids).fetchall()
        bd_to_acc = {}
        for bd, ref_del, amt, curr, acc_doc in rows:
            add_node(f"BD_{bd}", bd, "BillingDoc", {"amount": amt, "currency": curr})
            edges.append({"source": f"DEL_{ref_del}", "target": f"BD_{bd}", "label": "billed_as"})
            bd_to_acc[bd] = acc_doc

        # Journal entries + Payments
        for bd, acc_doc in list(bd_to_acc.items())[:20]:
            je_rows = cur.execute("SELECT accountingDocument, amountInTransactionCurrency, transactionCurrency FROM journal_entry_items WHERE referenceDocument=? LIMIT 1", (bd,)).fetchall()
            for je_doc, je_amt, je_curr in je_rows:
                je_id = f"JE_{je_doc}"
                add_node(je_id, je_doc, "JournalEntry", {"amount": je_amt, "currency": je_curr})
                edges.append({"source": f"BD_{bd}", "target": je_id, "label": "posted_to"})

            if acc_doc:
                p_rows = cur.execute("SELECT accountingDocument, amountInTransactionCurrency, transactionCurrency FROM payments_accounts_receivable WHERE accountingDocument=? LIMIT 1", (acc_doc,)).fetchall()
                for p_doc, p_amt, p_curr in p_rows:
                    pid = f"PAY_{p_doc}"
                    add_node(pid, p_doc, "Payment", {"amount": p_amt, "currency": p_curr})
                    edges.append({"source": f"BD_{bd}", "target": pid, "label": "paid_by"})

    except Exception as e:
        print(f"Graph error: {e}")
    finally:
        conn.close()

    return {"nodes": nodes, "edges": edges}
