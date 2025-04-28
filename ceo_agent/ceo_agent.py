from agency_swarm import Agent
from agency_swarm.tools import FileSearch
class CeoAgent(Agent):
    def __init__(self):
        super().__init__(
            name="CeoAgent",
            description="Proje yönetimi, rapor oluşturma ve iletişim koordinasyonundan sorumlu CEO acentesi.",
            instructions="./instructions.md",
            tools=[FileSearch],

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
