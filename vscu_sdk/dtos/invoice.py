from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from .item import ItemDTO


class InvoiceDTO:
    """Represents a standard Sales Invoice payload for KRA eTIMS VSCU."""

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        data = data or {}
        now = datetime.now()
        
        self.tin: str = data.get("tin", "")
        self.bhf_id: str = data.get("bhfId", "00")
        self.trd_invc_no: str = str(data.get("trdInvcNo", ""))
        self.invc_no: int = int(data.get("invcNo", 1))
        self.org_invc_no: str = str(data.get("orgInvcNo", "0"))
        
        self.cust_tin: Optional[str] = data.get("custTin")
        self.cust_nm: Optional[str] = data.get("custNm")
        
        self.sales_ty_cd: str = data.get("salesTyCd", "N")  # N: Normal, C: Copy, etc.
        self.rcpt_ty_cd: str = data.get("rcptTyCd", "S")    # S: Sale, R: Refund (Credit Note)
        self.pmt_ty_cd: str = data.get("pmtTyCd", "01")     # 01: Cash, 02: Credit, 03: Mobile Money
        self.sales_stts_cd: str = data.get("salesSttsCd", "02")  # 02: Approved
        
        # Date & timestamps (Defaults to current time if not provided)
        self.sales_dt: str = data.get("salesDt", now.strftime("%Y%m%d"))
        self.cfm_dt: str = data.get("cfmDt", now.strftime("%Y%m%d%H%M%S"))
        self.stock_rls_dt: str = data.get("stockRlsDt", now.strftime("%Y%m%d%H%M%S"))
        
        # Cancellation / Refund dates
        self.cncl_req_dt: Optional[str] = data.get("cnclReqDt")
        self.cncl_dt: Optional[str] = data.get("cnclDt")
        self.rfd_dt: Optional[str] = data.get("rfdDt")
        self.rfd_rsn_cd: Optional[str] = data.get("rfdRsnCd")
        
        # Counts and aggregated totals
        self.tot_item_cnt: int = 0
        
        # Taxable amounts per tax group
        self.taxbl_amt_a: float = 0.0
        self.taxbl_amt_b: float = 0.0
        self.taxbl_amt_c: float = 0.0
        self.taxbl_amt_d: float = 0.0
        self.taxbl_amt_e: float = 0.0
        
        # Tax rates (%)
        self.tax_rt_a: float = 0.0
        self.tax_rt_b: float = 16.0
        self.tax_rt_c: float = 0.0
        self.tax_rt_d: float = 0.0
        self.tax_rt_e: float = 8.0
        
        # Tax amounts per tax group
        self.tax_amt_a: float = 0.0
        self.tax_amt_b: float = 0.0
        self.tax_amt_c: float = 0.0
        self.tax_amt_d: float = 0.0
        self.tax_amt_e: float = 0.0
        
        # Overall totals
        self.tot_taxbl_amt: float = 0.0
        self.tot_tax_amt: float = 0.0
        self.tot_amt: float = 0.0
        
        self.prchr_acptc_yn: str = data.get("prchrAcptcYn", "N")
        self.remark: Optional[str] = data.get("remark")
        
        self.regr_id: str = data.get("regrId", "Admin")
        self.regr_nm: str = data.get("regrNm", "Admin")
        self.modr_id: str = data.get("modrId", "Admin")
        self.modr_nm: str = data.get("modrNm", "Admin")
        
        self.item_list: List[ItemDTO] = []
        
        self.receipt: Dict[str, Any] = {
            "custTin": self.cust_tin,
            "custNm": self.cust_nm,
            "custMblNo": data.get("custMblNo"),
            "rptNo": data.get("rptNo", 0),
            "trdeNm": data.get("trdeNm", ""),
            "adrs": data.get("adrs", ""),
            "topMsg": data.get("topMsg", ""),
            "btmMsg": data.get("btmMsg", ""),
            "prchrAcptcYn": self.prchr_acptc_yn,
        }

    def customer(self, tin_or_dict: Union[str, Dict[str, Any], None] = None, name: Optional[str] = None) -> "InvoiceDTO":
        """Set customer tax ID (PIN) and Name."""
        if isinstance(tin_or_dict, dict):
            self.cust_tin = tin_or_dict.get("tin") or tin_or_dict.get("custTin")
            self.cust_nm = tin_or_dict.get("nm") or tin_or_dict.get("custNm") or tin_or_dict.get("name")
        else:
            self.cust_tin = tin_or_dict
            if name:
                self.cust_nm = name

        self.receipt["custTin"] = self.cust_tin
        self.receipt["custNm"] = self.cust_nm
        return self

    def add_item(self, data: Union[ItemDTO, Dict[str, Any]]) -> ItemDTO:
        """Add an item line to the invoice with automatic sequence assignment."""
        if isinstance(data, ItemDTO):
            item = data
            item.item_seq = len(self.item_list) + 1
        else:
            item = ItemDTO()
            item.item_seq = len(self.item_list) + 1
            item.item_cd = data.get("itemCd", "")
            item.item_cls_cd = data.get("itemClsCd", "")
            item.item_nm = data.get("itemNm", "")
            item.pkg_unit_cd = data.get("pkgUnitCd", "OU")
            item.pkg = float(data.get("pkg", 1.0))
            item.qty_unit_cd = data.get("qtyUnitCd", "U")
            if "bcd" in data:
                item.bcd = data["bcd"]
            
            item.calculate(
                unit_price_inclusive=float(data.get("price", 0.0)),
                quantity=float(data.get("qty", 1.0)),
                tax_type=data.get("taxType", "B")
            )

        self.item_list.append(item)
        return item

    def calculate_totals(self) -> "InvoiceDTO":
        """Calculate overall and per-tax category totals from item list."""
        self.tot_item_cnt = len(self.item_list)
        self.tot_taxbl_amt = 0.0
        self.tot_tax_amt = 0.0
        self.tot_amt = 0.0

        # Reset per-tax totals
        self.taxbl_amt_a = self.taxbl_amt_b = self.taxbl_amt_c = self.taxbl_amt_d = self.taxbl_amt_e = 0.0
        self.tax_amt_a = self.tax_amt_b = self.tax_amt_c = self.tax_amt_d = self.tax_amt_e = 0.0

        for item in self.item_list:
            self.tot_taxbl_amt += item.taxbl_amt
            self.tot_tax_amt += item.tax_amt
            self.tot_amt += item.tot_amt

            tax_ty = item.tax_ty_cd.upper()
            if tax_ty == "A":
                self.taxbl_amt_a += item.taxbl_amt
                self.tax_amt_a += item.tax_amt
            elif tax_ty == "B":
                self.taxbl_amt_b += item.taxbl_amt
                self.tax_amt_b += item.tax_amt
            elif tax_ty == "C":
                self.taxbl_amt_c += item.taxbl_amt
                self.tax_amt_c += item.tax_amt
            elif tax_ty == "D":
                self.taxbl_amt_d += item.taxbl_amt
                self.tax_amt_d += item.tax_amt
            elif tax_ty == "E":
                self.taxbl_amt_e += item.taxbl_amt
                self.tax_amt_e += item.tax_amt

        # Round all aggregates to 2 decimal places
        self.tot_taxbl_amt = round(self.tot_taxbl_amt, 2)
        self.tot_tax_amt = round(self.tot_tax_amt, 2)
        self.tot_amt = round(self.tot_amt, 2)

        self.taxbl_amt_a = round(self.taxbl_amt_a, 2)
        self.taxbl_amt_b = round(self.taxbl_amt_b, 2)
        self.taxbl_amt_c = round(self.taxbl_amt_c, 2)
        self.taxbl_amt_d = round(self.taxbl_amt_d, 2)
        self.taxbl_amt_e = round(self.taxbl_amt_e, 2)

        self.tax_amt_a = round(self.tax_amt_a, 2)
        self.tax_amt_b = round(self.tax_amt_b, 2)
        self.tax_amt_c = round(self.tax_amt_c, 2)
        self.tax_amt_d = round(self.tax_amt_d, 2)
        self.tax_amt_e = round(self.tax_amt_e, 2)

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Serialize InvoiceDTO to dictionary matching KRA VSCU saveSales schema."""
        self.receipt["custTin"] = self.cust_tin
        self.receipt["custNm"] = self.cust_nm

        return {
            "tin": self.tin,
            "bhfId": self.bhf_id,
            "trdInvcNo": self.trd_invc_no,
            "invcNo": self.invc_no,
            "orgInvcNo": self.org_invc_no,
            "custTin": self.cust_tin,
            "custNm": self.cust_nm,
            "salesTyCd": self.sales_ty_cd,
            "rcptTyCd": self.rcpt_ty_cd,
            "pmtTyCd": self.pmt_ty_cd,
            "salesSttsCd": self.sales_stts_cd,
            "cfmDt": self.cfm_dt,
            "salesDt": self.sales_dt,
            "stockRlsDt": self.stock_rls_dt,
            "cnclReqDt": self.cncl_req_dt,
            "cnclDt": self.cncl_dt,
            "rfdDt": self.rfd_dt,
            "rfdRsnCd": self.rfd_rsn_cd,
            "totItemCnt": self.tot_item_cnt,
            "taxblAmtA": self.taxbl_amt_a,
            "taxblAmtB": self.taxbl_amt_b,
            "taxblAmtC": self.taxbl_amt_c,
            "taxblAmtD": self.taxbl_amt_d,
            "taxblAmtE": self.taxbl_amt_e,
            "taxRtA": self.tax_rt_a,
            "taxRtB": self.tax_rt_b,
            "taxRtC": self.tax_rt_c,
            "taxRtD": self.tax_rt_d,
            "taxRtE": self.tax_rt_e,
            "taxAmtA": self.tax_amt_a,
            "taxAmtB": self.tax_amt_b,
            "taxAmtC": self.tax_amt_c,
            "taxAmtD": self.tax_amt_d,
            "taxAmtE": self.tax_amt_e,
            "totTaxblAmt": self.tot_taxbl_amt,
            "totTaxAmt": self.tot_tax_amt,
            "totAmt": self.tot_amt,
            "prchrAcptcYn": self.prchr_acptc_yn,
            "remark": self.remark,
            "regrId": self.regr_id,
            "regrNm": self.regr_nm,
            "modrId": self.modr_id,
            "modrNm": self.modr_nm,
            "receipt": self.receipt,
            "itemList": [item.to_dict() for item in self.item_list],
        }
