import os
import glob
import json
import sqlite3
from database import engine, Base
from models import *  # noqa – ensures all tables are registered

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def safe_val(val):
    """Return None for empty/null-ish values, otherwise the value as-is."""
    if val in (None, "", "null"):
        return None
    return val


def safe_float(val):
    try:
        return float(val) if val not in (None, "", "null") else None
    except (ValueError, TypeError):
        return None


def load_jsonl(folder):
    records = []
    pattern = os.path.join(DATA_DIR, folder, "*.jsonl")
    for fpath in glob.glob(pattern):
        with open(fpath) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return records


# ── Table configs: (folder_name, table_name, column_mapping) ─────────────
# column_mapping: list of (jsonl_key, db_column, transform_fn)

_str = lambda v: str(v) if v not in (None, "", "null") else ""
_sf = safe_float

TABLE_CONFIGS = [
    ("business_partners", "business_partners", [
        ("businessPartner",), ("customer",), ("businessPartnerFullName",),
        ("businessPartnerName",), ("organizationBpName1",), ("industry",),
        ("businessPartnerCategory",), ("creationDate", None, _str),
        ("isMarkedForArchiving", None, _str),
    ]),
    ("business_partner_addresses", "business_partner_addresses", [
        ("businessPartner",), ("cityName",), ("country",), ("region",),
        ("streetName",), ("postalCode",),
    ]),
    ("products", "products", [
        ("product",), ("productType",), ("productGroup",), ("baseUnit",),
        ("grossWeight", None, _sf), ("netWeight", None, _sf),
        ("division",), ("industrySector",), ("isMarkedForDeletion", None, _str),
    ]),
    ("product_descriptions", "product_descriptions", [
        ("product",), ("language",), ("productDescription",),
    ]),
    ("plants", "plants", [
        ("plant",), ("plantName",), ("salesOrganization",),
        ("distributionChannel",), ("division",), ("plantCategory",),
    ]),
    ("sales_order_headers", "sales_order_headers", [
        ("salesOrder",), ("salesOrderType",), ("soldToParty",),
        ("creationDate", None, _str), ("totalNetAmount", None, _sf),
        ("transactionCurrency",), ("overallDeliveryStatus",),
        ("overallOrdReltdBillgStatus",), ("requestedDeliveryDate", None, _str),
        ("customerPaymentTerms",), ("salesOrganization",),
    ]),
    ("sales_order_items", "sales_order_items", [
        ("salesOrder",), ("salesOrderItem",), ("material",),
        ("requestedQuantity", None, _sf), ("requestedQuantityUnit",),
        ("netAmount", None, _sf), ("transactionCurrency",),
        ("productionPlant",), ("storageLocation",), ("salesDocumentRjcnReason",),
    ]),
    ("sales_order_schedule_lines", "sales_order_schedule_lines", [
        ("salesOrder",), ("salesOrderItem",), ("scheduleLineNumber",),
        ("scheduledQuantity", None, _sf), ("requestedDeliveryDate", None, _str),
        ("confirmedDeliveryDate", None, _str),
    ]),
    ("outbound_delivery_headers", "outbound_delivery_headers", [
        ("deliveryDocument",), ("shippingPoint",),
        ("actualGoodsMovementDate", None, _str), ("creationDate", None, _str),
        ("overallGoodsMovementStatus",), ("overallPickingStatus",),
        ("headerBillingBlockReason",),
    ]),
    ("outbound_delivery_items", "outbound_delivery_items", [
        ("deliveryDocument",), ("deliveryDocumentItem",),
        ("referenceSdDocument",), ("referenceSdDocumentItem",),
        ("plant",), ("storageLocation",),
        ("actualDeliveryQuantity", None, _sf), ("deliveryQuantityUnit",),
    ]),
    ("billing_document_headers", "billing_document_headers", [
        ("billingDocument",), ("billingDocumentType",), ("soldToParty",),
        ("billingDocumentDate", None, _str), ("creationDate", None, _str),
        ("totalNetAmount", None, _sf), ("transactionCurrency",),
        ("companyCode",), ("fiscalYear",), ("accountingDocument",),
        ("billingDocumentIsCancelled", None, _str),
    ]),
    ("billing_document_items", "billing_document_items", [
        ("billingDocument",), ("billingDocumentItem",), ("material",),
        ("billingQuantity", None, _sf), ("netAmount", None, _sf),
        ("transactionCurrency",), ("referenceSdDocument",),
        ("referenceSdDocumentItem",),
    ]),
    ("billing_document_cancellations", "billing_document_cancellations", [
        ("billingDocument",), ("cancelledBillingDocument",),
        ("cancellationDate", None, _str), ("companyCode",),
    ]),
    ("journal_entry_items_accounts_receivable", "journal_entry_items", [
        ("companyCode",), ("fiscalYear",), ("accountingDocument",),
        ("accountingDocumentItem",), ("referenceDocument",), ("customer",),
        ("glAccount",), ("amountInTransactionCurrency", None, _sf),
        ("transactionCurrency",), ("postingDate", None, _str),
        ("clearingDate", None, _str), ("clearingAccountingDocument",),
        ("financialAccountType",), ("profitCenter",),
    ]),
    ("payments_accounts_receivable", "payments_accounts_receivable", [
        ("companyCode",), ("fiscalYear",), ("accountingDocument",),
        ("accountingDocumentItem",), ("customer",), ("invoiceReference",),
        ("salesDocument",), ("amountInTransactionCurrency", None, _sf),
        ("transactionCurrency",), ("clearingDate", None, _str),
        ("postingDate", None, _str),
    ]),
    ("customer_company_assignments", "customer_company_assignments", [
        ("customer",), ("companyCode",), ("accountingClerk",),
        ("accountingClerkFaxNumber",), ("alternativePayerAccount",),
        ("paymentBlockingReason",), ("paymentMethodsList",),
        ("paymentTerms",), ("reconciliationAccount",),
        ("deletionIndicator",), ("customerAccountGroup",),
    ]),
    ("customer_sales_area_assignments", "customer_sales_area_assignments", [
        ("customer",), ("salesOrganization",), ("distributionChannel",),
        ("division",), ("billingIsBlockedForCustomer",), ("supplyingPlant",),
        ("salesDistrict",), ("exchangeRateType",), ("salesOffice",),
        ("shippingCondition",),
    ]),
    ("product_plants", "product_plants", [
        ("product",), ("plant",), ("countryOfOrigin",), ("regionOfOrigin",),
        ("productionInvtryManagedLoc",), ("availabilityCheckType",),
        ("fiscalYearVariant",), ("profitCenter",), ("mrpType",),
    ]),
    ("product_storage_locations", "product_storage_locations", [
        ("product",), ("plant",), ("storageLocation",),
        ("physicalInventoryBlockInd",),
        ("dateOfLastPostedCntUnRstrcdStk", None, _str),
    ]),
]


def _ingest_table(conn, folder, table, col_defs):
    """Load JSONL → INSERT OR IGNORE into SQLite (handles duplicates cleanly)."""
    records = load_jsonl(folder)
    if not records:
        print(f"  ⚠ No data found for {folder}")
        return 0

    # Build column names from config
    columns = [c[0] for c in col_defs]
    placeholders = ",".join(["?" for _ in columns])
    col_names = ",".join([f'"{c}"' for c in columns])
    sql = f'INSERT OR IGNORE INTO "{table}" ({col_names}) VALUES ({placeholders})'

    rows = []
    for r in records:
        row = []
        for cdef in col_defs:
            key = cdef[0]
            transform = cdef[2] if len(cdef) > 2 else None
            val = r.get(key, "")
            if transform:
                val = transform(val)
            elif val in (None, "null"):
                val = ""
            row.append(val)
        rows.append(tuple(row))

    conn.executemany(sql, rows)
    conn.commit()
    return len(rows)


def ingest():
    """Ingest all JSONL data into SQLite. Idempotent — skips if data exists."""
    Base.metadata.create_all(bind=engine)

    # Use raw sqlite3 with INSERT OR IGNORE for duplicate-safe bulk inserts
    conn = sqlite3.connect("graph_llm.db")

    # Check if already ingested
    try:
        # NEW — checks ALL critical tables
        MUST_HAVE = {
            "billing_document_headers": 150,
            "outbound_delivery_items": 120,
            "journal_entry_items": 100,
            "payments_accounts_receivable": 100,
            "sales_order_headers": 90,
        }
        for table, minimum in MUST_HAVE.items():
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if count < minimum:
                print(f"  ⚠ {table} has {count} rows — re-ingesting all tables.")
                break
        else:
            print("✅ Database already fully populated. Skipping.")
            conn.close()
            return
    except Exception:
        pass

    for folder, table, col_defs in TABLE_CONFIGS:
        print(f"Ingesting {folder}...")
        try:
            n = _ingest_table(conn, folder, table, col_defs)
            print(f"  ✓ {n} rows")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            conn.rollback()

    conn.close()
    print("✅ All data ingested successfully.")


if __name__ == "__main__":
    ingest()
