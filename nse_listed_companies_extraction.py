import httpx
import pandas as pd  # Optional: Useful if you want to export to CSV later
from bs4 import BeautifulSoup
from datetime import datetime


def parse_nse_data(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    extracted_data = []

    # 1. The page is divided into "Toggles" (Accordions) representing Sectors
    # We find all divs with class 'toggle'
    sector_toggles = soup.find_all("div", class_="toggle")

    for toggle in sector_toggles:
        # A. Extract the Sector Name (e.g., AGRICULTURAL, BANKING)
        # It is found inside the 'toggle-heading' link
        heading_tag = toggle.find("a", class_="toggle-heading")

        # Skip empty toggles (some might be structural spacers)
        if not heading_tag:
            continue

        sector_name = heading_tag.get_text(strip=True)

        # B. Find all Company Blocks inside this specific Sector
        # The key identifier we found earlier is 'nse_comptext'
        company_blocks = toggle.find_all("div", class_="nse_comptext")

        for block in company_blocks:
            company_info = {
                "Sector": sector_name,
                "Company": "N/A",
                "Symbol": "N/A",
                "ISIN": "N/A",
            }

            # --- 1. Extract Symbol and ISIN ---
            # We use a separator to handle cases where <p> tags are mashed together
            text_content = block.get_text(separator="|").strip()
            text_parts = [t.strip() for t in text_content.split("|") if t.strip()]

            for part in text_parts:
                # Clean up invisible characters and normalize
                clean_part = part.replace("\xa0", " ")

                if "Trading Symbol" in clean_part:
                    # Split by colon and take the last part
                    # Handle cases like "Trading Symbol: EGAD"
                    company_info["Symbol"] = clean_part.split(":")[-1].strip()
                elif "ISIN" in clean_part:
                    company_info["ISIN"] = clean_part.split(":")[-1].strip()

            # --- 2. Extract Company Name ---
            # The name is located in the 'nectar-animated-title' div
            # which is a *sibling* appearing immediately *before* the text block
            name_container = block.find_previous_sibling(
                "div", class_="nectar-animated-title"
            )

            if name_container:
                h6_tag = name_container.find("h6")
                if h6_tag:
                    company_info["Company"] = h6_tag.get_text(strip=True)

            extracted_data.append(company_info)

    return extracted_data


# --- Execution ---

# Assuming 'full_html' contains the string you pasted above.
# Since the HTML is massive, I will assume you are loading it from a file
# or pasting it into a variable named `html_source`.

# For this demonstration, if you have the file saved as 'nse.html':
# with open("nse.html", "r", encoding="utf-8") as f:
#    html_source = f.read()

# OR, if you pasted it into a variable:
# data = parse_nse_data(html_source)

# To run this with the file you provided, I will simulate the function call:
# (I am pasting the logic to run on the input you provided)

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

        timestamp = datetime.now().strftime("5Y%m%d_%H%M%S")
        df.to_csv(f"nse_listed_companies_{timestamp}.csv", index=False)
        print(f"\nSaved {len(data)} companies to nse_companies.csv")

    except FileNotFoundError:
        print(
            "Please save the HTML content into a file named 'nse.html' in the same folder."
        )
