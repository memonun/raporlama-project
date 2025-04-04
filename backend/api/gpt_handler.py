import openai
import os
import pdfplumber
import asyncio
import httpx
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, validator, Field
from fpdf import FPDF
import json
from config import (
    OPENAI_API_KEY, GPT_MODEL, GPT_TEMPERATURE, GPT_MAX_TOKENS,
)
from fastapi import UploadFile, File, Form
from datetime import datetime
from openai import OpenAI

# OpenAI API anahtarını ayarla
openai.api_key = OPENAI_API_KEY
print("OpenAI API anahtarı başarıyla ayarlandı")

# Sabitler
MAX_TOKEN_LIMIT = 4000  # gpt-4-turbo için maksimum token limiti
DEFAULT_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FALLBACK_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"

def calculate_tokens(text: str) -> int:
    """Yaklaşık token sayısını hesapla"""
    return len(text.split()) * 1.3  # Ortalama token/kelime oranı

def split_content(content: str, max_tokens: int = 4000) -> List[str]:
    """İçeriği token limitine göre böl"""
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for sentence in content.split('. '):
        sentence_tokens = calculate_tokens(sentence)
        if current_tokens + sentence_tokens > max_tokens:
            chunks.append('. '.join(current_chunk) + '.')
            current_chunk = [sentence]
            current_tokens = sentence_tokens
        else:
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
    
    if current_chunk:
        chunks.append('. '.join(current_chunk) + '.')
    
    return chunks

# Pydantic Modelleri
class AIRequest(BaseModel):
    user_input: Optional[str] = Field(None, description="Kullanıcının girdiği metin")
    pdf_content: Optional[str] = Field(None, description="PDF'ten çıkarılan içerik")
    project_name: Optional[str] = Field(None, description="Proje adı")
    components_data: Optional[Dict[str, Dict[str, str]]] = Field(None, description="Bileşen verileri")

    @validator('user_input', 'pdf_content')
    def check_empty(cls, value):
        if value is not None and value.strip() == '':
            raise ValueError('Metin içeriği boş olamaz.')
        return value

class AIResponse(BaseModel):
    combined_output: Optional[str] = Field(None, description="Birleştirilmiş çıktı")
    pdf_path: Optional[str] = Field(None, description="Oluşturulan PDF'in yolu")
    error: Optional[str] = Field(None, description="Hata mesajı")

class OpenAIMessage(BaseModel):
    role: str
    content: str

class OpenAIRequest(BaseModel):
    model: str = GPT_MODEL
    messages: List[OpenAIMessage]
    temperature: float = GPT_TEMPERATURE
    max_tokens: int = GPT_MAX_TOKENS

def create_chat_completion(model: str, messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> str:
    """
    OpenAI API için chat completion fonksiyonu
    """
    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "text"},
            presence_penalty=0.0,
            frequency_penalty=0.0,
            seed=42  # Tutarlı yanıtlar için
        )
        return response.choices[0].message.content
    except openai.RateLimitError as e:
        print(f"Rate limit aşıldı: {e}")
        raise
    except openai.APIError as e:
        print(f"API hatası: {e}")
        raise
    except Exception as e:
        print(f"Beklenmeyen hata: {e}")
        raise

def check_font_availability() -> str:
    """
    Sistemde DejaVu fontunun varlığını kontrol eder.
    
    Returns:
        Kullanılabilir font dosyasının yolu
    """
    if os.path.exists(DEFAULT_FONT_PATH):
        return DEFAULT_FONT_PATH
    elif os.path.exists(FALLBACK_FONT_PATH):
        return FALLBACK_FONT_PATH
    else:
        raise Exception("DejaVu fontu bulunamadı. Lütfen font dosyalarını yükleyin.")

def split_content_by_sentences(content: str) -> List[str]:
    """
    İçeriği cümle bazlı olarak böler.
    
    Args:
        content: Bölünecek içerik
        
    Returns:
        Cümlelerden oluşan liste
    """
    # Basit cümle ayırıcı (nokta, ünlem, soru işareti)
    sentences = []
    current_sentence = ""
    
    for char in content:
        current_sentence += char
        if char in '.!?':
            sentences.append(current_sentence.strip())
            current_sentence = ""
    
    if current_sentence.strip():
        sentences.append(current_sentence.strip())
    
    return sentences

def create_content_chunks(sentences: List[str], max_chunk_size: int) -> List[str]:
    """
    Cümleleri belirli bir boyutta parçalara böler.
    
    Args:
        sentences: Cümleler listesi
        max_chunk_size: Maksimum parça boyutu
        
    Returns:
        İçerik parçaları
    """
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_size = len(sentence.split())
        if current_size + sentence_size > max_chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_size = sentence_size
        else:
            current_chunk.append(sentence)
            current_size += sentence_size
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

async def handle_rate_limit(func):
    """Rate limiting için exponential backoff uygula"""
    max_retries = 3
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            return await func()
        except openai.RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)  # exponential backoff
            print(f"Rate limit aşıldı. {delay} saniye bekleniyor...")
            await asyncio.sleep(delay)

async def process_text_request_async(content: str, role: str = 'kurumsal raporlama') -> str:
    """
    Asenkron olarak metin işleme isteği gönderir.
    """
    system_roles = {
        'kurumsal raporlama': 'Sen kurumsal dilde raporlar yazan bir asistansın.',
        'teknik': 'Sen teknik verileri analiz eden bir uzmansın.',
        'finans': 'Sen finansal verileri yorumlayan bir finans uzmanısın.',
        'özet': 'Sen karmaşık metinleri özetleyen bir uzmansın.'
    }
    
    system_content = system_roles.get(role, system_roles['kurumsal raporlama'])
    
    async def make_request():
        return await asyncio.to_thread(
            create_chat_completion,
            GPT_MODEL,
            [{"role": "system", "content": system_content},
             {"role": "user", "content": content}],
            GPT_TEMPERATURE,
            int(GPT_MAX_TOKENS / 2)
        )
    
    try:
        return await handle_rate_limit(make_request)
    except Exception as e:
        error_msg = f'Asenkron işlem hatası: {str(e)}'
        print(error_msg)
        return error_msg

def create_storage_path(project_name: str) -> str:
    """
    Proje için depolama yolunu oluşturur.
    
    Args:
        project_name: Proje adı
        
    Returns:
        Proje klasörünün yolu
    """
    base_path = "pdf_reports"
    project_path = os.path.join(base_path, project_name)
    
    if not os.path.exists(project_path):
        os.makedirs(project_path)
        print(f"Proje klasörü oluşturuldu: {project_path}")
    
    return project_path

def ensure_reports_directory() -> str:
    """
    PDF raporları için ana klasörün varlığını kontrol eder ve gerekirse oluşturur.
    
    Returns:
        Ana raporlar klasörünün yolu
    """
    reports_dir = "pdf_reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
        print(f"Ana raporlar klasörü oluşturuldu: {reports_dir}")
    return reports_dir

def save_report_path(project_name: str, pdf_path: str) -> None:
    """
    PDF dosya yolunu JSON dosyasına kaydeder.
    
    Args:
        project_name: Proje adı
        pdf_path: PDF dosyasının yolu
    """
    try:
        # PDF dosya adını al
        pdf_filename = os.path.basename(pdf_path)
        
        report_data = {
            "project_name": project_name,
            "pdf_path": pdf_path,
            "pdf_filename": pdf_filename,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_finalized": False
        }
        
        # JSON dosyasının varlığını kontrol et
        if not os.path.exists('report_data.json'):
            with open('report_data.json', 'w') as f:
                json.dump([], f)
        
        # Mevcut verileri oku
        with open('report_data.json', 'r') as f:
            reports = json.load(f)
        
        # Eğer aynı proje için önceki bir rapor varsa güncelle, yoksa ekle
        found = False
        for i, report in enumerate(reports):
            if report["project_name"] == project_name and not report["is_finalized"]:
                reports[i] = report_data
                found = True
                break
        
        if not found:
            # Yeni raporu ekle
            reports.append(report_data)
        
        # Güncellenmiş verileri kaydet
        with open('report_data.json', 'w') as f:
            json.dump(reports, f, indent=2)
            
        print(f"PDF dosya yolu kaydedildi: {pdf_path}")
        return report_data
    except Exception as e:
        print(f"PDF dosya yolu kaydedilirken hata: {str(e)}")
        return None

def create_pdf(content: str, project_name: str) -> str:
    """
    İçeriği PDF olarak oluşturur ve kaydeder.
    
    Args:
        content: PDF içeriği
        project_name: Proje adı (dosya adı için)
        
    Returns:
        Oluşturulan PDF dosyasının yolu
    """
    # Proje klasörünün varlığını kontrol et
    project_dir = create_storage_path(project_name)
    
    # Tarih formatındaki PDF dosya adını oluştur
    current_date = datetime.now().strftime("%Y%m%d")
    safe_project_name = project_name.replace(" ", "_")
    pdf_filename = f"{safe_project_name}__{current_date}.pdf"
    pdf_path = os.path.join(project_dir, pdf_filename)
    
    try:
        # Kullanılabilir font kontrolü
        font_path = check_font_availability()
        
        # PDF oluştur
        pdf = FPDF()
        pdf.add_page()
        
        # DejaVu font eklemesi (Türkçe karakterler için)
        pdf.add_font('DejaVu', '', font_path, uni=True)
        pdf.set_font('DejaVu', '', 12)
        
        # İçeriği PDF'e ekle
        pdf.multi_cell(0, 10, content)
        
        # PDF'i kaydet
        pdf.output(pdf_path)
        print(f"PDF başarıyla oluşturuldu: {pdf_path}")
        
        # PDF yolunu kaydet
        report_data = save_report_path(project_name, pdf_path)
        
        return pdf_path
    except Exception as e:
        error_msg = f"PDF oluşturulurken hata: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)

def generate_pdf_filename(project_name: str) -> str:
    """
    PDF dosyası için benzersiz bir isim oluşturur.
    
    Args:
        project_name: Proje adı
        
    Returns:
        Oluşturulan dosya adı
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_project_name = project_name.replace(" ", "_")
    return f"{safe_project_name}__{date_str}.pdf"

def process_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gelen isteği değerlendirir ve OpenAI API'a gönderir.
    Hem text field verilerini hem de PDF verilerini işleyebilir.
    
    Args:
        data: İşlenecek veri (metin veya PDF içeriği)
        
    Returns:
        İşlenmiş veri sonuçları
    """
    try:
        # Gelen veriyi Pydantic modeline dönüştür
        request_data = AIRequest(**data)
        combined_input = ""

        # Proje raporu oluşturma isteği varsa
        if request_data.project_name and request_data.components_data:
            report_content = generate_report(request_data.project_name, request_data.components_data, request_data.user_input, request_data.pdf_content)
            combined_input += f"Proje Raporu:\n{report_content}\n\n"

        # Kullanıcı metni varsa
        if request_data.user_input:
            combined_input += f"Kullanıcı Metni:\n{request_data.user_input}\n\n"

        # PDF içeriği varsa
        if request_data.pdf_content:
            combined_input += f"PDF İçeriği:\n{request_data.pdf_content}\n\n"

        # İçeriği token limitine göre böl
        chunks = split_content(combined_input, max_tokens=GPT_MAX_TOKENS)

        # Her parçayı işle
        outputs = []
        for chunk in chunks:
            output = create_chat_completion(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "Sen profesyonel raporlar hazırlayan bir asistansın."},
                    {"role": "user", "content": chunk}
                ],
                temperature=GPT_TEMPERATURE,
                max_tokens=int(GPT_MAX_TOKENS / 2)
            )
            outputs.append(output)
        
        # Sonuçları birleştir
        combined_output = "\n\n".join(outputs)

        # PDF oluştur
        project_name = request_data.project_name or "rapor"
        pdf_path = create_pdf(combined_output, project_name)

        # Yanıtı Pydantic modeline dönüştür
        response_data = AIResponse(
            combined_output=combined_output,
            pdf_path=pdf_path
        )

        return response_data.dict()
    except Exception as e:
        return AIResponse(error=str(e)).dict()

def generate_report(project_name: str, components_data: Dict[str, Dict[str, Any]], user_input: Optional[str] = None, pdf_content: Optional[str] = None) -> str:
    """
    Proje, bileşen, kullanıcı notu ve PDF verilerini kullanarak GPT ile rapor oluşturur.
    
    Args:
        project_name: Proje adı
        components_data: Her bileşen için soru-cevap verilerini içeren sözlük (string veya dosya nesnesi içerebilir)
        user_input: Kullanıcının eklediği notlar (opsiyonel)
        pdf_content: Genel PDF'ten çıkarılan metin içeriği (opsiyonel)
        
    Returns:
        Oluşturulan rapor metni
    """
    # Verileri düzenli bir formata getir (Dosya nesnelerini filename ile değiştir)
    formatted_components = {}
    for comp_name, comp_answers in components_data.items():
        formatted_answers = {}
        for q_id, answer in comp_answers.items():
            if isinstance(answer, dict) and 'filename' in answer:
                formatted_answers[q_id] = f"(Yüklenen Dosya: {answer['filename']})"
            else:
                formatted_answers[q_id] = str(answer) # Ensure string
        formatted_components[comp_name] = formatted_answers

    formatted_data = json.dumps(formatted_components, indent=2, ensure_ascii=False)
    
    # Sistem talimatı (aynı kalabilir)
    system_instruction = """
    Sen profesyonel bir yatırımcı raporu hazırlama uzmanısın. 
    Verilen proje bilgilerini, departman verilerini, kullanıcı notlarını ve ek PDF içeriğini kullanarak kapsamlı bir yatırımcı raporu oluştur.
    Rapor şu bölümleri içermelidir:
    
    1. Yönetici Özeti
    2. Proje Durumu
    3. Finansal Analiz
    4. İşletme Verileri
    5. Kısa ve Uzun Vadeli Tahminler
    6. Öneriler
    
    Raporun profesyonel, bilgilendirici ve yatırımcılar için değerli içgörüler sağlayacak şekilde olmalıdır.
    """
    
    # Kullanıcı mesajı (userInput ve pdfContent eklendi)
    user_message = f"""
    Proje: {project_name}
    
    Departman Verileri:
    {formatted_data}
    """

    if user_input:
        user_message += f"\n\nKullanıcı Notları:\n{user_input}"

    if pdf_content:
        user_message += f"\n\nEk PDF İçeriği:\n{pdf_content}"
        
    user_message += "\n\nLütfen bu bilgilere dayanarak kapsamlı bir yatırımcı raporu oluştur."
    
    try:
        # OpenAI API çağrısı
        response = create_chat_completion(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_message}
            ],
            temperature=GPT_TEMPERATURE,
            max_tokens=GPT_MAX_TOKENS
        )
        
        return response
        
    except Exception as e:
        error_msg = f"GPT raporu oluşturulurken hata: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)

def analyze_component_completion(answers: Dict[str, str], questions: list) -> Dict[str, Any]:
    """
    Bir bileşenin tamamlanma durumunu analiz eder ve eksik bilgileri belirler.
    
    Args:
        answers: Kullanıcı tarafından sağlanan cevaplar
        questions: Bileşene ait sorular listesi
        
    Returns:
        Tamamlanma durumu ve eksik bilgiler
    """
    total_questions = len(questions)
    answered_questions = 0
    missing_info = []
    
    for question in questions:
        question_id = question["id"]
        if question_id in answers and answers[question_id].strip():
            answered_questions += 1
        elif question.get("required", False):
            missing_info.append(question["text"])
    
    completion_percentage = int((answered_questions / total_questions) * 100) if total_questions > 0 else 0
    status = "completed" if completion_percentage == 100 else "incomplete"
    
    return {
        "status": status,
        "completion_percentage": completion_percentage,
        "missing_info": missing_info
    }

def extract_pdf_content(file_path: str) -> str:
    """
    PDF dosyasından metin ve tablo içeriğini çıkarır, tabloları markdown formatında düzenler.
    
    Args:
        file_path: PDF dosyasının yolu
        
    Returns:
        Çıkarılan metin içeriği (markdown formatında tablolar içerir)
    """
    extracted_text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Sayfa numarası ekle
                extracted_text += f"\n## Sayfa {page_num}\n\n"
                
                # Metinleri Ayıkla
                page_text = page.extract_text() or ""
                if page_text:
                    extracted_text += page_text + "\n\n"

                # Tabloları Markdown formatında ayıkla
                tables = page.extract_tables()
                if tables:
                    for table_num, table in enumerate(tables, 1):
                        extracted_text += f"\n### Tablo {table_num}:\n\n"
                        
                        # Tablo başlığını oluştur
                        if table and len(table) > 0:
                            header = "| " + " | ".join([str(cell) if cell else "" for cell in table[0]]) + " |"
                            separator = "| " + " | ".join(["---" for _ in table[0]]) + " |"
                            extracted_text += header + "\n" + separator + "\n"
                            
                            # Tablo içeriğini ekle
                            for row in table[1:]:
                                row_text = "| " + " | ".join([str(cell) if cell else "" for cell in row]) + " |"
                                extracted_text += row_text + "\n"
                            
                            extracted_text += "\n"
    except Exception as e:
        raise Exception(f"PDF içeriği çıkarılırken hata: {str(e)}")
    
    return extracted_text.strip()

def process_text_request(content: str, role: str = 'kurumsal raporlama') -> str:
    """
    Kullanıcıdan gelen metin girdisini OpenAI API'ına gönderir ve sonucu döndürür.
    
    Args:
        content: İşlenecek metin içeriği
        role: Asistanın rolü/talimatı
        
    Returns:
        İşlenmiş metin çıktısı
    """
    system_roles = {
        'kurumsal raporlama': 'Sen kurumsal dilde raporlar yazan bir asistansın.',
        'teknik': 'Sen teknik verileri analiz eden bir uzmansın.',
        'finans': 'Sen finansal verileri yorumlayan bir finans uzmanısın.',
        'özet': 'Sen karmaşık metinleri özetleyen bir uzmansın.'
    }
    
    system_content = system_roles.get(role, system_roles['kurumsal raporlama'])
    
    try:
        # OpenAI API çağrısı için Pydantic modeli oluştur
        request = OpenAIRequest(
            model=GPT_MODEL,
            messages=[
                OpenAIMessage(role="system", content=system_content),
                OpenAIMessage(role="user", content=content)
            ],
            temperature=GPT_TEMPERATURE,
            max_tokens=int(GPT_MAX_TOKENS / 2)
        )
        
        # API çağrısını yap
        response = create_chat_completion(
            request.model,
            [{"role": m.role, "content": m.content} for m in request.messages],
            request.temperature,
            request.max_tokens
        )
        
        return response.strip()
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = f'OpenAI API hatası: {str(e)}'
        print(error_msg)
        return error_msg

async def process_report_request(user_input: str = None, pdf_content: str = None, project_name: str = "rapor") -> dict:
    """
    Rapor işleme isteğini asenkron olarak yönetir.
    """
    try:
        if not user_input and not pdf_content:
            return AIResponse(error="Kullanıcı girişi veya PDF içeriği gerekli").dict()
        
        processed_content = ""
        if pdf_content:
            processed_content = await process_pdf_content_async(pdf_content)
        
        if user_input:
            if processed_content:
                processed_content = f"{processed_content}\n\nKullanıcı Notu: {user_input}"
            else:
                processed_content = user_input
        
        # İçeriği analiz et
        analysis = await analyze_content_async(processed_content)
        
        # PDF oluştur
        pdf_path = create_pdf(processed_content, project_name)
        
        return AIResponse(
            combined_output=processed_content,
            pdf_path=pdf_path,
            success=True
        ).dict()
        
    except Exception as e:
        error_msg = f"Rapor işleme hatası: {str(e)}"
        print(error_msg)
        return AIResponse(error=error_msg).dict()

async def process_pdf_content_async(pdf_content: str) -> str:
    """
    PDF içeriğini asenkron olarak işler.
    """
    try:
        # PDF içeriğini token limitine göre böl
        chunks = split_content(pdf_content, MAX_TOKEN_LIMIT)
        
        processed_chunks = []
        for chunk in chunks:
            # Her chunk için OpenAI API çağrısı yap
            response = await asyncio.to_thread(
                create_chat_completion,
                GPT_MODEL,
                [
                    {"role": "system", "content": "Sen profesyonel raporlar hazırlayan bir asistansın."},
                    {"role": "user", "content": chunk}
                ],
                GPT_TEMPERATURE,
                int(GPT_MAX_TOKENS / 2)
            )
            processed_chunks.append(response)
        
        # İşlenmiş chunkları birleştir
        return '\n\n'.join(processed_chunks)
    except Exception as e:
        error_msg = f'PDF işleme hatası: {str(e)}'
        print(error_msg)
        return error_msg

async def analyze_content_async(content: str, analysis_type: str = 'summary') -> str:
    """
    İçeriği asenkron olarak analiz eder.
    """
    analysis_roles = {
        'summary': 'özet',
        'technical': 'teknik',
        'financial': 'finans'
    }
    
    role = analysis_roles.get(analysis_type, 'özet')
    
    try:
        # İçeriği token limitine göre böl
        chunks = split_content(content, MAX_TOKEN_LIMIT)
        
        analyzed_chunks = []
        for chunk in chunks:
            # Her chunk için asenkron işlem yap
            analyzed_chunk = await process_text_request_async(
                chunk,
                role=role
            )
            analyzed_chunks.append(analyzed_chunk)
        
        # Analiz edilmiş chunkları birleştir
        return '\n\n'.join(analyzed_chunks)
    except Exception as e:
        error_msg = f'İçerik analiz hatası: {str(e)}'
        print(error_msg)
        return error_msg

async def test_complete_system():
    """
    Tüm sistemin kapsamlı testini gerçekleştirir.
    """
    try:
        print("\n=== PDF Rapor Sistemi Testi Başlıyor ===\n")
        
        # Test 1: PDF Dosya Adı Oluşturma
        print("1. PDF Dosya Adı Oluşturma Testi")
        test_project = "Test Projesi 123"
        pdf_filename = generate_pdf_filename(test_project)
        print(f"Oluşturulan dosya adı: {pdf_filename}")
        assert "Test_Projesi_123" in pdf_filename, "Dosya adı proje adını içermiyor"
        assert datetime.now().strftime("%Y-%m-%d") in pdf_filename, "Dosya adı tarih içermiyor"
        print("✓ Dosya adı testi başarılı\n")
        
        # Test 2: Klasör Oluşturma
        print("2. Klasör Oluşturma Testi")
        storage_path = create_storage_path(test_project)
        print(f"Oluşturulan klasör: {storage_path}")
        assert os.path.exists(storage_path), "Klasör oluşturulamadı"
        print("✓ Klasör oluşturma testi başarılı\n")
        
        # Test 3: PDF Oluşturma
        print("3. PDF Oluşturma Testi")
        test_content = "Bu bir test içeriğidir.\n\nTest başlığı\n- Madde 1\n- Madde 2"
        pdf_path = create_pdf(test_content, test_project)
        print(f"Oluşturulan PDF: {pdf_path}")
        assert os.path.exists(pdf_path), "PDF dosyası oluşturulamadı"
        print("✓ PDF oluşturma testi başarılı\n")
        
        # Test 4: JSON Kayıt
        print("4. JSON Kayıt Testi")
        assert os.path.exists('report_data.json'), "JSON dosyası oluşturulamadı"
        with open('report_data.json', 'r') as f:
            reports = json.load(f)
        print(f"JSON içeriği: {json.dumps(reports, indent=2)}")
        assert any(report["pdf_path"] == pdf_path for report in reports), "PDF yolu JSON'a kaydedilmedi"
        print("✓ JSON kayıt testi başarılı\n")
        
        # Test 5: Rapor Listeleme
        print("5. Rapor Listeleme Testi")
        project_reports = get_project_reports(test_project)
        print(f"Proje raporları: {json.dumps(project_reports, indent=2)}")
        assert len(project_reports) > 0, "Proje raporları bulunamadı"
        print("✓ Rapor listeleme testi başarılı\n")
        
        # Test 6: Rapor Durumu Güncelleme
        print("6. Rapor Durumu Güncelleme Testi")
        success = update_report_status(pdf_path, True)
        print(f"Durum güncelleme sonucu: {success}")
        assert success, "Rapor durumu güncellenemedi"
        
        # Güncellenmiş durumu kontrol et
        updated_reports = get_project_reports(test_project)
        updated_report = next((r for r in updated_reports if r["pdf_path"] == pdf_path), None)
        assert updated_report and updated_report["is_finalized"], "Rapor durumu doğru güncellenmedi"
        print("✓ Rapor durumu güncelleme testi başarılı\n")
        
        # Test 7: Çoklu PDF Oluşturma
        print("7. Çoklu PDF Oluşturma Testi")
        test_content2 = "İkinci test içeriği"
        pdf_path2 = create_pdf(test_content2, test_project)
        print(f"İkinci PDF oluşturuldu: {pdf_path2}")
        assert pdf_path != pdf_path2, "İkinci PDF benzersiz değil"
        print("✓ Çoklu PDF testi başarılı\n")
        
        # Test 8: Hata Durumları
        print("8. Hata Durumları Testi")
        try:
            # Geçersiz proje adı
            create_pdf("test", "")
            assert False, "Boş proje adı kabul edildi"
        except Exception as e:
            print(f"✓ Boş proje adı hatası yakalandı: {str(e)}")
            
        try:
            # Geçersiz dosya yolu
            update_report_status("olmayan/dosya.pdf", True)
            assert False, "Geçersiz dosya yolu kabul edildi"
        except Exception as e:
            print(f"✓ Geçersiz dosya yolu hatası yakalandı: {str(e)}")
        
        print("\n=== Tüm Testler Başarıyla Tamamlandı ===\n")
        return "Tüm testler başarıyla tamamlandı."
        
    except AssertionError as e:
        error_msg = f"Test hatası: {str(e)}"
        print(f"\n❌ {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Beklenmeyen hata: {str(e)}"
        print(f"\n❌ {error_msg}")
        return error_msg

# Test fonksiyonunu çalıştır
if __name__ == "__main__":
    asyncio.run(test_complete_system())

def get_project_reports(project_name: str) -> List[Dict[str, Any]]:
    """
    Belirli bir projeye ait tüm raporları getirir.
    
    Args:
        project_name: Proje adı
        
    Returns:
        Projeye ait raporların listesi
    """
    try:
        if not os.path.exists('report_data.json'):
            return []
            
        with open('report_data.json', 'r') as f:
            reports = json.load(f)
            
        # Projeye ait raporları filtrele
        project_reports = [report for report in reports if report["project_name"] == project_name]
        
        return project_reports
    except Exception as e:
        error_msg = f"Raporlar getirilirken hata: {str(e)}"
        print(error_msg)
        return []

def update_report_status(pdf_path: str, is_finalized: bool = True) -> bool:
    """
    Raporun durumunu günceller.
    
    Args:
        pdf_path: PDF dosyasının yolu
        is_finalized: Raporun finalize edilip edilmediği
        
    Returns:
        Güncelleme başarılı ise True, değilse False
    """
    try:
        if not os.path.exists('report_data.json'):
            return False
            
        with open('report_data.json', 'r') as f:
            reports = json.load(f)
            
        # Raporu bul ve güncelle
        for report in reports:
            if report["pdf_path"] == pdf_path:
                report["is_finalized"] = is_finalized
                break
        else:
            return False
            
        # Güncellenmiş verileri kaydet
        with open('report_data.json', 'w') as f:
            json.dump(reports, f, indent=2, ensure_ascii=False)
            
        return True
    except Exception as e:
        error_msg = f"Rapor durumu güncellenirken hata: {str(e)}"
        print(error_msg)
        return False 