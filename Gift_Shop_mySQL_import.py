#!/usr/bin/python3
from sshtunnel import SSHTunnelForwarder
import pymysql.cursors
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import re
from random import randint


def sqlConnect(file_name, sheet_name, name, barcode, price):

    # Google Sheets loging using O Auth 2.0
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('FunValleyLabelMaker.json', scope)
    gc = gspread.authorize(credentials)
    sh = gc.open(file_name)
    worksheet = sh.worksheet(sheet_name)
    all_rows = worksheet.get_all_values()
    end_row = len(all_rows)


    pat1 = "\d\d\d\d\d"


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

            with connection.cursor() as cursor:
                # Create a new record
                sql = "SELECT barcode FROM shop_tblproduct WHERE barcode LIKE \'%s\'" %(barcode)
                cursor.execute(sql)
                result = cursor.fetchone()
                #print(result)

                if result == None:
                    while True:
                        random_number = randint(0,9999)
                        barcode = "FV%04d" % (random_number,)
                        try:
                            raise Exception(worksheet.find(fun_sku_number))
                        except Exception:
                            #print(barcode)
                            break
                    sql = "INSERT INTO shop_tblproduct (`productname`, `barcode`, `price`, `description`, `productstatus`, `fktaxclassid`, `istax`, `isinventory`, `inventory`, `istopproduct`, `isrental`, `iscustomizable`, `iskiosk`, `fkkioskcategoryid`) Values (\"%s\", \"%s\", \"%s\",\" \" , 1, 4, 1, 1, 0, 0, 0, 0, 0, 0)" %(name, barcode, price)
                    cursor.execute(sql)
                    connection.commit()
                    if name:
                        itemID = "SELECT pkproductid FROM shop_tblproduct where productname like \'%s\'" %(name)
                        cursor.execute(itemID)
                        result = cursor.fetchone()

                        reg1 = re.search(pat1, str(result))


                        if reg1:

                            print(reg1.group())

                            sql = "INSERT INTO tblregistertypeproduct (`fkregistertypeid`, `fkproductid`) Values (1, \"%s\")" %(reg1.group())
                            cursor.execute(sql)
                            sql = "INSERT INTO shop_tblproductcategory (`fkproductid`, `fkcategoryid`) Values (\"%s\", 5)" %(reg1.group())
                            cursor.execute(sql)
                            connection.commit()

                            return(barcode)



                        else:
                            print("FAILURE ON REG1")

                    else:
                        print("Name not valid")

                else:
                    return(None)
                    #print("%s is already in the database" % name)

        finally:
            connection.close()
