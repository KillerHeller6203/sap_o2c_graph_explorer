from sqlalchemy import Column, String, Float, Integer, Text
from database import Base


class BusinessPartner(Base):
    __tablename__ = "business_partners"
    businessPartner = Column(String, primary_key=True, index=True)
    customer = Column(String, index=True)
    businessPartnerFullName = Column(String)
    businessPartnerName = Column(String)
    organizationBpName1 = Column(String)
    industry = Column(String)
    businessPartnerCategory = Column(String)
    creationDate = Column(String)
    isMarkedForArchiving = Column(String)


class BusinessPartnerAddress(Base):
    __tablename__ = "business_partner_addresses"
    businessPartner = Column(String, primary_key=True, index=True)
    cityName = Column(String)
    country = Column(String)
    region = Column(String)
    streetName = Column(String)
    postalCode = Column(String)


class Product(Base):
    __tablename__ = "products"
    product = Column(String, primary_key=True, index=True)
    productType = Column(String)
    productGroup = Column(String)
    baseUnit = Column(String)
    grossWeight = Column(Float, nullable=True)
    netWeight = Column(Float, nullable=True)
    division = Column(String)
    industrySector = Column(String)
    isMarkedForDeletion = Column(String)


class ProductDescription(Base):
    __tablename__ = "product_descriptions"
    product = Column(String, primary_key=True, index=True)
    language = Column(String, primary_key=True)
    productDescription = Column(String)


class Plant(Base):
    __tablename__ = "plants"
    plant = Column(String, primary_key=True, index=True)
    plantName = Column(String)
    salesOrganization = Column(String)
    distributionChannel = Column(String)
    division = Column(String)
    plantCategory = Column(String)


class SalesOrderHeader(Base):
    __tablename__ = "sales_order_headers"
    salesOrder = Column(String, primary_key=True, index=True)
    salesOrderType = Column(String)
    soldToParty = Column(String, index=True)
    creationDate = Column(String)
    totalNetAmount = Column(Float, nullable=True)
    transactionCurrency = Column(String)
    overallDeliveryStatus = Column(String)
    overallOrdReltdBillgStatus = Column(String)
    requestedDeliveryDate = Column(String)
    customerPaymentTerms = Column(String)
    salesOrganization = Column(String)


class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"
    salesOrder = Column(String, primary_key=True, index=True)
    salesOrderItem = Column(String, primary_key=True)
    material = Column(String, index=True)
    requestedQuantity = Column(Float, nullable=True)
    requestedQuantityUnit = Column(String)
    netAmount = Column(Float, nullable=True)
    transactionCurrency = Column(String)
    productionPlant = Column(String)
    storageLocation = Column(String)
    salesDocumentRjcnReason = Column(String)


class SalesOrderScheduleLine(Base):
    __tablename__ = "sales_order_schedule_lines"
    salesOrder = Column(String, primary_key=True, index=True)
    salesOrderItem = Column(String, primary_key=True)
    scheduleLineNumber = Column(String, primary_key=True)
    scheduledQuantity = Column(Float, nullable=True)
    requestedDeliveryDate = Column(String)
    confirmedDeliveryDate = Column(String)


class OutboundDeliveryHeader(Base):
    __tablename__ = "outbound_delivery_headers"
    deliveryDocument = Column(String, primary_key=True, index=True)
    shippingPoint = Column(String)
    actualGoodsMovementDate = Column(String)
    creationDate = Column(String)
    overallGoodsMovementStatus = Column(String)
    overallPickingStatus = Column(String)
    headerBillingBlockReason = Column(String)


class OutboundDeliveryItem(Base):
    __tablename__ = "outbound_delivery_items"
    deliveryDocument = Column(String, primary_key=True, index=True)
    deliveryDocumentItem = Column(String, primary_key=True)
    referenceSdDocument = Column(String, index=True)  # links to salesOrder
    referenceSdDocumentItem = Column(String)
    plant = Column(String, index=True)
    storageLocation = Column(String)
    actualDeliveryQuantity = Column(Float, nullable=True)
    deliveryQuantityUnit = Column(String)


class BillingDocumentHeader(Base):
    __tablename__ = "billing_document_headers"
    billingDocument = Column(String, primary_key=True, index=True)
    billingDocumentType = Column(String)
    soldToParty = Column(String, index=True)
    billingDocumentDate = Column(String)
    creationDate = Column(String)
    totalNetAmount = Column(Float, nullable=True)
    transactionCurrency = Column(String)
    companyCode = Column(String)
    fiscalYear = Column(String)
    accountingDocument = Column(String, index=True)
    billingDocumentIsCancelled = Column(String)


class BillingDocumentItem(Base):
    __tablename__ = "billing_document_items"
    billingDocument = Column(String, primary_key=True, index=True)
    billingDocumentItem = Column(String, primary_key=True)
    material = Column(String, index=True)
    billingQuantity = Column(Float, nullable=True)
    netAmount = Column(Float, nullable=True)
    transactionCurrency = Column(String)
    referenceSdDocument = Column(String, index=True)  # links to delivery
    referenceSdDocumentItem = Column(String)


class BillingDocumentCancellation(Base):
    __tablename__ = "billing_document_cancellations"
    billingDocument = Column(String, primary_key=True, index=True)
    cancelledBillingDocument = Column(String, index=True)
    cancellationDate = Column(String)
    companyCode = Column(String)


class JournalEntryItem(Base):
    __tablename__ = "journal_entry_items"
    companyCode = Column(String, primary_key=True)
    fiscalYear = Column(String, primary_key=True)
    accountingDocument = Column(String, primary_key=True, index=True)
    accountingDocumentItem = Column(String, primary_key=True)
    referenceDocument = Column(String, index=True)  # links to billingDocument
    customer = Column(String, index=True)
    glAccount = Column(String)
    amountInTransactionCurrency = Column(Float, nullable=True)
    transactionCurrency = Column(String)
    postingDate = Column(String)
    clearingDate = Column(String)
    clearingAccountingDocument = Column(String)
    financialAccountType = Column(String)
    profitCenter = Column(String)


class PaymentAccountsReceivable(Base):
    __tablename__ = "payments_accounts_receivable"
    companyCode = Column(String, primary_key=True)
    fiscalYear = Column(String, primary_key=True)
    accountingDocument = Column(String, primary_key=True, index=True)
    accountingDocumentItem = Column(String, primary_key=True)
    customer = Column(String, index=True)
    invoiceReference = Column(String, index=True)  # links to billingDocument accounting doc
    salesDocument = Column(String, index=True)
    amountInTransactionCurrency = Column(Float, nullable=True)
    transactionCurrency = Column(String)
    clearingDate = Column(String)
    postingDate = Column(String)


class CustomerCompanyAssignment(Base):
    __tablename__ = "customer_company_assignments"
    customer = Column(String, primary_key=True, index=True)
    companyCode = Column(String, primary_key=True)
    accountingClerk = Column(String)
    accountingClerkFaxNumber = Column(String)
    alternativePayerAccount = Column(String)
    paymentBlockingReason = Column(String)
    paymentMethodsList = Column(String)
    paymentTerms = Column(String)
    reconciliationAccount = Column(String)
    deletionIndicator = Column(String)
    customerAccountGroup = Column(String)


class CustomerSalesAreaAssignment(Base):
    __tablename__ = "customer_sales_area_assignments"
    customer = Column(String, primary_key=True, index=True)
    salesOrganization = Column(String, primary_key=True)
    distributionChannel = Column(String, primary_key=True)
    division = Column(String, primary_key=True)
    billingIsBlockedForCustomer = Column(String)
    supplyingPlant = Column(String)
    salesDistrict = Column(String)
    exchangeRateType = Column(String)
    salesOffice = Column(String)
    shippingCondition = Column(String)


class ProductPlant(Base):
    __tablename__ = "product_plants"
    product = Column(String, primary_key=True, index=True)
    plant = Column(String, primary_key=True, index=True)
    countryOfOrigin = Column(String)
    regionOfOrigin = Column(String)
    productionInvtryManagedLoc = Column(String)
    availabilityCheckType = Column(String)
    fiscalYearVariant = Column(String)
    profitCenter = Column(String)
    mrpType = Column(String)


class ProductStorageLocation(Base):
    __tablename__ = "product_storage_locations"
    product = Column(String, primary_key=True, index=True)
    plant = Column(String, primary_key=True, index=True)
    storageLocation = Column(String, primary_key=True)
    physicalInventoryBlockInd = Column(String)
    dateOfLastPostedCntUnRstrcdStk = Column(String)
