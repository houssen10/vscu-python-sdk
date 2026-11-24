# VSCU Python SDK

A comprehensive Python SDK for integrating with the **KRA eTIMS VSCU (Virtual Sales Control Unit)** REST API. This SDK provides strongly typed DTOs, automated VAT tax back-calculations, Credit Note validation, Cloudflare Access support, and ready-to-use ERPNext/Frappe hooks.

---

## Features

- **Automated Tax Calculation**: Calculates taxable base amounts (`taxblAmt`) and tax amounts (`taxAmt`) from tax-inclusive prices across all 5 KRA tax types.
- **Credit Note Validation**: Inherits full invoice structure while enforcing KRA credit note rules (`rcptTyCd = 'R'`, mandatory `orgInvcNo`, `rfdDt`, `rfdRsnCd`).
- **Cloudflare Access Support**: Seamlessly authenticates through Cloudflare Tunnels using `CF-Access-Client-Id` and `CF-Access-Client-Secret` headers.
- **Native ERPNext Connector**: Includes `ERPNextVscuConnector` to map Frappe / ERPNext `Sales Invoice` documents to eTIMS payloads with a single call.

---

## Installation

Install via pip or from source:

```bash
git clone https://github.com/ongudidan/vscu-python-sdk.git
cd vscu-python-sdk
pip install -e .
```

---

## Quickstart

### 1. Initialize Client

```python
from vscu_sdk import Vscu

vscu = Vscu({
    "base_url": "http://your-vscu-server:8088/",  # VSCU Middleware Base URL
    "timeout": 30.0,
    # Optional: if VSCU is behind a Cloudflare Tunnel
    "cf_access_client_id": "your-cf-client-id",
    "cf_access_client_secret": "your-cf-client-secret",
})
```

---

### 2. Fiscalizing a Sales Invoice

```python
from vscu_sdk import InvoiceDTO

# 1. Create Invoice
invoice = InvoiceDTO()
invoice.tin = "P051234567M"          # Company KRA PIN
invoice.bhf_id = "00"                 # Branch ID
invoice.trd_invc_no = "INV-1001"      # Internal Invoice Number
invoice.invc_no = 1001                # Sequential Fiscal Number
invoice.regr_nm = "Admin"
invoice.modr_nm = "Admin"

# 2. Set Customer (Optional for B2C, required for B2B)
invoice.customer(tin_or_dict="P098765432Z", name="Customer Name Ltd")

# 3. Add Items (Taxes and line totals are calculated automatically from inclusive price)
invoice.add_item({
    "itemCd": "KE2OUU00000000000001",
    "itemClsCd": "50131702",          # KRA HS / Commodity Code
    "itemNm": "Fresh Milk 500ml",
    "price": 60.00,                   # Inclusive of tax
    "qty": 2.0,
    "taxType": "B",                   # 16% Standard VAT
})

invoice.add_item({
    "itemCd": "KE2OUU00000000000002",
    "itemClsCd": "50161509",
    "itemNm": "Sugar 1kg",
    "price": 150.00,
    "qty": 1.0,
    "taxType": "B",
})

# 4. Calculate All Totals and per-tax buckets
invoice.calculate_totals()

# 5. Send to VSCU
try:
    response = vscu.sales().save_sales(invoice.to_dict())
    print("Fiscal Response:", response)
    # response['data']['rcptSign'] -> KRA Fiscal Signature
    # response['data']['qrCodeUrl'] -> KRA Verification URL
except Exception as e:
    print(f"eTIMS Error: {e}")
```

---

### 3. Fiscalizing a Credit Note (Refund)

> **Important KRA Rules for Credit Notes:**
> 1. `invc_no` must share the same serial sequence counter as standard sales invoices.
> 2. `org_invc_no` must reference the original fiscal invoice receipt number.
> 3. `rfd_rsn_cd` and `rfd_dt` are mandatory.

```python
from vscu_sdk import CreditNoteDTO

credit_note = CreditNoteDTO()
credit_note.tin = "P051234567M"
credit_note.bhf_id = "00"
credit_note.org_invc_no = "KRACU0300010006/5"  # Original KRA Fiscal Invoice Number
credit_note.trd_invc_no = "CN-2024-0001"
credit_note.invc_no = 1005                     # Shared counter

credit_note.rfd_dt = "20261124"               # Refund Date (YYYYMMDD)
credit_note.rfd_rsn_cd = "01"                  # 01: Sales Return, 02: Post-sale discount

credit_note.add_item({
    "itemCd": "KE2OUU00000000000001",
    "itemClsCd": "50131702",
    "itemNm": "Fresh Milk 500ml",
    "price": 60.00,
    "qty": 1.0,
    "taxType": "B",
})

credit_note.calculate_totals()

response = vscu.sales().save_credit_note(credit_note.to_dict())
```

---

## ERPNext Integration

The SDK includes a built-in `ERPNextVscuConnector` that transforms ERPNext `Sales Invoice` documents into compliant eTIMS DTOs.

### In your Frappe App / Server Script:

```python
import frappe
from vscu_sdk import Vscu, ERPNextVscuConnector

def fiscalize_on_submit(doc, method):
    """Triggered on Sales Invoice submit."""
    # 1. Initialize client with ERPNext settings
    settings = frappe.get_single("KRA eTIMS Settings")
    client = Vscu({
        "base_url": settings.vscu_url,
        "cf_access_client_id": settings.get_password("cf_client_id"),
        "cf_access_client_secret": settings.get_password("cf_client_secret"),
    })

    connector = ERPNextVscuConnector(client)

    # 2. Fiscalize invoice
    response = connector.fiscalize_invoice(
        doc=doc,
        company_pin=frappe.db.get_value("Company", doc.company, "tax_id"),
        fiscal_seq_no=frappe.db.get_value("KRA Sequence", None, "next_value")
    )

    # 3. Save KRA fiscal details to ERPNext document
    if response.get("resultCd") == "000":
        data = response.get("data", {})
        doc.db_set({
            "custom_kra_sdc_id": data.get("sdcId"),
            "custom_kra_rcpt_sign": data.get("rcptSign"),
            "custom_kra_qr_code": data.get("qrCodeUrl"),
            "custom_kra_fiscal_status": "Fiscalized",
        })
```

---

## Tax Types Guide

| Tax Type | Description | Rate | Usage |
| :---: | :--- | :---: | :--- |
| **A** | Exempt | 0% | Items specifically exempt from VAT |
| **B** | Standard Rate | 16% | Most taxable goods and services |
| **C** | Zero Rated | 0% | Exports, certain zero-rated food products |
| **D** | Non-VAT | 0% | Items completely outside the scope of VAT |
| **E** | Petroleum / Fuel | 8% | Petroleum and fuel products |

---

## Available Resources

- `vscu.sales()`:
  - `save_sales(data)`: Submit invoice
  - `save_credit_note(data)`: Submit credit note / refund
  - `select_invoice_details(query)`: Lookup invoice by fiscal number
  - `select_items(query)`: Query cached items
  - `select_customer(query)`: Lookup customer tax info
- `vscu.items()`:
  - `save_item(data)`: Register / update item in eTIMS
  - `get_item_list(query)`: List registered items
  - `get_item_cls_list(query)`: List KRA HS classifications
  - `select_code_list(query)`: List KRA reference codes
- `vscu.customers()`:
  - `select_customer(query)`: Verify customer PIN

---

## License

MIT License. Copyright (c) 2026 ongudidan.
