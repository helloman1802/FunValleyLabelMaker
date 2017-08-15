#!/usr/bin/python3

# This program is used in the pandas label maker to import non excistent product rows into the Product database of FunValley.
# When the user inputs data into the pandas label maker, this program imports the product into the database
# if the product does NOT already excist.


from sshtunnel import SSHTunnelForwarder
import pymysql.cursors
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import re
from random import randint


def sqlConnect(file_name, sheet_name, name, barcode_number, price):

    # Google Sheets loging using O Auth 2.0
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('FunValleyLabelMaker.json', scope)
    gc = gspread.authorize(credentials)
    sh = gc.open(file_name)
    worksheet = sh.worksheet(sheet_name)
    all_rows = worksheet.get_all_values()
    end_row = len(all_rows)


    pat1 = "\d\d\d\d\d"

    # Creates an SSH tunnel to the database server
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
            # Using the SSH tunnel it access the SQL database
            with connection.cursor() as cursor:
                # Sets a query
                sql = "SELECT barcode FROM shop_tblproduct WHERE barcode LIKE \'%s\'" %(barcode_number)
                # Executes the query
                cursor.execute(sql)
                # Places the result from the query into a readable format
                result = cursor.fetchone()
                #print(result)

                # If the result does not exsit then the program will begin the process of importing the new product into the database
                if result == None:
                    # Creates a random 4 digit number that will be used as the barcode.
                    while True:
                        random_number = randint(0,9999)
                        # Adds FV to the front of the 4 digits
                        barcode = "FV%04d" % (random_number,)
                        try:
                            # worksheet.find looks for the genarated barcode on the Google Sheet.
                            # If the search fails to find the barcode, the function will raise an error.
                            # If the error occurs that means that the barcode is unique and the while loop is broken.
                            raise Exception(worksheet.find(barcode))
                        except Exception:
                            #print(barcode)
                            break
                    # Inserts the item data into the first database table
                    sql = "INSERT INTO shop_tblproduct (`productname`, `barcode`, `price`, `description`, `productstatus`, `fktaxclassid`, `istax`, `isinventory`, `inventory`, `istopproduct`, `isrental`, `iscustomizable`, `iskiosk`, `fkkioskcategoryid`) Values (\"%s\", \"%s\", \"%s\",\" \" , 1, 4, 1, 1, 0, 0, 0, 0, 0, 0)" %(name, barcode, price)
                    cursor.execute(sql)
                    connection.commit()
                    if name:
                        # Selects the item id from the inserted product and uses the id to insert into another table
                        itemID = "SELECT pkproductid FROM shop_tblproduct where productname like \'%s\'" %(name)
                        cursor.execute(itemID)
                        result = cursor.fetchone()
                        # Uses regular expressions to filter the id into a usable format.
                        reg1 = re.search(pat1, str(result))


                        if reg1:

                            print(reg1.group())
                            # Inserts the product data into the two remaining tables.
                            sql = "INSERT INTO tblregistertypeproduct (`fkregistertypeid`, `fkproductid`) Values (1, \"%s\")" %(reg1.group())
                            cursor.execute(sql)
                            sql = "INSERT INTO shop_tblproductcategory (`fkproductid`, `fkcategoryid`) Values (\"%s\", 5)" %(reg1.group())
                            cursor.execute(sql)
                            connection.commit()
                            # Returns the generated barcode to the pandas label maker so that pandas can insert the new barcode into the Google Sheet
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
