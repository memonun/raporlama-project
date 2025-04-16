from agency_swarm import Agent
from web_content_agent.tools.get_project_style_config_tool import GetProjectStyleConfigTool
from web_content_agent.tools.generate_dynamic_html_tool import GenerateDynamicHtmlTool
from web_content_agent.tools.process_images_for_report_tool import ProcessImagesForReportTool

class WebContentAgent(Agent):
    def __init__(self):
        super().__init__(
            name="WebContentAgent",
            description="Yapılandırılmış yatırımcı raporu içeriğini ve multimedya varlıklarını WeasyPrint ile uyumlu HTML'e dönüştürür.",
            instructions="instructions.md",
            # Web içeriği oluşturma acentesi için gerekli yapılandırmalar
            tools=[GenerateDynamicHtmlTool, GetProjectStyleConfigTool, ProcessImagesForReportTool],
        )
