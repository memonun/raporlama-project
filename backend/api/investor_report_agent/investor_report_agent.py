from agency_swarm import Agent

class InvestorReportAgent(Agent):
    def __init__(self):
        super().__init__(
            name="InvestorReportAgent",
            description="Yatırımcı raporları oluşturma ve finansal analiz konusunda uzman bir acente.",
            instructions="instructions.md",
            llm_model="gpt-4-turbo",
            # Yatırımcı raporu oluşturma acentesi için gerekli yapılandırmalar
            tools_folder="tools"
        )
