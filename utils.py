import re

import httpx


def convert_to_download_url(drive_preview_url: str) -> str | None:
    """
    Converts: https://drive.google.com/file/d/XYZ/preview
    To:       https://drive.google.com/uc?export=download&id=XYZ
    """
    if not drive_preview_url:
        return None
    match = re.search(r"/d/([^/]+)", drive_preview_url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return None


def get_google_drive_file_content(file_id: str) -> bytes:
    """
    Robustly downloads file content from Google Drive, handling:
    1. HTTP Redirects (Essential for Drive links)
    2. Large file virus scan confirmation tokens
    """
    url = "https://drive.google.com/uc"
    params = {"export": "download", "id": file_id}

    # 1. Initial Request (Allow redirects)
    with httpx.Client(follow_redirects=True) as client:
        response = client.get(url, params=params)

        # 2. Check for "Virus Scan Warning" (happens for large PDFs)
        # If we get a 200 OK but it's HTML, it's likely the warning page.
        if "text/html" in response.headers.get("content-type", ""):
            # We need to extract the confirmation token from the cookies or the link
            for key, value in response.cookies.items():
                if key.startswith("download_warning"):
                    # Re-try with the confirmation token
                    params["confirm"] = value
                    response = client.get(url, params=params)
                    break

        response.raise_for_status()  # Ensure we actually got a 200 OK
        return response.content


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


def clean_company_name(raw_name: str) -> str:
    # Normalize whitespace
    name = raw_name.strip()

    # Remove trailing share class / par value info
    name = re.sub(
        r"\s*(?:[O0]rd\.?|Ord\.?|ORD\.?)?\s*\d+(\.\d+)?\s*(?:AIMS|MIMS|MAIN)?$",
        "",
        name,
        flags=re.IGNORECASE,
    )

    # Remove trailing punctuation
    name = re.sub(r"[.,]\s*$", "", name)

    return name.strip()
