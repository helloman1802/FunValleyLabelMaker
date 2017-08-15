from PyPDF2 import PdfFileMerger, PdfFileReader

filenames = ['watermark.pdf', 'overlay.pdf']

merger = PdfFileMerger()
for filename in filenames:
    merger.append(PdfFileReader(filename, 'rb'))

merger.write("merged.pdf")
