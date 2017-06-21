from sshtunnel import SSHTunnelForwarder
import pymysql.cursors
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import re
from random import randint

# Google Sheets loging using O Auth 2.0
scope = ['https://spreadsheets.google.com/feeds']
credentials = ServiceAccountCredentials.from_json_keyfile_name('FunValleyLabelMaker.json', scope)
gc = gspread.authorize(credentials)
sh = gc.open("Grocery Inventory 2017")
worksheet = sh.worksheet("Sheet2")
all_rows = worksheet.get_all_values()
end_row = len(all_rows)





with SSHTunnelForwarder(
         ('172.29.10.252', 22),
         ssh_password="MalCannedAir$",
         ssh_username="simpatico",
         remote_bind_address=('localhost', 3306)) as server:

    connection = pymysql.connect(host='127.0.0.1',
                           port=server.local_bind_port,
                           user='root',
                           password='Nats@toolbag',
                           db='FunValleyPOS')
    try:

        for row in range(end_row):
            name = "%s" %(worksheet.cell(row+1, 2).value)
            #category = "%s" %(worksheet.cell(row+1, 4))
            print(name)
            barcode = worksheet.cell(row+1, 1).value
            price = worksheet.cell(row+1, 3).value
            """
            while True:
                random_number = randint(0,99999)
                barcode = "FV%05d" % (random_number,)
                try:
                    raise Exception(worksheet.find(fun_sku_number))
                except Exception:
                    print(barcode)
                    break
            """
            with connection.cursor() as cursor:
                # Create a new record
                sql = "INSERT INTO shop_tblproduct (`productname`, `barcode`, `price`, `description`, `productstatus`, `fktaxclassid`, `istax`, `isinventory`, `inventory`, `istopproduct`, `isrental`, `iscustomizable`, `iskiosk`, `fkkioskcategoryid`) Values (\"%s\", \"%s\", \"%s\",\" \" , 1, 4, 1, 1, 0, 0, 0, 0, 0, 0)" %(name, barcode, price)
                cursor.execute(sql)
                connection.commit()
                if name:
                    itemID = "SELECT pkproductid FROM shop_tblproduct where productname like \'%s\'" %(name)
                    cursor.execute(itemID)
                    result = cursor.fetchone()

                    reg1 = re.search(pat1, str(result))


                    if reg1:
                        #reg2 = re.search(pat2, category)
                        print(reg1.group())
                        """
                        if reg2:
                            category = reg2.group()
                            if category == "Ice Cream / Shakes":
                                category = 32
                            if category == "Drinks":
                                category = 33
                            if category == "Sides":
                                category = 34
                            if category == "Food":
                                category = 35
                        """
                        sql = "INSERT INTO tblregistertypeproduct (`fkregistertypeid`, `fkproductid`) Values (1, \"%s\")" %(reg1.group())
                        cursor.execute(sql)
                        sql = "INSERT INTO shop_tblproductcategory (`fkproductid`, `fkcategoryid`) Values (\"%s\", 8)" %(reg1.group())
                        cursor.execute(sql)
                        connection.commit()

                        #sql = "INSERT INTO shop_tblproductcategory (`fkproductid`, `fkcategoryid`) Values (\"%s\", \"%s\")" %(reg1.group(), category)
                        #cursor.execute(sql)
                        #connection.commit()

                        #else:
                        #    print("FAILURE ON REG2")

                else:
                    print("Name not valid")




    finally:
        connection.close()
