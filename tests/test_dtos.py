import unittest
from vscu_sdk.dtos.invoice import InvoiceDTO
from vscu_sdk.dtos.credit_note import CreditNoteDTO
from vscu_sdk.dtos.item import ItemDTO
from vscu_sdk.erpnext.connector import ERPNextVscuConnector
from vscu_sdk.client import Vscu


class TestVscuDtos(unittest.TestCase):

    def test_item_tax_calculation_standard_vat_16(self):
        """Test item calculation for 16% standard VAT (Type B)."""
        item = ItemDTO()
        # Price 116 inclusive, qty 1 -> taxable base should be 100.0, tax should be 16.0
        item.calculate(unit_price_inclusive=116.0, quantity=1.0, tax_type="B")
        
        self.assertEqual(item.tot_amt, 116.0)
        self.assertEqual(item.sply_amt, 116.0)
        self.assertEqual(item.taxbl_amt, 100.0)
        self.assertEqual(item.tax_amt, 16.0)
        self.assertEqual(item.tax_ty_cd, "B")

    def test_item_tax_calculation_petroleum_8(self):
        """Test item calculation for 8% petroleum VAT (Type E)."""
        item = ItemDTO()
        # Price 108 inclusive, qty 1 -> taxable base should be 100.0, tax should be 8.0
        item.calculate(unit_price_inclusive=108.0, quantity=1.0, tax_type="E")
        
        self.assertEqual(item.tot_amt, 108.0)
        self.assertEqual(item.taxbl_amt, 100.0)
        self.assertEqual(item.tax_amt, 8.0)
        self.assertEqual(item.tax_ty_cd, "E")

    def test_item_tax_calculation_exempt_and_zero(self):
        """Test exempt (A) and zero-rated (C) tax types."""
        item_a = ItemDTO()
        item_a.calculate(unit_price_inclusive=50.0, quantity=2.0, tax_type="A")
        self.assertEqual(item_a.tot_amt, 100.0)
        self.assertEqual(item_a.taxbl_amt, 100.0)
        self.assertEqual(item_a.tax_amt, 0.0)

        item_c = ItemDTO()
        item_c.calculate(unit_price_inclusive=250.0, quantity=1.0, tax_type="C")
        self.assertEqual(item_c.tot_amt, 250.0)
        self.assertEqual(item_c.taxbl_amt, 250.0)
        self.assertEqual(item_c.tax_amt, 0.0)

    def test_invoice_totals_aggregation(self):
        """Test Invoice totals aggregation across mixed tax types."""
        invoice = InvoiceDTO()
        invoice.tin = "P051234567M"
        invoice.bhf_id = "00"
        invoice.invc_no = 1001
        invoice.trd_invc_no = "INV-1001"
        invoice.customer(tin_or_dict="P098765432Z", name="Test Customer Ltd")

        # Item 1: Standard 16% (Fresh Milk)
        invoice.add_item({
            "itemCd": "KE2OUU00000000000001",
            "itemClsCd": "50131702",
            "itemNm": "Fresh Milk 500ml",
            "price": 60.0,
            "qty": 2.0,
            "taxType": "B",
        })

        # Item 2: Standard 16% (Sugar)
        invoice.add_item({
            "itemCd": "KE2OUU00000000000002",
            "itemClsCd": "50161509",
            "itemNm": "Sugar 1kg",
            "price": 150.0,
            "qty": 1.0,
            "taxType": "B",
        })

        invoice.calculate_totals()
        data = invoice.to_dict()

        self.assertEqual(data["totItemCnt"], 2)
        self.assertEqual(data["totAmt"], 270.0)
        self.assertEqual(data["rcptTyCd"], "S")
        self.assertEqual(data["custTin"], "P098765432Z")
        self.assertEqual(data["receipt"]["custNm"], "Test Customer Ltd")
        self.assertGreater(data["totTaxAmt"], 0.0)
        self.assertEqual(round(data["totTaxblAmt"] + data["totTaxAmt"], 2), 270.0)

    def test_credit_note_receipt_type(self):
        """Test Credit Note sets receipt type to 'R' and holds refund references."""
        credit_note = CreditNoteDTO()
        credit_note.tin = "P051234567M"
        credit_note.bhf_id = "00"
        credit_note.org_invc_no = "KRACU0300010006/5"
        credit_note.invc_no = 1002
        credit_note.trd_invc_no = "CN-1002"
        credit_note.rfd_rsn_cd = "01"
        credit_note.rfd_dt = "20261124"

        credit_note.add_item({
            "itemCd": "KE2OUU00000000000001",
            "itemClsCd": "50131702",
            "itemNm": "Fresh Milk 500ml",
            "price": 60.0,
            "qty": 1.0,
            "taxType": "B",
        })
        credit_note.calculate_totals()
        data = credit_note.to_dict()

        self.assertEqual(data["rcptTyCd"], "R")
        self.assertEqual(data["orgInvcNo"], "KRACU0300010006/5")
        self.assertEqual(data["rfdRsnCd"], "01")
        self.assertEqual(data["totAmt"], 60.0)

    def test_erpnext_connector_mapping(self):
        """Test ERPNext connector maps a sample Sales Invoice dict correctly."""
        client = Vscu({"base_url": "http://127.0.0.1:8088/"})
        connector = ERPNextVscuConnector(client)

        sample_erpnext_doc = {
            "name": "ACC-SINV-2026-00042",
            "is_return": 0,
            "posting_date": "2026-11-24",
            "customer": "Apex Enterprises",
            "customer_name": "Apex Enterprises Ltd",
            "tax_id": "P052999888X",
            "mode_of_payment": "M-Pesa",
            "items": [
                {
                    "item_code": "PROD-MILK-500",
                    "item_name": "Fresh Pasteurized Milk 500ml",
                    "qty": 10,
                    "rate": 65.0,
                    "tax_rate": 16.0,
                    "custom_kra_hs_code": "50131702",
                }
            ]
        }

        dto = connector.build_dto_from_sales_invoice(
            doc=sample_erpnext_doc,
            company_pin="P051000111A",
            fiscal_seq_no=501
        )

        data = dto.to_dict()
        self.assertEqual(data["tin"], "P051000111A")
        self.assertEqual(data["trdInvcNo"], "ACC-SINV-2026-00042")
        self.assertEqual(data["invcNo"], 501)
        self.assertEqual(data["pmtTyCd"], "03")  # M-Pesa mapped to 03
        self.assertEqual(data["custTin"], "P052999888X")
        self.assertEqual(data["totItemCnt"], 1)
        self.assertEqual(data["totAmt"], 650.0)


if __name__ == "__main__":
    unittest.main()
