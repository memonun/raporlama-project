import json
from typing import List, Dict, Any, Optional
import os
from pathlib import Path

# Sorular için sabit JSON yapısı (production'da bir veritabanında veya JSON dosyasında tutulabilir)
COMPONENT_QUESTIONS = {
    "İşletme": [
        {
            "id": "business_revenue",
            "text": "Aylık gelir bilgisi (TL):",
            "type": "text",
            "required": False
        },
        {
            "id": "business_expenses",
            "text": "Aylık gider bilgisi (TL):",
            "type": "text",
            "required": False
        },
        {
            "id": "business_details",
            "text": "İşletme ile ilgili önemli bilgiler:",
            "type": "textarea",
            "required": False
        },
        {
            "id": "business_report",
            "text": "İşletme raporu PDF dosyası:",
            "type": "file",
            "required": True
        }
    ],
    "Finans": [
        {
            "id": "currency_info",
            "text": "Dönemsel getiri bilgisi (USD/TL):",
            "type": "text",
            "required": False
        },
        {
            "id": "investment_return",
            "text": "Yatırım getiri oranı (%):",
            "type": "text",
            "required": False
        },
        {
            "id": "finance_details",
            "text": "Finansal performans detayları:",
            "type": "textarea",
            "required": False
        },
        {
            "id": "finance_report",
            "text": "Finansal rapor PDF dosyası:",
            "type": "file",
            "required": True
        }
    ],
    "İnşaat": [
        {
            "id": "construction_progress",
            "text": "İnşaat ilerleme durumu (%):",
            "type": "text",
            "required": False
        },
        {
            "id": "construction_completion",
            "text": "Tahmini tamamlanma tarihi:",
            "type": "text",
            "required": False
        },
        {
            "id": "construction_details",
            "text": "İnşaat ilerleme bilgileri:",
            "type": "textarea",
            "required": False
        },
        {
            "id": "construction_images",
            "text": "İnşaat görsel raporu:",
            "type": "file",
            "required": True
        }
    ],
    "Kurumsal İletişim": [
        {
            "id": "media_coverage",
            "text": "Medya görünürlüğü bilgisi:",
            "type": "select",
            "options": [
                { "value": "low", "label": "Düşük" },
                { "value": "medium", "label": "Orta" },
                { "value": "high", "label": "Yüksek" }
            ],
            "required": False
        },
        {
            "id": "positive_outlook",
            "text": "Kısa vadeli ekonomik beklentiler:",
            "type": "textarea",
            "required": False
        },
        {
            "id": "corporate_events",
            "text": "Yaklaşan kurumsal etkinlikler:",
            "type": "textarea",
            "required": False
        },
        {
            "id": "corporate_report",
            "text": "Kurumsal iletişim raporu:",
            "type": "file",
            "required": True
        }
    ]
}

def get_questions_for_component(component_name: str) -> List[Dict[str, Any]]:
    """
    Belirli bir bileşen için soruları döndürür.
    
    Args:
        component_name: Bileşen adı
        
    Returns:
        Bileşene ait sorular listesi
    """
    return COMPONENT_QUESTIONS.get(component_name, [])

def save_question_answer(component_name: str, question_id: str, answer: str) -> bool:
    """
    Bir soruya verilen cevabı kaydeder (örnek implementasyon).
    Production'da bir veritabanına kaydedilebilir.
    
    Args:
        component_name: Bileşen adı
        question_id: Soru ID'si
        answer: Cevap
        
    Returns:
        İşlem başarı durumu
    """
    # Burada veritabanına kaydetme işlemi yapılabilir
    # Şimdilik sadece başarılı olduğunu varsayıyoruz
    return True

def get_answers_for_component(component_name: str, project_name: str) -> Dict[str, str]:
    """
    Belirli bir bileşen ve proje için kaydedilmiş cevapları döndürür (örnek implementasyon).
    Production'da bir veritabanından çekilebilir.
    
    Args:
        component_name: Bileşen adı
        project_name: Proje adı
        
    Returns:
        Bileşene ait cevaplar sözlüğü
    """
    # Burada veritabanından çekme işlemi yapılabilir
    # Şimdilik boş bir sözlük döndürüyoruz
    return {} 