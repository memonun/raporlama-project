from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch

def create_test_pdf(filename="test_pdf.pdf"):
    # Create a canvas with letter size
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Add a title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, 10 * inch, "Test PDF Document")
    
    # Add some regular text
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, 9.5 * inch, "This is a test PDF document created for testing PDF extraction.")
    c.drawString(1 * inch, 9.2 * inch, "It contains text and a table to verify the extraction functionality.")
    
    # Add some Turkish characters to test encoding
    c.drawString(1 * inch, 8.8 * inch, "Turkish characters: çğıöşüÇĞİÖŞÜ")
    
    # Add a paragraph of text
    text = """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. 
    Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. 
    Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
    """
    textobject = c.beginText(1 * inch, 8.3 * inch)
    textobject.setFont("Helvetica", 10)
    for line in text.strip().split('\n'):
        textobject.textLine(line.strip())
    c.drawText(textobject)
    
    # Create a simple table
    data = [
        ['Header 1', 'Header 2', 'Header 3'],
        ['Row 1, Col 1', 'Row 1, Col 2', 'Row 1, Col 3'],
        ['Row 2, Col 1', 'Row 2, Col 2', 'Row 2, Col 3'],
        ['Row 3, Col 1', 'Row 3, Col 2', 'Row 3, Col 3'],
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
    table.drawOn(c, 1 * inch, 6 * inch)
    
    # Add a second page with more text
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, 10 * inch, "Second Page")
    
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, 9.5 * inch, "This is the second page of the test document.")
    
    # Add more text
    more_text = """
    Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
    Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam.
    Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione.
    """
    textobject = c.beginText(1 * inch, 9 * inch)
    textobject.setFont("Helvetica", 10)
    for line in more_text.strip().split('\n'):
        textobject.textLine(line.strip())
    c.drawText(textobject)
    
    # Save the PDF
    c.save()
    print(f"PDF created: {filename}")

if __name__ == "__main__":
    create_test_pdf("test_files/test_pdf.pdf")
