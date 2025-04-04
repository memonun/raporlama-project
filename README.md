# Raporlama Otomasyonu

AI-powered automated reporting system with PDF content extraction and processing capabilities.

## Features

- PDF file uploading and text extraction
- AI-based report generation
- Component-based report building
- Report finalization and management
- Email notifications for information requests

## Project Structure

- **Frontend**: React application with dynamic UI components
- **Backend**: FastAPI server handling data processing and AI integration

## Development Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The development server runs at `http://localhost:3000` and proxies API requests to the backend at `http://localhost:8000`.

## PDF Flow

PDF processing follows this standardized sequence:

1. **Upload**: User uploads PDF through the UI in ReportBuilder component
2. **Extraction**: PDF content is extracted via `/extract-pdf` or `/api/extract-pdf` endpoint
3. **Storage**: 
   - Content is stored directly in `active_report.pdf_content` field
   - Storage is handled by `save_component_data` function with special handling for "pdf_content" component
4. **Persistence**: 
   - PDF content is preserved across page refreshes
   - Accessible via `active_report.pdf_content` in project data
5. **Retrieval**: When generating reports, the PDF content is:
   - First checked in the incoming request
   - If not present, retrieved from `active_report.pdf_content`
   - If still not found, error is presented to user
6. **Processing**: The PDF content is passed to the AI for report generation
7. **Display**: PDF metadata (filename, size) is displayed in the UI for reference

### PDF Data Model
- The PDF content is stored as plain text in the `active_report.pdf_content` property
- PDF file metadata is stored in the UI state (not persisted)
- Component-specific PDFs are stored in their respective component data structures

### Error Handling
- Required PDF validation is performed before report generation
- User is notified if PDF upload fails or if required PDFs are missing
- Empty PDF content prompts appropriate error messages

## Özellikler

- 📊 Dört farklı proje için rapor oluşturma: V Mall, V Metroway, V Orman, V Statü
- 🔄 Accordion panel UI ile dört ana bileşeni yönetme: İşletme, Finans, İnşaat, Kurumsal İletişim
- ✅ Tamamlanmış ve eksik bileşenleri renk ile gösterme: Yeşil ✓ (Tamamlandı), Kırmızı ✗ (Eksik)
- 📝 Her bileşen için ilgili soru formlarını görüntüleme ve tamamlama
- 📧 Eksik bilgileri ilgili departmanlara e-posta ile gönderme
- 🤖 GPT-4 Turbo ile profesyonel rapor oluşturma
- 📄 Raporları PDF olarak kaydetme ve indirme

## Teknoloji Yığını

### Backend
- FastAPI (Python)
- OpenAI GPT-4 Turbo API
- ReportLab (PDF oluşturma)
- SQLAlchemy (Veritabanı ORM)
- Pydantic (Veri doğrulama)

### Frontend
- React + Vite
- TailwindCSS
- ShadCN UI / Radix UI
- React Router
- Axios

## Kurulum ve Çalıştırma

### Gereksinimler
- Python 3.8+
- Node.js 16+
- Docker ve Docker Compose (isteğe bağlı)

### Yerel Geliştirme
1. Repo'yu klonlayın:
   ```bash
   git clone https://github.com/kullanici/raporlama_otomasyonu.git
   cd raporlama_otomasyonu
   ```

2. Backend kurulumu:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Frontend kurulumu:
   ```bash
   cd frontend
   npm install
   ```

4. `.env` dosyasını oluşturun ve gerekli değişkenleri ekleyin:
   ```
   OPENAI_API_KEY=your_openai_api_key
   EMAIL_SENDER=your_email@example.com
   EMAIL_PASSWORD=your_email_password
   SMTP_SERVER=smtp.example.com
   SMTP_PORT=587
   ```

5. Backend'i çalıştırın:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

6. Frontend'i çalıştırın:
   ```bash
   cd frontend
   npm run dev
   ```

7. Tarayıcınızda `http://localhost:3000` adresine gidin.

### Docker ile Çalıştırma
1. Docker Compose ile tüm servisleri başlatın:
   ```bash
   docker-compose up -d
   ```

2. Tarayıcınızda `http://localhost:3000` adresine gidin.

## Kullanım

1. Ana sayfada bir proje seçin.
2. Rapor bileşenlerinden birini genişletmek için tıklayın.
3. İlgili soruları cevaplayın ve "Kaydet" düğmesine tıklayın.
4. Eksik bilgiler için "Eksik Bilgileri E-posta Gönder" seçeneğini kullanabilirsiniz.
5. Tüm bileşenler tamamlandığında "Rapor Oluştur" düğmesine tıklayın.
6. Oluşturulan raporu inceleyin ve "PDF Olarak İndir" düğmesine tıklayarak indirin.

## Lisans

Bu proje [MIT lisansı](LICENSE) altında lisanslanmıştır.