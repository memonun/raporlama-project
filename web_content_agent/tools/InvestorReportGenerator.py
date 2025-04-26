from agency_swarm.tools import BaseTool
from pydantic import Field
import json
from dotenv import load_dotenv
load_dotenv()  # Load environment variables

class InvestorReportGenerator(BaseTool):
    """
    Bu araç, proje ve bileşen verilerini kullanarak yatırımcıya yönelik profesyonel bir rapor oluşturur.
    """
    project_name: str = Field(..., description="Proje adı")
    components_data: dict = Field(..., description="Bileşenlerin cevapları ve PDF içerikleri")
    
    class ToolConfig:
        one_call_at_a_time = True

    def run(self) -> dict:
        formatted_components = {}
        all_pdf_contents = []

        for comp_name, comp_data in self.components_data.items():
            formatted_answers = {}
            if 'answers' in comp_data and isinstance(comp_data['answers'], dict):
                for q_id, answer in comp_data['answers'].items():
                    is_pdf = False
                    pdf_data = None
                    if isinstance(answer, str):
                        try:
                            parsed = json.loads(answer)
                            if isinstance(parsed, dict) and 'fileName' in parsed:
                                pdf_data = parsed
                                is_pdf = True
                        except json.JSONDecodeError:
                            pass
                    elif isinstance(answer, dict) and 'fileName' in answer:
                        pdf_data = answer
                        is_pdf = True

                    if is_pdf and pdf_data:
                        all_pdf_contents.append({
                            "component": comp_name,
                            "fileName": pdf_data.get("fileName", ""),
                            "content": pdf_data.get("content", "")
                        })
                        formatted_answers[q_id] = f"(Yüklenen PDF: {pdf_data.get('fileName')})"
                    else:
                        formatted_answers[q_id] = str(answer)

                formatted_components[comp_name] = formatted_answers
            else:
                formatted_components[comp_name] = {}
# Bileşen verilerini JSON formatına dönüştür
        formatted_json = json.dumps(formatted_components, indent=2, ensure_ascii=False)
# Sistem talimatı
        system_prompt = """
        Sen profesyonel bir yatırımcı raporu hazırlama uzmanısın. 
        Verilen proje bilgilerini, departman verilerini, kullanıcı notlarını ve PDF içeriklerini kullanarak kapsamlı bir yatırımcı raporu oluştur.
        Rapor şu bölümleri içermelidir:

        1. Yönetici Özeti
        2. Proje Durumu
        3. Finansal Analiz
        4. İşletme Verileri
        5. Kısa ve Uzun Vadeli Tahminler
        6. Öneriler
        """

        user_prompt = f"""
        Proje: {self.project_name}

        Departman Verileri:
        {formatted_json}
        """

        if self.user_input:
            user_prompt += f"\n\nKullanıcı Notları:\n{self.user_input}"
# Bileşenlere ait PDF içeriklerini ekle
        if all_pdf_contents:
            user_prompt += "\n\n## Bileşen PDF İçerikleri:\n"
            for i, pdf in enumerate(all_pdf_contents, 1):
                content = pdf["content"]
                if len(content) > 10000:
                    content = content[:10000] + "...\n[İçerik kısaltıldı]"
                user_prompt += f"\n### {pdf['component']} - {pdf['fileName']}:\n{content}"

        # Hazırlanan prompt'ları döndür, agent kendisi completion'ı çağıracak
        return {
            "user_prompt": user_prompt,
            "system_prompt": system_prompt
        }


if __name__ == "__main__":
    # Test the tool
    # Not: Bu test artık doğrudan completion çağırmayacak, sadece prompt'ları üretecek.
    tool = InvestorReportGenerator(
        project_name="Test Project",
        components_data={
            "component1": {
                "answers": {
                    "q1": "Test answer 1",
                    "q2": "Test answer 2"
                }
            }
        },
        user_input="Test user notes"
    )
    result = tool.run()
    print(json.dumps(result, indent=2))
