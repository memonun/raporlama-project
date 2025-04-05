from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch

def create_turkish_pdf(filename="turkish_test.pdf"):
    # Create a canvas with letter size
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Add a title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, 10 * inch, "Turkish Character Test PDF")
    
    # Add some regular text
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, 9.5 * inch, "This PDF contains Turkish characters to test encoding issues.")
    
    # Add Turkish characters
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, 9 * inch, "Turkish Characters:")
    
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, 8.7 * inch, "çğıöşüÇĞİÖŞÜ")
    c.drawString(1 * inch, 8.4 * inch, "ç - c with cedilla")
    c.drawString(1 * inch, 8.1 * inch, "ğ - g with breve")
    c.drawString(1 * inch, 7.8 * inch, "ı - dotless i")
    c.drawString(1 * inch, 7.5 * inch, "ö - o with diaeresis")
    c.drawString(1 * inch, 7.2 * inch, "ş - s with cedilla")
    c.drawString(1 * inch, 6.9 * inch, "ü - u with diaeresis")
    
    # Add a table with Turkish characters
    data = [
        ['Header 1', 'Turkish', 'Header 3'],
        ['Row 1', 'çğıöşü', 'Row 1, Col 3'],
        ['Row 2', 'ÇĞİÖŞÜ', 'Row 2, Col 3'],
        ['Row 3', 'İstanbul', 'Row 3, Col 3'],
    ]
    
    # Create the table
    table = Table(data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch])
    
    # Add style to the table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    # Draw the table on the canvas
    table.wrapOn(c, width, height)
    table.drawOn(c, 1 * inch, 5 * inch)
    
    # Add a paragraph with Turkish text
    text = """
    Türkçe karakterler: çğıöşüÇĞİÖŞÜ
    
    İstanbul, Türkiye'nin en büyük şehridir. Boğaziçi Köprüsü, Asya ve Avrupa'yı birbirine bağlar.
    Türk kahvesi, geleneksel bir içecektir. Çay da Türkiye'de çok popülerdir.
    """
    textobject = c.beginText(1 * inch, 4 * inch)
    textobject.setFont("Helvetica", 10)
    for line in text.strip().split('\n'):
        textobject.textLine(line.strip())
    c.drawText(textobject)
    
    # Save the PDF
    c.save()
    print(f"Turkish PDF created: {filename}")

if __name__ == "__main__":
    create_turkish_pdf("turkish_test.pdf")
