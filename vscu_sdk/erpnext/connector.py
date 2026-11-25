"""
ERPNext Connector for KRA eTIMS VSCU
------------------------------------
Provides seamless mapping between ERPNext Sales Invoice / Credit Note DocTypes
and the VSCU DTOs, enabling 1-click fiscalization on invoice submission.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from ..client import Vscu
from ..dtos.invoice import InvoiceDTO
from ..dtos.credit_note import CreditNoteDTO


class ERPNextVscuConnector:
    """Helper to convert ERPNext Sales Invoice documents into eTIMS payloads."""

    def __init__(self, vscu_client: Vscu, default_bhf_id: str = "00"):
        self.client = vscu_client
        self.default_bhf_id = default_bhf_id

    def build_dto_from_sales_invoice(
        self,
        doc: Any,
        company_pin: str,
        bhf_id: Optional[str] = None,
        fiscal_seq_no: Optional[int] = None,
        regr_name: str = "Administrator"
    ) -> InvoiceDTO:
        """
        Convert an ERPNext Sales Invoice document (or dict) into an InvoiceDTO or CreditNoteDTO.

        :param doc: Frappe Sales Invoice document or dict
        :param company_pin: Seller's KRA PIN (e.g. P051...)
        :param bhf_id: Branch ID (defaults to '00')
        :param fiscal_seq_no: Sequential invoice number (invcNo)
        :param regr_name: Submitting user name
        """
        is_dict = isinstance(doc, dict)

        def get_val(key: str, default: Any = None) -> Any:
            return doc.get(key, default) if is_dict else getattr(doc, key, default)

        is_return = bool(get_val("is_return", False))
        posting_date = get_val("posting_date")
        posting_time = get_val("posting_time")

        # Parse date and datetime
        if isinstance(posting_date, str):
            sales_dt = posting_date.replace("-", "")
        elif hasattr(posting_date, "strftime"):
            sales_dt = posting_date.strftime("%Y%m%d")
        else:
            sales_dt = datetime.now().strftime("%Y%m%d")

        now_str = datetime.now().strftime("%Y%m%d%H%M%S")

        # Instantiate appropriate DTO (Invoice vs Credit Note)
        dto_class = CreditNoteDTO if is_return else InvoiceDTO
        dto = dto_class()

        dto.tin = company_pin
        dto.bhf_id = bhf_id or get_val("custom_kra_bhf_id") or self.default_bhf_id
        dto.trd_invc_no = str(get_val("name", ""))
        dto.invc_no = int(fiscal_seq_no or get_val("custom_kra_invc_no") or 1)

        dto.sales_dt = sales_dt
        dto.cfm_dt = now_str
        dto.stock_rls_dt = now_str
        dto.regr_nm = regr_name
        dto.modr_nm = regr_name

        # Customer details
        cust_pin = get_val("tax_id") or get_val("custom_kra_pin")
        cust_name = get_val("customer_name") or get_val("customer")
        dto.customer(tin_or_dict=cust_pin, name=cust_name)

        # Payment Type mapping:
        # 01: Cash, 02: Credit, 03: Mobile Money (M-Pesa), 04: Bank
        mop = str(get_val("mode_of_payment", "") or "").lower()
        if not mop:
            payments = get_val("payments", []) or []
            for p in payments:
                p_amt = p.get("amount", 0) if isinstance(p, dict) else getattr(p, "amount", 0)
                if float(p_amt or 0) > 0:
                    p_mop = p.get("mode_of_payment", "") if isinstance(p, dict) else getattr(p, "mode_of_payment", "")
                    if p_mop:
                        mop = str(p_mop).lower()
                        break

        if "mpesa" in mop or "m-pesa" in mop or "mobile" in mop:
            dto.pmt_ty_cd = "03"
        elif "bank" in mop or "card" in mop or "eft" in mop or "rtgs" in mop:
            dto.pmt_ty_cd = "04"
        elif "credit" in mop or float(get_val("outstanding_amount", 0) or 0) > 0:
            dto.pmt_ty_cd = "02"
        else:
            dto.pmt_ty_cd = "01"

        # Handle Credit Note specific fields
        if is_return:
            dto.org_invc_no = str(get_val("custom_kra_org_invc_no") or get_val("return_against") or "0")
            dto.rfd_dt = sales_dt
            dto.rfd_rsn_cd = str(get_val("custom_kra_refund_reason") or "01")  # 01: Sales Return

        # Process Items
        items = get_val("items", [])
        for item_row in items:
            def get_item_val(k: str, default: Any = None) -> Any:
                return item_row.get(k, default) if isinstance(item_row, dict) else getattr(item_row, k, default)

            # Determine KRA Tax Type: explicit custom_kra_tax_type takes precedence
            explicit_tax = str(get_item_val("custom_kra_tax_type") or "").strip().upper()
            if explicit_tax in ("A", "B", "C", "D", "E"):
                tax_type = explicit_tax
            else:
                tax_rate = float(get_item_val("tax_rate", 16.0) or 16.0)
                item_tax_template = str(get_item_val("item_tax_template", "") or "").lower()

                if "exempt" in item_tax_template:
                    tax_type = "A"
                elif "zero" in item_tax_template:
                    tax_type = "C"
                elif "non-vat" in item_tax_template or "non vat" in item_tax_template:
                    tax_type = "D"
                elif "8%" in item_tax_template or "8 %" in item_tax_template or tax_rate == 8.0:
                    tax_type = "E"
                elif tax_rate == 0.0:
                    tax_type = "D"
                else:
                    tax_type = "B"  # Default 16% standard VAT

            qty = abs(float(get_item_val("qty", 1.0)))
            rate = abs(float(get_item_val("rate", 0.0)))

            dto.add_item({
                "itemCd": str(get_item_val("custom_kra_item_cd") or get_item_val("item_code", "")),
                "itemClsCd": str(get_item_val("custom_kra_hs_code") or get_item_val("custom_item_classification") or "50131702"),
                "itemNm": str(get_item_val("item_name") or get_item_val("item_code")),
                "price": rate,
                "qty": qty,
                "taxType": tax_type,
                "pkgUnitCd": str(get_item_val("custom_kra_pkg_unit") or "NT"),
                "qtyUnitCd": str(get_item_val("custom_kra_qty_unit") or "U"),
            })

        dto.calculate_totals()
        return dto

    def fiscalize_invoice(
        self,
        doc: Any,
        company_pin: str,
        bhf_id: Optional[str] = None,
        fiscal_seq_no: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Builds the DTO, sends it to VSCU, and returns the response containing KRA signatures.
        """
        dto = self.build_dto_from_sales_invoice(
            doc=doc,
            company_pin=company_pin,
            bhf_id=bhf_id,
            fiscal_seq_no=fiscal_seq_no
        )

        payload = dto.to_dict()
        if dto.rcpt_ty_cd == "R":
            response = self.client.sales().save_credit_note(payload)
        else:
            response = self.client.sales().save_sales(payload)

        return response
