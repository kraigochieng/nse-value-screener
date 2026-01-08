import re
from datetime import datetime

import httpx
import pandas as pd
from bs4 import BeautifulSoup

from utils import clean_company_name


def parse_nse_data(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    extracted_data = []

    sector_toggles = soup.find_all("div", class_="toggle")

    for toggle in sector_toggles:
        heading_tag = toggle.find("a", class_="toggle-heading")

        if not heading_tag:
            continue

        sector_name = heading_tag.get_text(strip=True)

        company_blocks = toggle.find_all("div", class_="nse_comptext")

        for block in company_blocks:
            company_info = {
                "Exchange": "Nairobi Securities Exchange PLC",
                "Sector": sector_name,
                "Symbol": "N/A",
                "ISIN": "N/A",
                "Company": "N/A",
            }

            text_content = block.get_text(separator="|").strip()
            text_parts = [t.strip() for t in text_content.split("|") if t.strip()]

            for part in text_parts:
                clean_part = part.replace("\xa0", " ")

                if "Trading Symbol" in clean_part:
                    company_info["Symbol"] = clean_part.split(":")[-1].strip()
                elif "ISIN" in clean_part:
                    company_info["ISIN"] = clean_part.split(":")[-1].strip()

            name_container = block.find_previous_sibling(
                "div", class_="nectar-animated-title"
            )

            if name_container:
                h6_tag = name_container.find("h6")
                if h6_tag:
                    raw_name = h6_tag.get_text(strip=True)

                    company_info["Company"] = clean_company_name(raw_name)

            extracted_data.append(company_info)

    return extracted_data


if __name__ == "__main__":
    # 1. READ FILE (Save your HTML paste to a file named nse.html)
    try:
        url = "https://www.nse.co.ke/listed-companies/"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = httpx.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()

        print("Parsing HTML...")
        data = parse_nse_data(response.text)

        # # 2. DISPLAY RESULTS
        # print(f"{'SECTOR':<30} | {'SYMBOL':<10} | {'ISIN':<15} | {'COMPANY'}")
        # print("-" * 90)
        # for item in data:
        #     print(
        #         f"{item['Sector'][:28]:<30} | {item['Symbol']:<10} | {item['ISIN']:<15} | {item['Company']}"
        #     )

        # 3. OPTIONAL: Save to CSV
        df = pd.DataFrame(data)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"nse_listed_companies_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"\nSaved {len(data)} companies to {filename}")

    except FileNotFoundError:
        print(
            "Please save the HTML content into a file named 'nse.html' in the same folder."
        )
