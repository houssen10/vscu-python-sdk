from typing import Optional, Dict, Any


class ItemDTO:
    """Represents an individual line item on a fiscal Invoice or Credit Note."""

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        data = data or {}
        
        self.item_seq: int = data.get("itemSeq", 1)
        self.item_cd: str = data.get("itemCd", "")
        self.item_cls_cd: str = data.get("itemClsCd", "")
        self.item_nm: str = data.get("itemNm", "")
        self.bcd: Optional[str] = data.get("bcd")
        self.pkg_unit_cd: str = data.get("pkgUnitCd", "OU")
        self.pkg: float = float(data.get("pkg", 1.0))
        self.qty_unit_cd: str = data.get("qtyUnitCd", "U")
        self.qty: float = float(data.get("qty", 1.0))
        
        # Financial amounts
        self.prc: float = float(data.get("prc", 0.0))  # Unit price (tax inclusive)
        self.sply_amt: float = float(data.get("splyAmt", 0.0))  # Total supply amount (tax inclusive)
        self.dc_rt: float = float(data.get("dcRt", 0.0))  # Discount rate (%)
        self.dc_amt: float = float(data.get("dcAmt", 0.0))  # Discount amount
        
        # Insurance / excise fields
        self.isrcc_cd: Optional[str] = data.get("isrccCd")
        self.isrcc_nm: Optional[str] = data.get("isrccNm")
        self.isrc_rt: Optional[float] = data.get("isrcRt")
        self.isrc_amt: Optional[float] = data.get("isrcAmt")
        
        # Tax attributes
        self.tax_ty_cd: str = data.get("taxTyCd", "B")  # Default 16% Standard VAT
        self.taxbl_amt: float = float(data.get("taxblAmt", 0.0))  # Taxable amount (tax exclusive)
        self.tax_amt: float = float(data.get("taxAmt", 0.0))  # Tax amount
        self.tot_amt: float = float(data.get("totAmt", 0.0))  # Total amount (tax inclusive)

        # If price and qty are passed in initial dict and amounts aren't pre-calculated
        if "price" in data or ("prc" in data and self.tot_amt == 0.0):
            price = float(data.get("price", self.prc))
            tax_type = data.get("taxType", self.tax_ty_cd)
            self.calculate(price, self.qty, tax_type)

    def calculate(self, unit_price_inclusive: float, quantity: float, tax_type: str = "B") -> "ItemDTO":
        """
        Calculate taxable base and tax amount from tax-inclusive unit price and quantity.
        
        Tax Types:
          A: Exempt (0%)
          B: Standard Rate (16%)
          C: Zero Rated (0%)
          D: Non-VAT (0%)
          E: 8% Rate (Petroleum/Fuel)
        """
        self.prc = float(unit_price_inclusive)
        self.qty = float(quantity)
        self.tax_ty_cd = tax_type.upper()
        
        self.tot_amt = round(self.prc * self.qty, 2)
        self.sply_amt = self.tot_amt

        tax_rate = self.get_tax_rate(self.tax_ty_cd)
        
        # Back-calculate taxable base: Total / (1 + Rate / 100)
        self.taxbl_amt = round(self.tot_amt / (1.0 + (tax_rate / 100.0)), 2)
        self.tax_amt = round(self.tot_amt - self.taxbl_amt, 2)

        return self

    @staticmethod
    def get_tax_rate(tax_type: str) -> float:
        rates = {
            "B": 16.0,
            "E": 8.0,
            "A": 0.0,
            "C": 0.0,
            "D": 0.0,
        }
        return rates.get(tax_type.upper(), 0.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ItemDTO to dictionary with exact KRA eTIMS camelCase keys."""
        return {
            "itemSeq": self.item_seq,
            "itemCd": self.item_cd,
            "itemClsCd": self.item_cls_cd,
            "itemNm": self.item_nm,
            "bcd": self.bcd,
            "pkgUnitCd": self.pkg_unit_cd,
            "pkg": self.pkg,
            "qtyUnitCd": self.qty_unit_cd,
            "qty": self.qty,
            "prc": self.prc,
            "splyAmt": self.sply_amt,
            "dcRt": self.dc_rt,
            "dcAmt": self.dc_amt,
            "isrccCd": self.isrcc_cd,
            "isrccNm": self.isrcc_nm,
            "isrcRt": self.isrc_rt,
            "isrcAmt": self.isrc_amt,
            "taxTyCd": self.tax_ty_cd,
            "taxblAmt": self.taxbl_amt,
            "taxAmt": self.tax_amt,
            "totAmt": self.tot_amt,
        }
