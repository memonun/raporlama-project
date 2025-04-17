from agency_swarm import Agent

class CeoAgent(Agent):
    def __init__(self):
        super().__init__(
            name="CeoAgent",
            description="Proje yönetimi, rapor oluşturma ve iletişim koordinasyonundan sorumlu CEO acentesi.",
            instructions="./instructions.md",
            tools=[]
        )


