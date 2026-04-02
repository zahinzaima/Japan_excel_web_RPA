# Search page
SEARCH_BOX = "input[name='text']"
SEARCH_BUTTON = "input[value='検索']"

# Result page
RESULT_TABLE_LINKS = "table.list1 td.data1 a"

# Detail page
INGREDIENT_JP = "xpath=//th[contains(text(),'一般名')]/following-sibling::td"
INGREDIENT_EN = "xpath=//th[contains(text(),'欧文一般名')]/following-sibling::td"

PRODUCT_TABLE_ROWS = "xpath=//h3[contains(text(),'商品情報')]/following::table[1]//tr[position()>1]"

# inside product row:
BRAND_CELL = "td:nth-child(1)"
COMPANY_CELL = "td:nth-child(3)"
PRICE_CELL = "td:nth-child(5)"