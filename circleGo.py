import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import PyPDF2
import os
import pyqrcode as qr
from reportlab.pdfgen import canvas
from random_words import RandomWords
from random import randint
import math
import pandas as pd
rw = RandomWords()
#from flask import Flask

# Google Sheets loging using O Auth 2.0
scope = ['https://spreadsheets.google.com/feeds']
credentials = ServiceAccountCredentials.from_json_keyfile_name('FunValleyLabelMaker.json', scope)
gc = gspread.authorize(credentials)
sh = gc.open("FunValleyGiftshopItemData")
sheet = sh.worksheet("Sheet")
#app = Flask(__name__)
#app.run(host='172.29.0.29', port=4999)

#@app.route('/')
#def index():
#    return("Pandas")
#@app.route('/circle/')
def circle():
    all_rows = sheet.get_all_values()
    end_row = len(all_rows)
    position = 1
    counter = int(position)
    print(end_row)
    offset = 2
    data_frame_circle = pd.DataFrame(None, columns=list("ABCDEFGHIJ"))
    data_frame_square = pd.DataFrame(None, columns=list("ABCDEFGHIJ"))

    try:
        row_number = 1
        for row in range(end_row-1):
            if int(sheet.cell(row+offset, 6).value) > 0:
                if int(sheet.cell(row+offset, 10).value) == 0:

                    # An if statement will check the value of column 5.
                    # If column 5 is equal to zero, put that row's values into the circle data frame.
                    # If column 5 is equal to 1, put that row's value into the square data frame.


                    A = sheet.cell(row+offset, 1).value
                    # Discription
                    B = sheet.cell(row+offset, 2).value
                    # Color
                    C = sheet.cell(row+offset, 3).value
                    # Size
                    D = sheet.cell(row+offset, 4).value
                    # Price
                    E = sheet.cell(row+offset, 5).value
                    # Quantity
                    F = sheet.cell(row+offset, 6).value
                    # Vendor SKU
                    G = sheet.cell(row+offset, 7).value
                    # Vendor Invoice
                    H = sheet.cell(row+offset, 8).value
                    # Vendor Name
                    I = sheet.cell(row+offset, 9).value
                    # Circle or Square label
                    J = sheet.cell(row+offset, 10).value

                    row_number = row_number+1
                    print("Pandas are making circles")
                    sql_import = sqlConnect(sheet_file_name, sheet_name, B, A, E)
                    print(sql_import)
                    if sql_import != None:
                        sheet.update_cell(row+offset, 1, sql_import)
                    circle_sorted = pd.DataFrame([[A, B, C, D, E, F, G, H, I, J]], columns=list("ABCDEFGHIJ"))
                    frames = [data_frame_circle, circle_sorted]
                    data_frame_circle = pd.concat(frames)
            else:
                print("No Quantity")
                print("Row Number: ", row_number)
                row_number = row_number+1

        totalLabels = 0
        for index, row in data_frame_circle.iterrows():
            totalLabels = totalLabels + int(row["F"])

        n = 0
        t = 1

        x_qr = 101
        y_qr = 626

        x_price = 116
        y_price = 695

        x_dis = 116
        y_dis = 656

        page_num_x = 20
        page_num_y = 20
        page_counter = 0
        word = rw.random_word()
        row_count = 0
        #print_count = len(data_frame_circle.index)

        c = canvas.Canvas('watermark.pdf')
        for index, row in data_frame_circle.iterrows():

            print("New Product")
            for i in range(int(row["F"])):
                row_count = row_count+1




                print(row_count)





                price       = row["E"]
                discription = row["B"]
                size        = row["D"]
                color       = row["C"]
                overlay     = "overlay.pdf"

                file_name = "qrcode%d.png" % (n)
                QR = qr.create(row["A"])
                QR.png(file_name, scale=1)




                if counter == 1:
                    #c.drawImage("welcome_925.png", -11 , 630)
                    c.setFont('Helvetica', 8)
                    c.drawCentredString(x_dis, y_dis, discription)
                    c.setFont('Helvetica-Bold', 15)
                    c.drawCentredString(x_price, y_price, price)
                    c.setFont('Helvetica-Bold', 13)
                    if size:
                        c.drawCentredString(x_dis,y_dis+24,size)
                    c.setFont('Helvetica-Bold', 10)
                    if color:
                        c.drawCentredString(x_dis,y_dis+12,color)
                    c.drawImage(file_name, x_qr, y_qr)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        print("Merging PDFs")
                        overlayFile = open(overlay, 'rb')
                        pdfReader = PyPDF2.PdfFileReader(overlayFile)
                        minutesFirstPage = pdfReader.getPage(0)
                        pdfWatermarkReader = PyPDF2.PdfFileReader(open('watermark.pdf', 'rb'))
                        minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
                        pdfWriter = PyPDF2.PdfFileWriter()
                        pdfWriter.addPage(minutesFirstPage)

                        for pageNum in range(1, pdfReader.numPages):
                                pageObj = pdfReader.getPage(pageNum)
                                pdfWriter.addPage(pageObj)
                        resultPdfFile = open('merged.pdf', 'wb')
                        pdfWriter.write(resultPdfFile)
                        overlayFile.close()
                        os.system("lp merged.pdf")
                        counter = 1

                    else:
                        counter = counter +1
                        n += 1




                elif counter == 2:
                    #c.drawImage("welcome_925.png", 250, 740)
                    c.setFont('Helvetica', 8)
                    c.drawCentredString(x_dis + 190, y_dis, discription)
                    c.setFont('Helvetica-Bold', 15)
                    c.drawCentredString(x_price + 190, y_price, price)
                    c.setFont('Helvetica-Bold', 13)
                    if size:
                        c.drawCentredString(x_dis + 190,y_dis+24,size)
                    c.setFont('Helvetica-Bold', 10)
                    if color:
                        c.drawCentredString(x_dis + 190,y_dis+12,color)
                    c.drawImage(file_name, x_qr + 190, y_qr)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        print("Merging PDFs")
                        overlayFile = open(overlay, 'rb')
                        pdfReader = PyPDF2.PdfFileReader(overlayFile)
                        minutesFirstPage = pdfReader.getPage(0)
                        pdfWatermarkReader = PyPDF2.PdfFileReader(open('watermark.pdf', 'rb'))
                        minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
                        pdfWriter = PyPDF2.PdfFileWriter()
                        pdfWriter.addPage(minutesFirstPage)

                        for pageNum in range(1, pdfReader.numPages):
                                pageObj = pdfReader.getPage(pageNum)
                                pdfWriter.addPage(pageObj)
                        resultPdfFile = open('merged.pdf', 'wb')
                        pdfWriter.write(resultPdfFile)
                        overlayFile.close()
                        os.system("lp merged.pdf")
                        counter = 1

                    else:
                        counter = counter +1
                        n += 1



                elif counter == 3:
                    #c.drawImage("welcome_925.png", x_price + 400, 740)
                    c.setFont('Helvetica', 8)
                    c.drawCentredString(x_dis + 380, y_dis, discription)
                    c.setFont('Helvetica-Bold', 15)
                    c.drawCentredString(x_price + 380, y_price, price)
                    c.setFont('Helvetica-Bold', 13)
                    if size:
                        c.drawCentredString(x_price + 380,y_dis+24,size)
                    c.setFont('Helvetica-Bold', 10)
                    if color:
                        c.drawCentredString(x_price + 380,y_dis+12,color)
                    c.drawImage(file_name, x_qr + 380, y_qr)

                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        print("Merging PDFs")
                        overlayFile = open(overlay, 'rb')
                        pdfReader = PyPDF2.PdfFileReader(overlayFile)
                        minutesFirstPage = pdfReader.getPage(0)
                        pdfWatermarkReader = PyPDF2.PdfFileReader(open('watermark.pdf', 'rb'))
                        minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
                        pdfWriter = PyPDF2.PdfFileWriter()
                        pdfWriter.addPage(minutesFirstPage)

                        for pageNum in range(1, pdfReader.numPages):
                                pageObj = pdfReader.getPage(pageNum)
                                pdfWriter.addPage(pageObj)
                        resultPdfFile = open('merged.pdf', 'wb')
                        pdfWriter.write(resultPdfFile)
                        overlayFile.close()
                        os.system("lp merged.pdf")
                        counter = 1

                    else:
                        counter = counter +1
                        n += 1



                elif counter == 4:
                    #c.drawImage("welcome_925.png", 37.5, 540)
                    c.setFont('Helvetica', 8)
                    c.drawCentredString(x_dis, y_dis - 183, discription)
                    c.setFont('Helvetica-Bold', 15)
                    c.drawCentredString(x_price, y_price - 185, price)
                    c.setFont('Helvetica-Bold', 13)
                    if size:
                        c.drawCentredString(x_dis, y_dis-160,size)
                    c.setFont('Helvetica-Bold', 10)
                    if color:
                        c.drawCentredString(x_dis,y_dis-172,color)
                    c.drawImage(file_name, x_qr, y_qr - 185)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        print("Merging PDFs")
                        overlayFile = open(overlay, 'rb')
                        pdfReader = PyPDF2.PdfFileReader(overlayFile)
                        minutesFirstPage = pdfReader.getPage(0)
                        pdfWatermarkReader = PyPDF2.PdfFileReader(open('watermark.pdf', 'rb'))
                        minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
                        pdfWriter = PyPDF2.PdfFileWriter()
                        pdfWriter.addPage(minutesFirstPage)

                        for pageNum in range(1, pdfReader.numPages):
                                pageObj = pdfReader.getPage(pageNum)
                                pdfWriter.addPage(pageObj)
                        resultPdfFile = open('merged.pdf', 'wb')
                        pdfWriter.write(resultPdfFile)
                        overlayFile.close()
                        os.system("lp merged.pdf")
                        counter = 1

                    else:
                        counter = counter +1
                        n += 1



                elif counter == 5:
                    #c.drawImage("welcome_925.png", 250, 540)
                    c.setFont('Helvetica', 8)
                    c.drawCentredString(x_dis + 190, y_dis - 183, discription)
                    c.setFont('Helvetica-Bold', 15)
                    c.drawCentredString(x_price + 190, y_price - 185, price)
                    c.setFont('Helvetica-Bold', 13)
                    if size:
                        c.drawCentredString(x_price + 190, y_dis-160,size)
                    c.setFont('Helvetica-Bold', 10)
                    if color:
                        c.drawCentredString(x_price + 190,y_dis-172,color)
                    c.drawImage(file_name, x_qr + 190, y_qr - 185)

                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        print("Merging PDFs")
                        overlayFile = open(overlay, 'rb')
                        pdfReader = PyPDF2.PdfFileReader(overlayFile)
                        minutesFirstPage = pdfReader.getPage(0)
                        pdfWatermarkReader = PyPDF2.PdfFileReader(open('watermark.pdf', 'rb'))
                        minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
                        pdfWriter = PyPDF2.PdfFileWriter()
                        pdfWriter.addPage(minutesFirstPage)

                        for pageNum in range(1, pdfReader.numPages):
                                pageObj = pdfReader.getPage(pageNum)
                                pdfWriter.addPage(pageObj)
                        resultPdfFile = open('merged.pdf', 'wb')
                        pdfWriter.write(resultPdfFile)
                        overlayFile.close()
                        os.system("lp merged.pdf")
                        counter = 1

                    else:
                        counter = counter +1
                        n += 1



                elif counter == 6:
                    #c.drawImage("welcome_925.png", x_price + 400, 540)
                    c.setFont('Helvetica', 8)
                    c.drawCentredString(x_dis + 380, y_dis - 183, discription)
                    c.setFont('Helvetica-Bold', 15)
                    c.drawCentredString(x_price + 380, y_price - 185, price)
                    c.setFont('Helvetica-Bold', 13)
                    if size:
                        c.drawCentredString(x_price + 380, y_dis-160,size)
                    c.setFont('Helvetica-Bold', 10)
                    if color:
                        c.drawCentredString(x_price + 380,y_dis-172,color)
                    c.drawImage(file_name, x_qr+380, y_qr - 185)

                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        print("Merging PDFs")
                        overlayFile = open(overlay, 'rb')
                        pdfReader = PyPDF2.PdfFileReader(overlayFile)
                        minutesFirstPage = pdfReader.getPage(0)
                        pdfWatermarkReader = PyPDF2.PdfFileReader(open('watermark.pdf', 'rb'))
                        minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
                        pdfWriter = PyPDF2.PdfFileWriter()
                        pdfWriter.addPage(minutesFirstPage)

                        for pageNum in range(1, pdfReader.numPages):
                                pageObj = pdfReader.getPage(pageNum)
                                pdfWriter.addPage(pageObj)
                        resultPdfFile = open('merged.pdf', 'wb')
                        pdfWriter.write(resultPdfFile)
                        overlayFile.close()
                        os.system("lp merged.pdf")
                        counter = 1

                    else:
                        counter = counter +1
                        n += 1



                elif counter == 7:
                    #c.drawImage("welcome_925.png", 37.5, 340)
                    c.setFont('Helvetica', 8)
                    c.drawCentredString(x_dis, y_dis - 368, discription)
                    c.setFont('Helvetica-Bold', 15)
                    c.drawCentredString(x_price, y_price - 370, price)
                    c.setFont('Helvetica-Bold', 13)
                    if size:
                        c.drawCentredString(x_dis, y_dis - 346,size)
                    c.setFont('Helvetica-Bold', 10)
                    if color:
                        c.drawCentredString(x_dis,y_dis-357,color)
                    c.drawImage(file_name, x_qr, y_qr - 370)

                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        print("Merging PDFs")
                        overlayFile = open(overlay, 'rb')
                        pdfReader = PyPDF2.PdfFileReader(overlayFile)
                        minutesFirstPage = pdfReader.getPage(0)
                        pdfWatermarkReader = PyPDF2.PdfFileReader(open('watermark.pdf', 'rb'))
                        minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
                        pdfWriter = PyPDF2.PdfFileWriter()
                        pdfWriter.addPage(minutesFirstPage)

                        for pageNum in range(1, pdfReader.numPages):
                                pageObj = pdfReader.getPage(pageNum)
                                pdfWriter.addPage(pageObj)
                        resultPdfFile = open('merged.pdf', 'wb')
                        pdfWriter.write(resultPdfFile)
                        overlayFile.close()
                        os.system("lp merged.pdf")
                        counter = 1

                    else:
                        counter = counter +1
                        n += 1



                elif counter == 8:
                    #c.drawImage("welcome_925.png", 250, 340)
                    c.setFont('Helvetica', 8)
                    c.drawCentredString(x_dis+190, y_dis - 368, discription)
                    c.setFont('Helvetica-Bold', 15)
                    c.drawCentredString(x_price+190, y_price - 370, price)
                    c.setFont('Helvetica-Bold', 13)
                    if size:
                        c.drawCentredString(x_price+190, y_dis - 346,size)
                    c.setFont('Helvetica-Bold', 10)
                    if color:
                        c.drawCentredString(x_price+190,y_dis-357,color)
                    c.drawImage(file_name, x_qr + 190, y_qr - 370)

                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        print("Merging PDFs")
                        overlayFile = open(overlay, 'rb')
                        pdfReader = PyPDF2.PdfFileReader(overlayFile)
                        minutesFirstPage = pdfReader.getPage(0)
                        pdfWatermarkReader = PyPDF2.PdfFileReader(open('watermark.pdf', 'rb'))
                        minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
                        pdfWriter = PyPDF2.PdfFileWriter()
                        pdfWriter.addPage(minutesFirstPage)

                        for pageNum in range(1, pdfReader.numPages):
                                pageObj = pdfReader.getPage(pageNum)
                                pdfWriter.addPage(pageObj)
                        resultPdfFile = open('merged.pdf', 'wb')
                        pdfWriter.write(resultPdfFile)
                        overlayFile.close()
                        os.system("lp merged.pdf")
                        counter = 1

                    else:
                        counter = counter +1
                        n += 1




                elif counter == 9:
                    #c.drawImage("welcome_925.png", x_price + 400, 340)
                    c.setFont('Helvetica', 8)
                    c.drawCentredString(x_dis + 380, y_dis - 368, discription)
                    c.setFont('Helvetica-Bold', 15)
                    c.drawCentredString(x_price + 380, y_price - 370, price)
                    c.setFont('Helvetica-Bold', 13)
                    if size:
                        c.drawCentredString(x_price + 380,  y_dis - 346,size)
                    c.setFont('Helvetica-Bold', 10)
                    if color:
                        c.drawCentredString(x_price + 380,y_dis-357,color)
                    c.drawImage(file_name, x_qr+380, y_qr - 370)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        print("Merging PDFs")
                        overlayFile = open(overlay, 'rb')
                        pdfReader = PyPDF2.PdfFileReader(overlayFile)
                        minutesFirstPage = pdfReader.getPage(0)
                        pdfWatermarkReader = PyPDF2.PdfFileReader(open('watermark.pdf', 'rb'))
                        minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
                        pdfWriter = PyPDF2.PdfFileWriter()
                        pdfWriter.addPage(minutesFirstPage)

                        for pageNum in range(1, pdfReader.numPages):
                                pageObj = pdfReader.getPage(pageNum)
                                pdfWriter.addPage(pageObj)
                        resultPdfFile = open('merged.pdf', 'wb')
                        pdfWriter.write(resultPdfFile)
                        overlayFile.close()
                        os.system("lp merged.pdf")
                        counter = 1

                    else:
                        counter = counter +1
                        n += 1




                elif counter == 10:
                    #c.drawImage("welcome_925.png", 37.5, 140)
                    c.setFont('Helvetica', 8)
                    c.drawCentredString(x_dis, y_dis - 553, discription)
                    c.setFont('Helvetica-Bold', 15)
                    c.drawCentredString(x_price, y_price-555, price)
                    c.setFont('Helvetica-Bold', 13)
                    if size:
                        c.drawCentredString(x_dis, y_dis-530,size)
                    c.setFont('Helvetica-Bold', 10)
                    if color:
                        c.drawCentredString(x_dis,y_dis-542,color)
                    c.drawImage(file_name, x_qr, y_qr-555)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        print("Merging PDFs")
                        overlayFile = open(overlay, 'rb')
                        pdfReader = PyPDF2.PdfFileReader(overlayFile)
                        minutesFirstPage = pdfReader.getPage(0)
                        pdfWatermarkReader = PyPDF2.PdfFileReader(open('watermark.pdf', 'rb'))
                        minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
                        pdfWriter = PyPDF2.PdfFileWriter()
                        pdfWriter.addPage(minutesFirstPage)

                        for pageNum in range(1, pdfReader.numPages):
                                pageObj = pdfReader.getPage(pageNum)
                                pdfWriter.addPage(pageObj)
                        resultPdfFile = open('merged.pdf', 'wb')
                        pdfWriter.write(resultPdfFile)
                        overlayFile.close()
                        os.system("lp merged.pdf")
                        counter = 1

                    else:
                        counter = counter +1
                        n += 1




                elif counter == 11:
                    #c.drawImage("welcome_925.png", 250, 140)
                    c.setFont('Helvetica', 8)
                    c.drawCentredString(x_dis + 190, y_dis - 553, discription)
                    c.setFont('Helvetica-Bold', 15)
                    c.drawCentredString(x_price + 190, y_price-555, price)
                    c.setFont('Helvetica-Bold', 13)
                    if size:
                        c.drawCentredString(x_price + 190,y_dis-530,size)
                    c.setFont('Helvetica-Bold', 10)
                    if color:
                        c.drawCentredString(x_price + 190,y_dis-542,color)
                    c.drawImage(file_name, x_qr + 190, y_qr-555)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        print("Merging PDFs")
                        overlayFile = open(overlay, 'rb')
                        pdfReader = PyPDF2.PdfFileReader(overlayFile)
                        minutesFirstPage = pdfReader.getPage(0)
                        pdfWatermarkReader = PyPDF2.PdfFileReader(open('watermark.pdf', 'rb'))
                        minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
                        pdfWriter = PyPDF2.PdfFileWriter()
                        pdfWriter.addPage(minutesFirstPage)

                        for pageNum in range(1, pdfReader.numPages):
                                pageObj = pdfReader.getPage(pageNum)
                                pdfWriter.addPage(pageObj)
                        resultPdfFile = open('merged.pdf', 'wb')
                        pdfWriter.write(resultPdfFile)
                        overlayFile.close()
                        os.system("lp merged.pdf")
                        counter = 1

                    else:
                        counter = counter +1
                        n += 1





                elif counter == 12:
                    #c.drawImage("welcome_925.png", x_price + 400, 140)
                    c.setFont('Helvetica', 8)
                    c.drawCentredString(x_dis + 380, y_dis - 553, discription)
                    c.setFont('Helvetica-Bold', 15)
                    c.drawCentredString(x_price + 380, y_price-555, price)
                    c.setFont('Helvetica-Bold', 13)
                    if size:
                        c.drawCentredString(x_price + 380, y_dis-530,size)
                    c.setFont('Helvetica-Bold', 10)
                    if color:
                        c.drawCentredString(x_price + 380,y_dis-542,color)
                    c.drawImage(file_name, x_qr+380, y_qr-555)
                    counter = 1
                    page_counter = page_counter + 1
                    page_number = "%s %d" % (word, page_counter)
                    c.drawString(page_num_x, page_num_y, page_number)
                    c.save()

                    print("Merging PDFs")
                    overlayFile = open(overlay, 'rb')
                    pdfReader = PyPDF2.PdfFileReader(overlayFile)
                    minutesFirstPage = pdfReader.getPage(0)
                    pdfWatermarkReader = PyPDF2.PdfFileReader(open('watermark.pdf', 'rb'))
                    minutesFirstPage.mergePage(pdfWatermarkReader.getPage(0))
                    pdfWriter = PyPDF2.PdfFileWriter()
                    pdfWriter.addPage(minutesFirstPage)

                    for pageNum in range(1, pdfReader.numPages):
                            pageObj = pdfReader.getPage(pageNum)
                            pdfWriter.addPage(pageObj)
                    resultPdfFile = open('merged.pdf', 'wb')
                    pdfWriter.write(resultPdfFile)
                    overlayFile.close()
                    resultPdfFile.close()
                    PDF_name = 'watermark.pdf'
                    c = canvas.Canvas(PDF_name)
                    os.system("lp merged.pdf")
                    n += 1


                    counter = 1

                if n > 20:
                    n = 0
        #return redirect("http://172.29.0.29/index.php/pandas-are-done-slaving/")

    except KeyboardInterrupt:
        print(": EXITING")
        quit()
circle()
