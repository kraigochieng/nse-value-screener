import re
from playwright.sync_api import Page, expect


def test_has_title(page: Page):
    page.goto("https://africanfinancials.com/kenya-listed-company-documents/")

    page.get_by_role("combobox", name="wpv-document-type").select_option("annual-reports")
