from agency_swarm import Agent
from investor_report_agent.tools.ExtractPdfContentTool import ExtractPdfContentTool
from investor_report_agent.tools.InvestorReportGenerator import InvestorReportGenerator

class InvestorReportAgent(Agent):
    def __init__(self):
        super().__init__(
            name="InvestorReportAgent",
                  description="Yatırımcı raporları oluşturma ve finansal analiz konusunda uzman bir acente.",
                  instructions="./instructions.md",
                  # Yatırımcı raporu oluşturma acentesi için gerekli yapılandırmalar
                  tools=[
                      ExtractPdfContentTool,
                      InvestorReportGenerator
                  ],
                  
              )
