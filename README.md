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

PDF processing follows this sequence:
1. User uploads PDF through the UI
2. PDF content is extracted via backend API
3. Content is stored in the active report
4. PDF metadata remains visible in the UI for reference
5. Stored content is used for AI report generation