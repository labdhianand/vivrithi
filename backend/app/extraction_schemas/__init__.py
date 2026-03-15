from .alm import ALM_DEFAULT_SCHEMA
from .annual_report import ANNUAL_REPORT_DEFAULT_SCHEMA
from .bank_statement import BANK_STATEMENT_DEFAULT_SCHEMA
from .borrowing import BORROWING_DEFAULT_SCHEMA
from .financials import FINANCIALS_DEFAULT_SCHEMA
from .gst_returns import GST_RETURNS_DEFAULT_SCHEMA
from .itr import ITR_DEFAULT_SCHEMA
from .shareholding import SHAREHOLDING_DEFAULT_SCHEMA

DEFAULT_SCHEMAS = {
    "ALM": ALM_DEFAULT_SCHEMA,
    "Annual_Report": ANNUAL_REPORT_DEFAULT_SCHEMA,
    "Bank_Statement": BANK_STATEMENT_DEFAULT_SCHEMA,
    "Borrowing_Profile": BORROWING_DEFAULT_SCHEMA,
    "GST_Returns": GST_RETURNS_DEFAULT_SCHEMA,
    "ITR": ITR_DEFAULT_SCHEMA,
    "Portfolio_Performance": FINANCIALS_DEFAULT_SCHEMA,
    "Shareholding_Pattern": SHAREHOLDING_DEFAULT_SCHEMA,
}
