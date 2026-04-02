# japan/pages/drug_page.py
# This is data collection code. Matching not done here, just extraction. Validation is done separately in validation_service.py

from playwright.sync_api import Page
from japan import config
from japan import selectors
from japan.services.normalization_service import normalize_price


class DrugPage:
    def __init__(self, page: Page):
        self.page = page

    def safe_goto(self, url, retries=3, wait_until="domcontentloaded"):
        for attempt in range(retries):
            try:
                self.page.goto(url, timeout=60000, wait_until=wait_until)
                self.page.wait_for_load_state("domcontentloaded")
                return
            except Exception:
                if attempt == retries - 1:
                    raise
                self.page.wait_for_timeout(2000)

    # 🔎 Search page
    def search_drug(self, drug_id: str):

        search_url = config.SEARCH_URL + drug_id
        self.safe_goto(search_url)

        # Give page some buffer time (important for KEGG slow response)
        self.page.wait_for_timeout(1000)

        # CASE 1: Directly landed on detail page
        if self.page.locator("table.product_info").count() > 0:
            return

        # CASE 2: Result list page
        if self.page.locator(selectors.RESULT_TABLE_LINKS).count() > 0:
            return

        # CASE 3: No result page
        if self.is_no_result_page():
            return

        self.page.wait_for_timeout(2000)

        if self.page.locator(selectors.RESULT_TABLE_LINKS).count() > 0:
            return

        if self.page.locator("table.product_info").count() > 0:
            return

        # If still nothing → raise error
        raise Exception("Search result unstable or not loaded properly")

    def get_result_links(self):
        return self.page.locator(selectors.RESULT_TABLE_LINKS)

    def open_matching_result(self):

        links = self.get_result_links()

        if links.count() == 0:
            return False

        for attempt in range(3):  # increased retry
            try:
                links.first.click(timeout=10000)
                self.page.wait_for_selector("css=table.product_info", timeout=15000)
                return True
            except Exception:
                self.page.wait_for_timeout(2000)

        return False

    def is_no_result_page(self):
        no_result = self.page.locator("css=div.box2")

        if no_result.count() > 0:
            message = no_result.inner_text().strip()
            if "一致する医薬品情報はありません" in message:
                return True

        return False

    def extract_details(self, yj_code_from_excel: str):

        result = {}
        yj_code_from_excel = str(yj_code_from_excel).strip()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(500)
        
        if self.page.locator("css=table.product_info").count() == 0:
            self.page.wait_for_timeout(1000)

        # 一般名 (Common name)
        # -------------------------
        ingredient_locator = self.page.locator(
            "xpath=//th[text()='一般名']/following-sibling::td"
        )

        if ingredient_locator.count() > 0:
            result["Ingredient"] = ingredient_locator.first.inner_text().strip()
        else:
            result["Ingredient"] = ""

        # 欧文一般名 (European common name)
        ingredient_en_locator = self.page.locator(
            "xpath=//th[text()='欧文一般名']/following-sibling::td"
        )

        if ingredient_en_locator.count() > 0:
            result["Ingredient_English"] = ingredient_en_locator.first.inner_text().strip()
        else:
            result["Ingredient_English"] = ""

        # -------------------------
        # 製剤名 (Formulation)
        # -------------------------
        seizai_locator = self.page.locator(
            "xpath=//th[text()='製剤名']/following-sibling::td"
        )

        if seizai_locator.count() > 0:
            result["Formulation"] = seizai_locator.inner_text().strip()
        else:
            result["Formulation"] = ""

        # ATCコード (ATC code)
        atc_locator = self.page.locator(
            "xpath=//th[text()='ATCコード']/following-sibling::td"
        )

        if atc_locator.count() > 0:
            result["ATC_Code"] = atc_locator.first.inner_text().strip()
        else:
            result["ATC_Code"] = ""


        rows = self.page.locator("css=table.product_info tbody tr")
        row_count = rows.count()

        for i in range(row_count):
            row = rows.nth(i)
            cells = row.locator("td")

            if cells.count() < 5:
                continue

            yj_code = cells.nth(3).inner_text().strip()

            if yj_code == yj_code_from_excel:
                result["brand"] = cells.nth(0).inner_text().strip()
                # 欧文商標名 (English Brand Name)
                try:
                    brand_en_cell = cells.nth(1)
                    result["brand_en"] = brand_en_cell.inner_text(timeout=2000).strip()
                except Exception:
                    result["brand_en"] = ""
                result["company"] = cells.nth(2).inner_text().strip()
                result["yj_code"] = yj_code
                result["price"] = cells.nth(4).inner_text().strip()
                return result

        return {}