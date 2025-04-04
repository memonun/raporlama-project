import logging
from processing.pdf_extractor import PDFExtractor # Adjust import path if needed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PROJECT_TO_TEST = "v_metroway_test/" # Or your actual project folder name
BASE_PDF_DIR = "data/raw_pdfs/"   # Adjust if needed

try:
    print(f"--- Testing PDFExtractor for project: {PROJECT_TO_TEST} ---")
    extractor = PDFExtractor(project_name=PROJECT_TO_TEST, base_pdf_directory=BASE_PDF_DIR)
    extracted_data = extractor.process_project_pdfs()

    print(f"\n--- Extraction Results ({len(extracted_data)} files) ---")
    for data in extracted_data:
        print(f"File: {data.file_name}")
        if data.extraction_error:
            print(f"  Error: {data.extraction_error}")
        else:
            print(f"  Pages: {data.page_count}")
            print(f"  Text Length: {len(data.text)}")
            print(f"  Tables Found: {len(data.tables)}")
            # print("  Text Preview:", data.text[:200] + "...") # Uncomment for text preview
            # print("  Tables:", data.tables) # Uncomment to see table data
        print("-" * 20)

except FileNotFoundError as e:
    print(f"ERROR: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    import traceback
    traceback.print_exc()
