from agency_swarm import Agent
from web_content_agent.tools.get_project_style_config_tool import GetProjectStyleConfigTool
from web_content_agent.tools.generate_dynamic_html_tool import GenerateDynamicHtmlTool
from web_content_agent.tools.process_images_for_report_tool import ProcessImagesForReportTool
from agency_swarm.tools import FileSearch
from web_content_agent.tools.InvestorReportGenerator import InvestorReportGenerator
import json
from pathlib import Path

class WebContentAgent(Agent):
    def __init__(self):
        super().__init__(
            name="WebContentAgent",
            description="Yapılandırılmış yatırımcı raporu içeriğini ve multimedya varlıklarını WeasyPrint ile uyumlu HTML'e dönüştürür.",
            instructions="instructions.md",
            # Web içeriği oluşturma acentesi için gerekli yapılandırmalar
            tools=[
                GenerateDynamicHtmlTool, 
                GetProjectStyleConfigTool, 
                ProcessImagesForReportTool,
                InvestorReportGenerator,
            ],
            files_folder=["../assets/images",],
            parallel_tool_calls=False,
            file_search={'max_num_results': 25},
            tool_resources={
                "file_search": [
                    "file-Dnup26R7LssPs2zxQJCmPB", 
                    "file-W1q9S9zFsJq4VVCpHPN65F"
                ]
            }
        )
    def response_validator(self, message: str) -> str:
        """
        Rapor oluşturma işleminin başarılı olup olmadığını kontrol eder.
        Başarısız olursa hata fırlatır.
        """
        try:
            # Mesajı JSON olarak parse etmeyi dene
            if isinstance(message, str) and "success" in message.lower():
                if "false" in message.lower() or "error" in message.lower():
                    raise ValueError("Rapor oluşturma işlemi başarısız oldu.")
                return message
            return message
        except Exception as e:
            raise ValueError(f"Rapor oluşturma işlemi sırasında bir hata oluştu: {str(e)}")    
    



    