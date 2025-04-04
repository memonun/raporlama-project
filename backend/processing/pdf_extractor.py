import os
import fitz  # PyMuPDF
import camelot
import pandas as pd
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Pydantic Model ---
class ExtractedPDF(BaseModel):
    file_name: str = Field(..., description="Original name of the PDF file (e.g., '2025-01-01.pdf')")
    full_path: str = Field(..., description="Absolute or relative path to the PDF file")
    page_count: Optional[int] = Field(None, description="Number of pages in the PDF")
    text: str = Field(..., description="Full extracted text content from all pages")
    tables: List[List[List[str]]] = Field(default_factory=list, description="List of tables found. Each table is a list of rows, each row is a list of cell strings.")
    extraction_error: Optional[str] = Field(None, description="Error message if extraction failed for this file")

# --- PDF Extractor Class ---
class PDFExtractor:
    """
    Extracts text and tables from PDF files within a project directory.
    """
    def __init__(self, project_name: str, base_pdf_directory: str = "backend/data/raw_pdfs/"):
        """
        Initializes the PDFExtractor.

        Args:
            project_name: The name of the project subdirectory.
            base_pdf_directory: The base directory containing project PDF subdirectories.

        Raises:
            FileNotFoundError: If the project-specific PDF directory does not exist.
        """
        self.project_name = project_name
        self.base_pdf_directory = Path(base_pdf_directory)
        self.project_pdf_path = self.base_pdf_directory / self.project_name

        if not self.project_pdf_path.is_dir():
            logging.error(f"Project PDF directory not found: {self.project_pdf_path}")
            raise FileNotFoundError(f"Project PDF directory not found: {self.project_pdf_path}")

        logging.info(f"PDFExtractor initialized for project '{self.project_name}' at path: {self.project_pdf_path}")

    def _get_pdf_files(self) -> List[Path]:
        """
        Finds and returns a sorted list of full paths to PDF files in the project directory.
        """
        pdf_files = sorted([f for f in self.project_pdf_path.glob('*.pdf') if f.is_file()])
        logging.info(f"Found {len(pdf_files)} PDF files in {self.project_pdf_path}")
        return pdf_files

    def _extract_text(self, pdf_path: Path) -> Tuple[str, Optional[int]]:
        """
        Extracts text from all pages of the PDF using PyMuPDF.

        Args:
            pdf_path: Path object for the PDF file.

        Returns:
            A tuple containing:
                - Extracted text (str). Empty string if extraction fails.
                - Page count (int | None). None if file cannot be opened.
        """
        full_text = ""
        page_count = None
        try:
            doc = fitz.open(pdf_path)
            page_count = doc.page_count
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                full_text += page.get_text("text") + "\n" # Add newline between pages
            doc.close()
            logging.debug(f"Successfully extracted text from {pdf_path.name} ({page_count} pages)")
            return full_text.strip(), page_count
        except Exception as e:
            logging.warning(f"Could not extract text from {pdf_path.name}: {e}")
            return "", page_count # Return empty string but potentially page count if known

    def _extract_tables(self, pdf_path: Path) -> List[List[List[str]]]:
        """
        Extracts tables from the PDF using Camelot.

        Args:
            pdf_path: Path object for the PDF file.

        Returns:
            A list of tables. Each table is a list of rows, and each row is a list of cell strings.
            Returns an empty list if no tables are found or extraction fails.
        """
        all_tables_data = []
        try:
            # Camelot works best with string paths
            pdf_path_str = str(pdf_path.resolve())
            # Try both lattice (for tables with clear lines) and stream (for tables without lines)
            # Process all pages using 'all'
            tables_lattice = camelot.read_pdf(pdf_path_str, pages='all', flavor='lattice', suppress_stdout=True, line_scale=40)
            tables_stream = camelot.read_pdf(pdf_path_str, pages='all', flavor='stream', suppress_stdout=True)

            for table_report in tables_lattice:
                # Convert DataFrame to List[List[str]]
                # Replace NaN/None with empty strings and ensure all are strings
                df_cleaned = table_report.df.fillna('').astype(str)
                all_tables_data.append(df_cleaned.values.tolist())

            for table_report in tables_stream:
                 # Convert DataFrame to List[List[str]]
                df_cleaned = table_report.df.fillna('').astype(str)
                all_tables_data.append(df_cleaned.values.tolist())

            logging.debug(f"Found {len(all_tables_data)} tables in {pdf_path.name} using Camelot")
            return all_tables_data
        except ImportError:
             logging.error("Camelot or its dependencies (like ghostscript, tk) might not be installed correctly.")
             return []
        except Exception as e:
            # Catch potential errors from Camelot, e.g., file parsing issues
            logging.warning(f"Could not extract tables from {pdf_path.name} using Camelot: {e}")
            return [] # Return empty list on failure

    def process_project_pdfs(self) -> List[ExtractedPDF]:
        """
        Processes all PDF files in the project directory, extracting text and tables.

        Returns:
            A list of ExtractedPDF objects, one for each PDF file found.
        """
        pdf_files = self._get_pdf_files()
        extracted_data_list = []

        if not pdf_files:
            logging.warning(f"No PDF files found in directory: {self.project_pdf_path}")
            return []

        for pdf_path in pdf_files:
            logging.info(f"Processing file: {pdf_path.name}")
            file_error = None
            extracted_text = ""
            extracted_tables = []
            page_count = None

            try:
                # Extract text and page count
                extracted_text, page_count = self._extract_text(pdf_path)

                # Extract tables (only if text extraction was somewhat successful)
                if page_count is not None: # Attempt table extraction only if PDF could be opened
                    extracted_tables = self._extract_tables(pdf_path)
                else:
                    file_error = "Could not open PDF to determine page count or extract text."
                    logging.warning(f"{pdf_path.name}: {file_error}")

            except Exception as e:
                logging.error(f"Unexpected error processing {pdf_path.name}: {e}")
                file_error = f"Unexpected error during processing: {str(e)}"

            # Create the Pydantic model instance
            pdf_data = ExtractedPDF(
                file_name=pdf_path.name,
                full_path=str(pdf_path.resolve()), # Store resolved path
                page_count=page_count,
                text=extracted_text,
                tables=extracted_tables,
                extraction_error=file_error
            )
            extracted_data_list.append(pdf_data)

        logging.info(f"Finished processing {len(extracted_data_list)} PDF files for project '{self.project_name}'.")
        return extracted_data_list

# --- Example Usage (Optional, can be run if script is executed directly) ---
if __name__ == '__main__':
    logging.info("Running PDFExtractor example...")
    try:
        # Ensure the example directories and files exist for testing
        EXAMPLE_BASE = Path("backend/data/raw_pdfs/")
        EXAMPLE_PROJECT = "v_metroway_test"
        example_project_path = EXAMPLE_BASE / EXAMPLE_PROJECT
        example_project_path.mkdir(parents=True, exist_ok=True)

        # Create dummy PDF files for testing if they don't exist
        pdf_path1 = example_project_path / "test1.pdf"
        pdf_path2 = example_project_path / "corrupted.pdf" # Example corrupted file
        if not pdf_path1.exists():
             # Create a simple PDF using reportlab (requires pip install reportlab)
             try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                c = canvas.Canvas(str(pdf_path1), pagesize=letter)
                c.drawString(100, 750, "This is page 1 text.")
                # Add a simple table structure
                c.drawString(100, 700, "Header1 | Header2")
                c.drawString(100, 680, "Data1   | Data2")
                c.showPage()
                c.drawString(100, 750, "This is page 2 text.")
                c.save()
                logging.info(f"Created dummy PDF: {pdf_path1}")
             except ImportError:
                 logging.warning("reportlab not installed. Cannot create dummy PDF for example.")
                 # Create empty file as placeholder if reportlab isn't installed
                 pdf_path1.touch()


        # Create an empty/potentially corrupt file
        if not pdf_path2.exists():
            with open(pdf_path2, "w") as f:
                f.write("This is not a valid PDF.")
            logging.info(f"Created dummy corrupted file: {pdf_path2}")


        # --- Run the extractor ---
        extractor = PDFExtractor(project_name=EXAMPLE_PROJECT, base_pdf_directory=str(EXAMPLE_BASE))
        extracted_data = extractor.process_project_pdfs()

        print("\n--- Extraction Results ---")
        for data in extracted_data:
            print(f"File: {data.file_name}")
            if data.extraction_error:
                print(f"  Error: {data.extraction_error}")
            else:
                print(f"  Pages: {data.page_count}")
                print(f"  Text Length: {len(data.text)}")
                print(f"  Tables Found: {len(data.tables)}")
                # print("  Tables:", data.tables) # Uncomment to see table data
            print("-" * 20)

    except FileNotFoundError as fnf_error:
        print(f"\nError during example execution: {fnf_error}")
    except Exception as ex:
        print(f"\nAn unexpected error occurred during example: {ex}")
        import traceback
        traceback.print_exc() 