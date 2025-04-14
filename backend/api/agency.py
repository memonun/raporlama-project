from agency_swarm import Agency
from web_content_agent.web_content_agent import WebContentAgent
from investor_report_agent.investor_report_agent import InvestorReportAgent

# Acenteleri oluştur
web_content_agent = WebContentAgent()
investor_report_agent = InvestorReportAgent()

# Agency yapısını tanımla
agency = Agency(
    [
        web_content_agent,  # İlk acente kullanıcıyla iletişim için giriş noktası olacak
        [web_content_agent, investor_report_agent],  # Web Content Agent, Investor Report Agent ile iletişim kurabilir
    ],
    shared_instructions='agency_manifesto.md',  # Tüm acenteler için paylaşılan talimatlar
    temperature=0.7,  # Tüm acenteler için varsayılan sıcaklık
    max_prompt_tokens=20000  # Konuşma geçmişindeki maksimum token sayısı
)

# Demo çalıştırma
if __name__ == "__main__":
    agency.run_demo()  # Terminal üzerinde acente ağını başlatır
