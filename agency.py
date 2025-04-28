import os
from agency_swarm import Agency
from agency_swarm import set_openai_key
from web_content_agent.web_content_agent import WebContentAgent
from ceo_agent.ceo_agent import CeoAgent
from dotenv import load_dotenv
from pathlib import Path
import json
# Load environment variables
load_dotenv()
# Set your API key
set_openai_key(os.getenv("OPENAI_API_KEY"))
# Acenteleri oluştur
ceo_agent = CeoAgent()
web_content_agent = WebContentAgent()
PROJECT_ROOT = Path(__file__).resolve().parent  # adjust depending where this script is
CONFIG_FILE = PROJECT_ROOT / "project_assets.json"


agency = Agency(
    [
        ceo_agent, 
        web_content_agent,
        [ceo_agent, web_content_agent],  # CEO, Web Content Agent ile iletişim kurabilir
        
    ],
    shared_instructions='agency_manifesto.md',  # Tüm acenteler için paylaşılan talimatlar
    temperature=0.7,  # Tüm acenteler için varsayılan sıcaklık
    max_prompt_tokens=20000,  # Konuşma geçmişindeki maksimum token sayısı
   
)

# Demo çalıştırma
if __name__ == "__main__":
    agency.demo_gradio()  # Terminal üzerinde acente ağını başlatır


