import pandas as pd

# 1. Load the harvested CSV
filename = "annual_reports_queue_20260108_102010"
df = pd.read_csv(f"{filename}.csv")

# 2. Filter: Keep only rows where 'title' contains "Annual Report"
# case=False makes it insensitive to capitalization (e.g., "Annual report" vs "ANNUAL REPORT")
annual_reports = df[df["title"].str.contains("Annual Report", case=False, na=False)]

# Optional: You can also filter by year if you only want 2025
# annual_reports = annual_reports[annual_reports['title'].str.contains("2025")]

# 3. Check the result
print(f"Original count: {len(df)}")
print(f"Filtered count: {len(annual_reports)}")
print(annual_reports.head())

# 4. Save the cleaned list for the downloader
annual_reports.to_csv(f"{filename}_cleaned.csv", index=False)
