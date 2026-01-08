from typing import Optional

from pydantic import BaseModel, Field


class IncomeStatementData(BaseModel):
    revenue: Optional[float] = Field(None, description="Total revenue or net sales.")
    gross_profit: Optional[float] = Field(
        None, description="Gross profit (Revenue minus Cost of Goods Sold)."
    )
    sga_expenses: Optional[float] = Field(
        None, description="Selling, General, and Administrative expenses."
    )
    rd_expenses: Optional[float] = Field(
        None, description="Research and Development expenses."
    )
    depreciation_and_amortization: Optional[float] = Field(
        None,
        description="Depreciation and amortization expense (often found in Operating Expenses or Cash Flow).",
    )
    operating_income: Optional[float] = Field(
        None, description="Operating Income or EBIT."
    )
    interest_expense: Optional[float] = Field(None, description="Interest expense.")
    net_income: Optional[float] = Field(None, description="Net earnings or Net income.")
    eps_diluted: Optional[float] = Field(
        None, description="Diluted Earnings Per Share."
    )
    weighted_average_shares: Optional[float] = Field(
        None, description="Weighted average shares outstanding (diluted)."
    )


class BalanceSheetData(BaseModel):
    current_assets: Optional[float] = Field(None, description="Total current assets.")
    current_liabilities: Optional[float] = Field(
        None, description="Total current liabilities."
    )
    net_receivables: Optional[float] = Field(
        None, description="Net accounts receivable."
    )
    total_assets: Optional[float] = Field(None, description="Total assets.")
    short_term_debt: Optional[float] = Field(
        None, description="Short-term debt plus current portion of long-term debt."
    )
    long_term_debt: Optional[float] = Field(
        None, description="Long-term debt (excluding current portion)."
    )
    total_liabilities: Optional[float] = Field(None, description="Total liabilities.")
    total_equity: Optional[float] = Field(
        None, description="Total shareholders' equity."
    )
    treasury_stock: Optional[float] = Field(
        None,
        description="Treasury stock (usually a negative number in equity section, extract absolute value if possible).",
    )


class CashFlowData(BaseModel):
    capital_expenditures: Optional[float] = Field(
        None,
        description="Capital expenditures (CapEx) or payments for property, plant, and equipment.",
    )


class FinancialReportExtraction(BaseModel):
    company_name: str = Field(..., description="The name of the company.")
    fiscal_year: int = Field(
        ..., description="The fiscal year ending date for this report."
    )
    currency_symbol: str = Field(
        "KES", description="The currency symbol used in the report (e.g., $, €, £)."
    )
    scale: str = Field(
        "Millions",
        description="The scale of the numbers (e.g., Millions, Thousands, Billions).",
    )

    # Sub-models
    income_statement: IncomeStatementData
    balance_sheet: BalanceSheetData
    cash_flow: CashFlowData
