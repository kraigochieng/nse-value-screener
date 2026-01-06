import io
import pathlib
from typing import List, Optional

import httpx
from google import genai
from ollama import Client
from pydantic import BaseModel, Field

from settings import settings


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


def read_pdf_into_bytes(file_path):
    """
    Reads a PDF file from disk into a bytes object.

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        bytes: The binary content of the PDF file.
    """
    try:
        # Open the file in binary read mode ('rb') using a context manager
        with open(file_path, "rb") as pdf_file:
            # Read the entire file content into a bytes object
            pdf_bytes = pdf_file.read()
        return pdf_bytes
    except FileNotFoundError:
        print(f"Error: The file at '{file_path}' was not found.")
        return None
    except PermissionError:
        print(f"Error: Insufficient permissions to access '{file_path}'.")
        return None


def main():
    # client = Client(
    #     host="https://ollama.com",
    #     headers={"Authorization": "Bearer " + settings.ollama_api_key},
    # )

    # print(client)

    # path = "/home/kraigochieng/projects/nse-value-screener/git-wrapped-kraigochieng.png"

    # response = client.chat(
    #     model="gemma3:4b",
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": "What is in this image? Be concise.",
    #             "images": [path],
    #         }
    #     ],
    # )

    # print(response.message.content)

    # pdf_path = "/home/kraigochieng/projects/nse-value-screener/ke-scom-2025-ar-00.pdf"
    pdf_path = pathlib.Path("financial_reports/ke-scom-2025-ar-00.pdf")

    client = genai.Client(api_key=settings.gemini_api_key)

    # response = client.models
    # doc_io = read_pdf_into_bytes(file_path=pdf_path)

    doc_io = io.BytesIO(
        httpx.get(
            "https://drive.google.com/file/d/1hYsI-6jD4LTtowRyqdnONjBrCYkIckmD/view?usp=sharing"
        ).content
    )

    # print(doc_io)

    # sample_doc = client.files.upload(
    #     file=doc_io, config={"mime_type": "application/pdf"}
    # )

    sample_doc = client.files.upload(file=pdf_path)

    # prompt = "Summarise this document"

    prompt = """
    Analyze this financial report. Extract the specific values for the Income Statement, 
    Balance Sheet, and Cash Flow statement for the most recent fiscal year available in the document.
    
    If a specific field (like R&D or Treasury Stock) is not explicitly present, return null.
    Ensure you capture the correct scale (e.g., if the table says 'in millions', extract the number as seen).
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[sample_doc, prompt],
        config={
            "response_mime_type": "application/json",
            "response_json_schema": FinancialReportExtraction.model_json_schema(),
        },
    )

    # print(response.text)

    financial_report = FinancialReportExtraction.model_validate_json(response.text)
    print(financial_report)


if __name__ == "__main__":
    main()
