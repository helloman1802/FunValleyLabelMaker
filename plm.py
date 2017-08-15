#!/usr/bin/python3

# This program runs on a flask server that is started on system startup.
# This program interfaces with Google Sheets to extract data and then prints the data on Avery labels.
# This program was desinged for the Fun Valley Gift Shop and is used to print labels for Gift Shop items
# that are inputted into the Google Sheet.

# Here are the steps that the program runs:

# On the Google Sheet a user inputs data in preset columns. These columns are then
# imported into a pandas dataframe because pandas is much faster at data manipulation.
# These are the columns in the Google Sheet:

# Column A: This column contains the barcode of the product. The barcode is randomly genorated and is not inputted by the user.
# Column B: This column is the item discription and is inputted by the user.
# Column C: This column is the color of the item and is inputted by the user.
# Column D: This column is the size of the item in terms of clothing and is inputted by the user.
# Column E: This column is the price of the item and is inputted by the user.
# Column F: This column is the print quantity of the item. This column determines how many lebels of a certain product are going to be printed.
# This column is set to 0 by default. If the user changes the column to anything greater than 0, that is how many lebels of that product that will be printed.
# Columns G-I: These columns are vendor information and are not needed by the program.
# Column J: This column determines if the product is going to be printed on a larger circle label or a smaller square label.
# If the column is set to 0, the program will treat the label as a circle. If the column is 1 then it is treated as a square.

# After importing all of the product rows into a pandas dataframe it searches all of the rows on column F to see if the quantity is greater than 0.
# The program then imports all of the rows with a quantity greater than zero into another pandas dataframe.
# It does this because it makes the operation faster because there is less data to deal with.
# Now the program iterates through all of the rows in the dataframe and prints the labels based on their quantity.




# Needed for interfacing with Google Sheets API
import gspread
from oauth2client.service_account import ServiceAccountCredentials
# Used for PDF manipulation
import PyPDF2
from PyPDF2 import PdfFileReader
# Needed to run the Linux print command
import os
# Used for generating QR codes
import pyqrcode as qr
# Used for PDF manipulation
from reportlab.pdfgen import canvas
# Used for adding a random word to each set of pages generated
from random_words import RandomWords
# Needed to generate numbers for barcodes
from random import randint
# Not used, but is attached to a disabled function
import math
# Used for data manipulation
import pandas as pd
# Imports from Gift_Shop_mySQL_import in the current directory.
from Gift_Shop_mySQL_import import sqlConnect
# Creates a web server
from flask import Flask, redirect
from time import sleep

# Calls the random word genorator
rw = RandomWords()


# Starts the Flask web app
app = Flask(__name__)
app.debug = False
#app.run(host='172.29.0.29', port=5000)
# Sets the default URL route that the Flask server directs the user to. It's the index page of the web app
@app.route('/')
def index():
    return("Pandas")

# This function is run when the user is directed from the index page to the /square/ route
@app.route('/square/')
def square():
    try:
        # Google Sheets loging using O Auth 2.0
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name('FunValleyLabelMaker.json', scope)
        gc = gspread.authorize(credentials)

        # States the Google worksheet that the program will be extracting data
        sheet_file_name = "FunValleyGiftshopItemData"
        sheet_name = "Sheet"
        sh = gc.open(sheet_file_name)
        sheet = sh.worksheet(sheet_name)

        # Offset sets the Pandas index number on a row equal to the equivilant row in the Google Spreadsheet.
        # Pandas starts counting from 0 while Google Sheets starts at 1.
        offset = 1




        # Creates an empty DataFrame that will be appended to after row have been found with a print quantity.
        to_be_printed_square = pd.DataFrame(None, columns=list("ABCDEFGHIJ"))



        # The goal is to replicate the Google Sheet in a Pandas DataFrame.
        # Each variable reprisents all of the column data from the Google Sheet in the form of a list.

        row_values = [('A', sheet.col_values(1)),
        ('B', sheet.col_values(2)),
        ('C', sheet.col_values(3)),
        ('D', sheet.col_values(4)),
        ('E', sheet.col_values(5)),
        ('F', sheet.col_values(6)),
        ('G', sheet.col_values(7)),
        ('H', sheet.col_values(8)),
        ('I', sheet.col_values(9)),
        ('J', sheet.col_values(10)),
        ]
        # row_values now contains every cell value from the Spreadsheet

        # Turns the above list into a Pandas DataFrame.
        dataDump = pd.DataFrame.from_items(row_values)

        # The pandas function iterrows goes through every index id in the pandas DataFrame and attaches the row corresponding to the index id
        for index, row in dataDump.iterrows():
            try:
                # Checks to see if column F has a quantity and if it has a quantity, checks to see if column J is a circle or square.
                # The program determines if the item contains a quantity if the row is greater than 0.
                # The program determines if the item is a circle or squre based on whether column J is a 1 or a 0. (1 being square and circle being 0)
                if int(row['F']) > 0 and int(row['J']) == 1:
                    # Adds the resulting items to a new pandas DataFrame that is smaller and takes less computation.
                    appendedDF = pd.DataFrame([[row['A'], row['B'], row['C'], row['D'], row['E'], row['F'], row['G'], row['H'], row['I'], row['J']]], columns=list("ABCDEFGHIJ"))

                    frames = [to_be_printed_square, appendedDF]
                    to_be_printed_square = pd.concat(frames)
                    # Calls on the sqlConnect module to check if the item already exists on the Google Sheet
                    # or in the DB.
                    # If the item does not exist in either the DB or the Sheet, it will create a barcode and import the
                    # barcode into column A in the Googel Sheet and will imort the entire row into the DB.
                    sql_import = sqlConnect(sheet_file_name, sheet_name, row['B'], row['A'], row['E'])
                    print(sql_import)
                    if sql_import != None:
                        sheet.update_cell(int(index+offset), 1, sql_import)

            except ValueError:
                print('Non intiger')


        # totalLabels gives the program a count of how many labels it needs to print in total.
        totalLabels = 0

        for index, row in to_be_printed_square.iterrows():
            totalLabels = totalLabels + int(row["F"])





        counter = 0

        # Creates a blank PDF
        c = canvas.Canvas('watermark.pdf')
        # These variables contain counters and pixel coordinates for placing the barcodes and discriptions
        # based on the amount of labels needed to be printed for each label.
        n = 0
        t = 1

        x = 170
        y = 36.4

        discr_x = 40
        discr_y = 36.4

        color_x = 40
        color_y = 36.4

        price_x = 40
        price_y = 36.4

        page_num_x = 20
        page_num_y = 20
        page_counter = 0
        word = rw.random_word()
        row_count = 0


        # For every item in the pandas DataFrame
        for index, row in to_be_printed_square.iterrows():
            print("New Product")
            # For quantity of the item determined by column F
            for i in range(int(row["F"])):

                # Sets the variables for each column needed on the label
                price       = row["E"]
                discription = row["B"]
                size        = row["D"]
                color       = row["C"]

                row_count = row_count+1

                # Genereates a file name for the barcode in png format.
                # The program does not release the cache fast enough for the file name to be the same everytime so I fixed the problem by creating
                # new file names for every item on a page.
                #
                # Square labels are placed on a 20x4 labels sheet of paper. Thus there are 80 labels in total.
                # The program creates new png file for every label on the paper, so there are a max of 80 differently named png files.
                file_name = "qrcode%d.png" % (n)
                QR = qr.create(row["A"])
                print(row["A"])
                QR.png(file_name, scale=1)
                sleep(0.05)
                print(row_count, totalLabels)
                if counter == 0:
                    # This process is repeated on every if statement until the last one:
                    # All of the items discriptions and barcode are placed on the PDF according
                    # to the coordinates set.
                    # The coordinates are determined by the counter and the counter keeps track of the
                    # position that the discriptions are placed

                    # Places the barcode (in QR code format) on the PDF.
                    c.drawImage(file_name, 25, 37.5)
                    # Sets the font type and size for the discription
                    c.setFont('Helvetica', 6)
                    # Places the discription on PDF.
                    c.drawString(discr_x+15, 38.5, discription)
                    # Determines if the item has a color
                    if color:
                    # Places the color on the PDF.
                        c.drawString(color_x+15, color_y+9.4, color)
                    # Sets a larger font for the price so that it stands out to the customer better.
                    c.setFont('Helvetica-Bold', 10)
                    # Places the price on the PDF.
                    c.drawString(price_x+15, price_y+20, price)
                    # Determines if the program has met the required amount of labels
                    # by comparing the total amount of labels needed to be printed
                    # and the current row in the pandas DataFrame.
                    if totalLabels == row_count:
                        # If totalLabels equals row_count then the program
                        # Will preform the same steps it does at the end of evey page.
                        page_counter = page_counter + 1
                        # Places the page number and the random word at the bottem of the PDF.
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        # Saves the PDF
                        c.save()
                        # Merges the PDF with another PDF that lines the labels up
                        # with a template provides by Avery Labels
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        # Finally the print command is sent to Linux
                        # then Linux passes the command to the local CUPS server and prints to the predetermined printer.
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 1:
                    c.drawImage(file_name, x+5, 37.5)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, 38.5, discription)
                    if color:
                        c.drawString(color_x+165, color_y+9.4, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, (price_y+20), price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 2:
                    c.drawImage(file_name, x+155, 37.5)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, 38.5, discription)
                    if color:
                        c.drawString(color_x+320, color_y+9.4, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, (price_y+20), price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 3:
                    c.drawImage(file_name, x+300, 37.5)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, 38.5, discription)
                    if color:
                        c.drawString(color_x+465, color_y+9.4, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, (price_y+20), price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 4:
                    c.drawImage(file_name, 25, y*2)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*2, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*2, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*2, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 5:
                    c.drawImage(file_name, x+5, y*2)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*2, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*2, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*2, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 6:
                    c.drawImage(file_name, x+155, y*2)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*2, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*2, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*2, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                    c.drawImage(file_name, x+300, y*2)
                elif counter == 7:
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*2, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*2, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*2, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 8:
                    c.drawImage(file_name, 25, y*3)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*3, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*3, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*3, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 9:
                    c.drawImage(file_name, x+5, y*3)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*3, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*3, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*3, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 10:
                    c.drawImage(file_name, x+155, y*3)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*3, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*3, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*3, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 11:
                    c.drawImage(file_name, x+300, y*3)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*3, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*3, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*3, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 12:
                    c.drawImage(file_name, 25, y*4)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*4, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*4, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*4, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 13:
                    c.drawImage(file_name, x+5, y*4)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*4, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*4, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*4, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 14:
                    c.drawImage(file_name, x+155, y*4)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*4, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*4, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*4, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 15:
                    c.drawImage(file_name, x+300, y*4)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*4, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*4, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*4, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1




                elif counter == 16:
                    c.drawImage(file_name, 25, y*5)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*5, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*5, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*5, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 17:
                    c.drawImage(file_name, x+5, y*5)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*5, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*5, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*5, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 18:
                    c.drawImage(file_name, x+155, y*5)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*5, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*5, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*5, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 19:
                    c.drawImage(file_name, x+300, y*5)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*5, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*5, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*5, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 20:
                    c.drawImage(file_name, 25, y*6)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*6, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*6, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*6, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 21:
                    c.drawImage(file_name, x+5, y*6)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*6, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*6, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*6, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 22:
                    c.drawImage(file_name, x+155, y*6)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*6, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*6, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*6, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 23:
                    c.drawImage(file_name, x+300, y*6)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*6, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*6, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*6, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 24:
                    c.drawImage(file_name, 25, y*7)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*7, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*7, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*7, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 25:
                    c.drawImage(file_name, x+5, y*7)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*7, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*7, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*7, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 26:
                    c.drawImage(file_name, x+155, y*7)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*7, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*7, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*7, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 27:
                    c.drawImage(file_name, x+300, y*7)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*7, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*7, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*7, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 28:
                    c.drawImage(file_name, 25, y*8)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*8, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*8, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*8, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 29:
                    c.drawImage(file_name, x+5, y*8)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*8, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*8, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*8, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 30:
                    c.drawImage(file_name, x+155, y*8)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*8, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*8, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*8, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 31:
                    c.drawImage(file_name, x+300, y*8)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*8, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*8, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*8, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 32:
                    c.drawImage(file_name, 25, y*9)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*9, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*9, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*9, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 33:
                    c.drawImage(file_name, x+5, y*9)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*9, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*9, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*9, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 34:
                    c.drawImage(file_name, x+155, y*9)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*9, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*9, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*9, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 35:
                    c.drawImage(file_name, x+300, y*9)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*9, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*9, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*9, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 36:
                    c.drawImage(file_name, 25, y*10)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*10, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*10, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*10, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 37:
                    c.drawImage(file_name, x+5, y*10)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*10, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*10, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*10, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 38:
                    c.drawImage(file_name, x+155, y*10)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*10, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*10, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*10, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 39:
                    c.drawImage(file_name, x+300, y*10)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*10, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*10, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*10, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 40:
                    c.drawImage(file_name, 25, y*11)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*11, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*11, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*11, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 41:
                    c.drawImage(file_name, x+5, y*11)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*11, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*11, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*11, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 42:
                    c.drawImage(file_name, x+155, y*11)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*11, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*11, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*11, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 43:
                    c.drawImage(file_name, x+300, y*11)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*11, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*11, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*11, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 44:
                    c.drawImage(file_name, 25, y*12)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*12, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*12, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*12, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 45:
                    c.drawImage(file_name, x+5, y*12)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*12, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*12, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*12, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 46:
                    c.drawImage(file_name, x+155, y*12)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*12, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*12, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*12, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 47:
                    c.drawImage(file_name, x+300, y*12)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*12, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*12, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*12, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 48:
                    c.drawImage(file_name, 25, y*13)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*13, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*13, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*13, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 49:
                    c.drawImage(file_name, x+5, y*13)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*13, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*13, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*13, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 50:
                    c.drawImage(file_name, x+155, y*13)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*13, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*13, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*13, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 51:
                    c.drawImage(file_name, x+300, y*13)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*13, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*13, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*13, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 52:
                    c.drawImage(file_name, 25, y*14)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*14, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*14, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*14, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 53:
                    c.drawImage(file_name, x+5, y*14)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*14, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*14, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*14, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 54:
                    c.drawImage(file_name, x+155, y*14)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*14, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*14, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*14, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 55:
                    c.drawImage(file_name, x+300, y*14)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*14, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*14, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*14, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 56:
                    c.drawImage(file_name, 25, y*15)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*15, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*15, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*15, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 57:
                    c.drawImage(file_name, x+5, y*15)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*15, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*15, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*15, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 58:
                    c.drawImage(file_name, x+155, y*15)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*15, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*15, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*15, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 59:
                    c.drawImage(file_name, x+300, y*15)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*15, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*15, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*15, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 60:
                    c.drawImage(file_name, 25, y*16)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*16, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*16, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*16, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 61:
                    c.drawImage(file_name, x+5, y*16)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*16, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*16, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*16, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 62:
                    c.drawImage(file_name, x+155, y*16)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*16, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*16, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*16, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 63:
                    c.drawImage(file_name, x+300, y*16)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*16, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*16, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*16, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 64:
                    c.drawImage(file_name, 25, y*17)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*17, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*17, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*17, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 65:
                    c.drawImage(file_name, x+5, y*17)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*17, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*17, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*17, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 66:
                    c.drawImage(file_name, x+155, y*17)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*17, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*17, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*17, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 67:
                    c.drawImage(file_name, x+300, y*17)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*17, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*17, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*17, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 68:
                    c.drawImage(file_name, 25, y*18)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*18, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*18, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*18, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 69:
                    c.drawImage(file_name, x+5, y*18)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*18, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*18, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*18, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 70:
                    c.drawImage(file_name, x+155, y*18)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*18, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*18, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*18, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 71:
                    c.drawImage(file_name, x+300, y*18)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*18, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*18, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*18, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 72:
                    c.drawImage(file_name, 25, y*19)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*19, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*19, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*19, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 73:
                    c.drawImage(file_name, x+5, y*19)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*19, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*19, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*19, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 74:
                    c.drawImage(file_name, x+155, y*19)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*19, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*19, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*19, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 75:
                    c.drawImage(file_name, x+300, y*19)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+465, discr_y*19, discription)
                    if color:
                        c.drawString(color_x+465, 7+color_y*19, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+465, 18+price_y*19, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1



                elif counter == 76:
                    c.drawImage(file_name, 25, y*20)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+15, discr_y*20, discription)
                    if color:
                        c.drawString(color_x+15, 7+color_y*20, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+15, 18+price_y*20, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 77:
                    c.drawImage(file_name, x+5, y*20)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+165, discr_y*20, discription)
                    if color:
                        c.drawString(color_x+165, 7+color_y*20, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+165, 18+price_y*20, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 78:
                    c.drawImage(file_name, x+155, y*20)
                    c.setFont('Helvetica', 6)
                    c.drawString(discr_x+320, discr_y*20, discription)
                    if color:
                        c.drawString(color_x+320, 7+color_y*20, color)
                    c.setFont('Helvetica-Bold', 10)
                    c.drawString(price_x+320, 18+price_y*20, price)
                    if totalLabels == row_count:
                        page_counter = page_counter + 1
                        page_number = "%s %d" % (word, page_counter)
                        c.drawString(page_num_x, page_num_y, page_number)
                        c.save()
                        overlayFile = open('overlay2.pdf', 'rb')
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
                        sleep(1)
                        os.system("lp merged.pdf")

                        counter = 1
                    else:
                        counter = counter +1
                        n += 1


                elif counter == 79:
                    # Places the barcode (in QR code format) on the PDF.
                    c.drawImage(file_name, x+300, y*20)
                    # Sets the font type and size for the discription
                    c.setFont('Helvetica', 6)
                    # Places the discription on PDF.
                    c.drawString(discr_x+465, discr_y*20, discription)
                    # Determines if the item has a color
                    if color:
                    # Places the color on the PDF.
                        c.drawString(color_x+465, 7+color_y*20, color)
                        # Sets a larger font for the price so that it stands out to the customer better.
                    c.setFont('Helvetica-Bold', 10)
                    # Places the price on the PDF.
                    c.drawString(price_x+465, 18+price_y*20, price)
                    # Places the page number and the random word at the bottem of the PDF.
                    page_counter = page_counter + 1
                    page_number = "%s %d" % (word, page_counter)
                    c.drawString(page_num_x, page_num_y, page_number)
                    # Sets the counter to 0 so that the loops starts over.
                    counter = 0

                    # Saves the PDF
                    c.save()
                    # Merges the PDF with another PDF that lines the labels up
                	# with a template provides by Avery Labels
                    overlayFile = open('overlay2.pdf', 'rb')
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
                    # Resets the PDF for the next page.
                    PDF_name = 'watermark.pdf'
                    c = canvas.Canvas(PDF_name)
                    #input("Waiting")
                    n += 1

                    sleep(1)
                    # Finally the print command is sent to Linux
                	# then Linux passes the command to the local CUPS server and prints to the predetermined printer.
                    os.system("lp merged.pdf")

                    if totalLabels == row_count:
                        counter = 1




                if n > 100:
                    n = 0
        # Redirects the user to the finished printing page on the WordPress site.
        return redirect("http://172.29.0.29/index.php/pandas-are-done-slaving/")
    except KeyboardInterrupt:
        print(": EXITING")
        quit()

# All of the functions above are repeated on the circle function below.
# The only differece is the amount of labels that are the page.
# A circle label page is a 12x3 grid.

@app.route('/circle/')
def circle():
    try:
        # Google Sheets loging using O Auth 2.0
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name('FunValleyLabelMaker.json', scope)
        gc = gspread.authorize(credentials)
        sheet_file_name = "FunValleyGiftshopItemData"
        sheet_name = "Sheet"
        sh = gc.open(sheet_file_name)
        sheet = sh.worksheet(sheet_name)

        # Offset sets the Pandas index number on a row equal to the equivilant row in the Google Spreadsheet.
        offset = 1


        # The goal is to replicate the Google Sheet in a Pandas DataFrame.
        # Each variable reprisents all of the column data from the Google Sheet in the form of a list.

        # Creates an empty DataFrame that will be appended to after row have been found with a print quantity.
        to_be_printed_circle = pd.DataFrame(None, columns=list("ABCDEFGHIJ"))

        row_values = [('A', sheet.col_values(1)),
        ('B', sheet.col_values(2)),
        ('C', sheet.col_values(3)),
        ('D', sheet.col_values(4)),
        ('E', sheet.col_values(5)),
        ('F', sheet.col_values(6)),
        ('G', sheet.col_values(7)),
        ('H', sheet.col_values(8)),
        ('I', sheet.col_values(9)),
        ('J', sheet.col_values(10)),
        ]
        dataDump = pd.DataFrame.from_items(row_values)

        for index, row in dataDump.iterrows():
            try:

                if int(row['F']) > 0 and int(row['J']) == 0:
                    appendedDF = pd.DataFrame([[row['A'], row['B'], row['C'], row['D'], row['E'], row['F'], row['G'], row['H'], row['I'], row['J']]], columns=list("ABCDEFGHIJ"))
                    frames = [to_be_printed_circle, appendedDF]
                    to_be_printed_circle = pd.concat(frames)
                    sql_import = sqlConnect(sheet_file_name, sheet_name, row['B'], row['A'], row['E'])
                    print(sql_import)
                    if sql_import != None:
                        sheet.update_cell(int(index+offset), 1, sql_import)

            except ValueError:
                print('Non intiger')

        totalLabels = 0
        for index, row in to_be_printed_circle.iterrows():
            totalLabels = totalLabels + int(row["F"])

        n = 0
        t = 1

        x_qr = 102
        y_qr = 622

        x_price = 116
        y_price = 695

        x_dis = 116
        y_dis = 656

        page_num_x = 20
        page_num_y = 20
        page_counter = 0
        word = rw.random_word()
        row_count = 0
        counter = 1
        #print_count = len(data_frame_circle.index)

        c = canvas.Canvas('watermark.pdf')
        for index, row in to_be_printed_circle.iterrows():

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
                sleep(0.05)




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
                        resultPdfFile.close()

                        counter = 1

                        break

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
                        resultPdfFile.close()

                        counter = 1

                        break
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
                        resultPdfFile.close()

                        counter = 1

                        break

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
                        resultPdfFile.close()

                        counter = 1

                        break

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
                        resultPdfFile.close()

                        counter = 1

                        break

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
                        resultPdfFile.close()

                        counter = 1

                        break

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
                        resultPdfFile.close()

                        counter = 1

                        break

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
                        sleep(1)
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
                        sleep(1)
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
                        sleep(1)
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
                        sleep(1)
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
                    sleep(1)
                    os.system("lp merged.pdf")

                    n += 1


                    counter = 1

                if n > 20:
                    n = 0
        with open('merged.pdf', "rb") as f:
            input = PdfFileReader(f, "rb")

        os.system("lp merged.pdf")
        return redirect("http://172.29.0.29/index.php/pandas-are-done-slaving/")

    except KeyboardInterrupt:
        print(": EXITING")
        quit()

# This function prints the last saved PDF and then redirects the user to WordPress site.
@app.route('/reprint/')
def reprint():
    os.system("lp merged.pdf")
    return redirect("http://172.29.0.29/index.php/pandas-are-done-slaving/")
