from agency_swarm.tools import BaseTool
from pydantic import Field
import os
import pdfplumber


class ExtractPdfContentTool(BaseTool):
    """
    Verilen bir PDF dosyasından metin ve tablo içeriklerini çıkarır.
    Çıktı metin + markdown formatında tablo içerikleri olarak döner.
    """

    file_path: str = Field(..., description="PDF dosyasının tam dosya yolu")

    class ToolConfig:
        one_call_at_a_time = True

    def run(self) -> str:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"PDF dosyası bulunamadı: {self.file_path}")

        extracted_text = ""
        with pdfplumber.open(self.file_path) as pdf:
            if len(pdf.pages) == 0:
                raise ValueError("PDF dosyasında sayfa bulunamadı")

            for page_num, page in enumerate(pdf.pages, 1):
                extracted_text += f"\n## Sayfa {page_num}\n\n"

                page_text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
                if page_text:
                    page_text = page_text.replace('\x00', '')
                    extracted_text += page_text + "\n\n"

                tables = page.extract_tables()
                for table_num, table in enumerate(tables, 1):
                    extracted_text += f"### Tablo {table_num}:\n\n"
                    if table and len(table) > 0:
                        header = "| " + " | ".join([str(cell) if cell else "" for cell in table[0]]) + " |"
                        separator = "| " + " | ".join(["---"] * len(table[0])) + " |"
                        extracted_text += header + "\n" + separator + "\n"

                        for row in table[1:]:
                            row_text = "| " + " | ".join([str(cell) if cell else "" for cell in row]) + " |"
                            extracted_text += row_text + "\n"
                        extracted_text += "\n"

        return extracted_text.strip()
