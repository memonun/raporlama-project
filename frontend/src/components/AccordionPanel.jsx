import { useState, useEffect } from 'react';
import * as Accordion from '@radix-ui/react-accordion';
import { ChevronDown, Check, X, FileText, Upload } from 'lucide-react';
import ProgressIndicator from './ProgressIndicator';
import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export default function AccordionPanel({
  componentName,
  projectName,
  isOpen,
  onOpenChange,
  onSaveSuccess,
  onEmailRequest
}) {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const [isSaving, setSaving] = useState(false);
  const [uploadFiles, setUploadFiles] = useState({});

  // Bileşen için soruları yükle
  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/questions/${componentName}`);
        setQuestions(response.data.questions);
        setLoading(false);
      } catch (err) {
        setError('Sorular yüklenirken bir hata oluştu.');
        setLoading(false);
        console.error('Sorular yüklenirken hata:', err);
      }
    };

    fetchQuestions();
  }, [componentName]);

  // İlerleme durumunu hesapla
  useEffect(() => {
    if (questions.length === 0) return;

    const requiredQuestions = questions.filter(q => q.required);
    if (requiredQuestions.length === 0) {
      setProgress(100);
      return;
    }

    let answeredCount = 0;
    for (const q of requiredQuestions) {
      if (answers[q.id] && answers[q.id].trim() !== '') {
        answeredCount++;
      }
    }

    const calculatedProgress = Math.floor((answeredCount / requiredQuestions.length) * 100);
    setProgress(calculatedProgress);
  }, [answers, questions]);

  // Cevapları değiştirme
  const handleAnswerChange = (questionId, value) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  // Dosya yükleme
  const handleFileUpload = (questionId, files) => {
    if (files && files.length > 0) {
      setUploadFiles(prev => ({
        ...prev,
        [questionId]: files[0]
      }));
      
      handleAnswerChange(questionId, files[0].name);
    }
  };

  // Verileri kaydetme
  const handleSave = async () => {
    setSaving(true);
    try {
      // Formları gönder
      await axios.post(`${BACKEND_URL}/save-component`, {
        project_name: projectName,
        component_name: componentName,
        answers: answers
      });

      // Dosyaları yükle
      for (const questionId in uploadFiles) {
        const formData = new FormData();
        formData.append('file', uploadFiles[questionId]);
        formData.append('project_name', projectName);
        formData.append('component_name', componentName);
        formData.append('question_id', questionId);
        
        await axios.post(`${BACKEND_URL}/upload-file`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
      }

      setSaving(false);
      onSaveSuccess(componentName, progress);
    } catch (err) {
      setSaving(false);
      setError('Veriler kaydedilirken bir hata oluştu.');
      console.error('Kaydetme hatası:', err);
    }
  };

  // Eksik bilgileri e-posta ile talep etme
  const handleEmailRequest = () => {
    // Eksik soruları belirle
    const missingQuestions = questions
      .filter(q => q.required && (!answers[q.id] || answers[q.id].trim() === ''))
      .map(q => q.text)
      .join('\n- ');

    if (missingQuestions) {
      onEmailRequest(componentName, `- ${missingQuestions}`);
    }
  };

  // Yükleme durumu
  if (loading) {
    return (
      <Accordion.Item value={componentName} className="mb-4 overflow-hidden rounded-lg border border-gray-200 bg-white">
        <Accordion.Header>
          <Accordion.Trigger className="flex w-full items-center justify-between p-5 text-left">
            <div className="flex items-center gap-2">
              <span className="text-lg font-semibold">{componentName}</span>
              <div className="ml-4 h-6 w-6 rounded-full bg-gray-200"></div>
            </div>
            <ChevronDown className="h-5 w-5 transform transition-transform ui-state-open:rotate-180" />
          </Accordion.Trigger>
        </Accordion.Header>
        <Accordion.Content className="overflow-hidden data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down">
          <div className="p-5">Yükleniyor...</div>
        </Accordion.Content>
      </Accordion.Item>
    );
  }

  return (
    <Accordion.Item 
      value={componentName} 
      className="mb-4 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition-all"
      data-state={isOpen ? 'open' : 'closed'}
    >
      <Accordion.Header>
        <Accordion.Trigger 
          className="flex w-full items-center justify-between p-5 text-left"
          onClick={() => onOpenChange(componentName)}
        >
          <div className="flex items-center gap-2">
            <span className="text-lg font-semibold">{componentName}</span>
            {progress === 100 ? (
              <div className="ml-4 rounded-full bg-green-100 p-1">
                <Check className="h-4 w-4 text-green-600" />
              </div>
            ) : (
              <div className="ml-4 rounded-full bg-red-100 p-1">
                <X className="h-4 w-4 text-red-600" />
              </div>
            )}
          </div>
          <div className="flex items-center gap-3">
            <ProgressIndicator progress={progress} />
            <ChevronDown className="h-5 w-5 transform transition-transform ui-state-open:rotate-180" />
          </div>
        </Accordion.Trigger>
      </Accordion.Header>
      
      <Accordion.Content className="overflow-hidden data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down">
        <div className="space-y-4 p-5">
          {error && (
            <div className="mb-4 rounded-md bg-red-50 p-4 text-red-700">
              {error}
            </div>
          )}
          
          {questions.map((question) => (
            <div key={question.id} className="space-y-2">
              <label htmlFor={question.id} className="block font-medium text-gray-700">
                {question.text} {question.required && <span className="text-red-500">*</span>}
              </label>
              
              {question.type === 'text' && (
                <input
                  type="text"
                  id={question.id}
                  value={answers[question.id] || ''}
                  onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                  className="w-full rounded-md border border-gray-300 p-2"
                  required={question.required}
                />
              )}
              
              {question.type === 'textarea' && (
                <textarea
                  id={question.id}
                  value={answers[question.id] || ''}
                  onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                  className="h-24 w-full rounded-md border border-gray-300 p-2"
                  required={question.required}
                />
              )}
              
              {question.type === 'checkbox' && (
                <div className="space-y-2">
                  {question.options?.map((option) => (
                    <div key={option} className="flex items-center">
                      <input
                        type="radio"
                        id={`${question.id}-${option}`}
                        name={question.id}
                        value={option}
                        checked={answers[question.id] === option}
                        onChange={() => handleAnswerChange(question.id, option)}
                        className="mr-2 h-4 w-4"
                      />
                      <label htmlFor={`${question.id}-${option}`}>{option}</label>
                    </div>
                  ))}
                </div>
              )}
              
              {question.type === 'select' && (
                <select
                  id={question.id}
                  value={answers[question.id] || ''}
                  onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                  className="w-full rounded-md border border-gray-300 p-2"
                  required={question.required}
                >
                  <option value="">Seçiniz</option>
                  {question.options?.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              )}
              
              {question.type === 'file' && (
                <div className="mt-1 flex items-center">
                  <label 
                    htmlFor={`file-${question.id}`}
                    className="flex cursor-pointer items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
                  >
                    <Upload className="h-4 w-4" />
                    <span>Dosya Yükle</span>
                    <input
                      id={`file-${question.id}`}
                      type="file"
                      onChange={(e) => handleFileUpload(question.id, e.target.files)}
                      className="sr-only"
                    />
                  </label>
                  {answers[question.id] && (
                    <span className="ml-3 inline-flex items-center gap-1 text-sm text-gray-500">
                      <FileText className="h-4 w-4" />
                      {answers[question.id]}
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
          
          <div className="flex justify-between pt-4">
            <button
              type="button"
              onClick={handleEmailRequest}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
            >
              Eksik Bilgileri E-posta Gönder
            </button>
            
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
            >
              {isSaving ? 'Kaydediliyor...' : 'Kaydet'}
            </button>
          </div>
        </div>
      </Accordion.Content>
    </Accordion.Item>
  );
} 