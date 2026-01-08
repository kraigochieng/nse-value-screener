import io
import pathlib

from google import genai

from schemas import FinancialReportExtraction
from settings import settings
from utils import get_google_drive_file_content, read_pdf_into_bytes


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

    print(">>> Downloading file from Drive...")

    file_id = "1r-UQ_saLPgdcduj-IUbPV1zQJKQxgNmp"
    pdf_bytes = get_google_drive_file_content(file_id)
    print(f">>> Downloaded {len(pdf_bytes)} bytes.")
    # response = client.models
    # doc_io = read_pdf_into_bytes(file_path=pdf_path)

    # doc_io = io.BytesIO(
    #     httpx.get(
    #         "https://drive.google.com/uc?export=download&id=1r-UQ_saLPgdcduj-IUbPV1zQJKQxgNmp"
    #     ).content
    # )
    doc_io = io.BytesIO(pdf_bytes)

    # print(doc_io)

    print(">>> Uploading to Gemini...")
    sample_doc = client.files.upload(
        file=doc_io, config={"mime_type": "application/pdf"}
    )

    # sample_doc = client.files.upload(file=pdf_path)

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
