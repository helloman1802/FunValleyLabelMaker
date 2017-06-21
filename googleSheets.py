import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds']

credentials = ServiceAccountCredentials.from_json_keyfile_name('FunValleyLabelMaker.json', scope)

gc = gspread.authorize(credentials)

sh = gc.open("FunValleyGiftshopItemData")
worksheet = sh.worksheet("Sheet")

for i in range(worksheet.row_count):
    fun_sku = "FV3062"
    val = worksheet.cell(i+2, 1).value
    print(i+2, val)
    if val == fun_sku:
        print(val, " : ", fun_sku)
        break
        
