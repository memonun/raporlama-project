from agency_swarm import Agent
from ceo_agent.tools.SavePdfReportTool import SavePdfReportTool
from ceo_agent.tools.UpdateReportStatusTool import UpdateReportStatusTool
class CeoAgent(Agent):
    def __init__(self):
        super().__init__(
            name="CeoAgent",
            description="Proje yönetimi, rapor oluşturma ve iletişim koordinasyonundan sorumlu CEO acentesi.",
            instructions="./instructions.md",
            tools=[SavePdfReportTool,UpdateReportStatusTool],
            parallel_tool_calls=False
        )


