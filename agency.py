import os
from agency_swarm import Agency
from agency_swarm import set_openai_key
from web_content_agent.web_content_agent import WebContentAgent
from investor_report_agent.investor_report_agent import InvestorReportAgent
from ceo_agent.ceo_agent import CeoAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# Set your API key
set_openai_key(os.getenv("OPENAI_API_KEY"))
# Acenteleri oluştur
ceo_agent = CeoAgent()
web_content_agent = WebContentAgent()
investor_report_agent = InvestorReportAgent()

# Agency yapısını tanımla
agency = Agency(
    [
        ceo_agent, 
        web_content_agent,
        investor_report_agent,
        [ceo_agent, web_content_agent],  # CEO, Web Content Agent ile iletişim kurabilir
        [ceo_agent, investor_report_agent],  # CEO, Investor Report Agent ile iletişim kurabilir
        [web_content_agent, investor_report_agent],  # Web Content Agent, Investor Report Agent ile iletişim kurabilir
    ],
    shared_instructions='agency_manifesto.md',  # Tüm acenteler için paylaşılan talimatlar
    temperature=0.7,  # Tüm acenteler için varsayılan sıcaklık
    max_prompt_tokens=20000  # Konuşma geçmişindeki maksimum token sayısı
)

# Demo çalıştırma
if __name__ == "__main__":
    agency.run_demo()  # Terminal üzerinde acente ağını başlatır
