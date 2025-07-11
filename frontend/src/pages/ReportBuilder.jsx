import React, { useState, useEffect, useRef, useCallback, useReducer } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectService, componentService, mailService, reportService, axiosInstance as axios } from '../services/api';
import { useToast } from '../context/ToastContext';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// PDF.js worker'ı için CDN URL'i
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

// Reducer state için başlangıç değerleri
const initialState = {
  components: [], // Mevcut useState: components
  componentData: {}, // Mevcut useState: componentData
  loading: true, // Mevcut useState: loading
  pdfLoadingStates: {}, // Mevcut useState: pdfLoading (her bileşen/soru için ayrı)
  imageLoadingStates: {}, // Görsel yüklemeleri için loading state'leri
  error: null, // Mevcut useState: error
  activeReport: null, // Mevcut useState: activeReport
};

// Reducer fonksiyonu
function reportBuilderReducer(state, action) {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_INITIAL_DATA':
      return {
        ...state,
        components: action.payload.components,
        componentData: action.payload.componentData,
        activeReport: action.payload.activeReport,
        loading: false,
        error: null,
      };
    case 'SET_ERROR':
      return { ...state, loading: false, error: action.payload };
    case 'UPDATE_ANSWER':
      return {
        ...state,
        componentData: {
          ...state.componentData,
          [action.payload.component]: {
            ...state.componentData[action.payload.component],
            answers: {
              ...state.componentData[action.payload.component].answers,
              [action.payload.questionId]: action.payload.value,
            },
          },
        },
      };
    case 'SET_PDF_LOADING':
      return {
        ...state,
        pdfLoadingStates: {
          ...state.pdfLoadingStates,
          [action.payload.key]: action.payload.isLoading,
        },
      };
    case 'SET_IMAGE_LOADING':
      return {
        ...state,
        imageLoadingStates: {
          ...state.imageLoadingStates,
          [action.payload.key]: action.payload.isLoading,
        },
      };
    case 'SET_ACTIVE_REPORT':
         return { ...state, activeReport: action.payload };
    // Diğer action type'ları buraya eklenebilir (örn: SET_COMPONENTS, ADD_PDF_CONTENT vb.)
    default:
      return state;
  }
}

// Debounce fonksiyonu
const useDebounce = (callback, delay) => {
  const timeoutRef = useRef(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return useCallback((...args) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }, [callback, delay]);
};


// helper: always return an array for rendering
const ensureArray = (val) => {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  try {
    const parsed = typeof val === 'string' ? JSON.parse(val) : val;
    return Array.isArray(parsed) ? parsed : [parsed];
  } catch {
    return [val];
  }
};

const ReportBuilder = () => {
  const { projectName } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  // useReducer kullanımı
  const [state, dispatch] = useReducer(reportBuilderReducer, initialState);
  const {
    components,
    componentData,
    loading,
    pdfLoadingStates,
    imageLoadingStates,
    error, // error state'i reducer'dan alınacak
    activeReport,
   } = state;

  // Mevcut useState hook'ları (henüz reducer'a taşınmayanlar)
  // const [components, setComponents] = useState([]); // Reducer'a taşındı
  // const [componentData, setComponentData] = useState({}); // Reducer'a taşındı
  // const [loading, setLoading] = useState(true); // Reducer'a taşındı
  const [savingReport, setSavingReport] = useState(false);
  // const [activeReport, setActiveReport] = useState(null); // Reducer'a taşındı
  const [emailSending, setEmailSending] = useState(false);

  // const [pdfLoading, setPdfLoading] = useState(false); // pdfLoadingStates ile değiştirildi

  // New states for AI prompt section
  const [aiPrompt, setAiPrompt] = useState('');
  const [showAiSection, setShowAiSection] = useState(false);
  const [isAiPromptExpanded, setIsAiPromptExpanded] = useState(false);
  const [charCount, setCharCount] = useState(0);
  const MAX_CHAR_COUNT = 2000;

  // AI prompt suggestions
  const promptSuggestions = [
    "Raporumu daha kurumsal ve profesyonel bir dilde oluştur",
    "Finansal verilere daha çok odaklan ve detaylı analiz yap",
    "Yatırımcılar için özet bilgiler ve önemli noktaları vurgula",
    "Görsellerle metinler arasında daha iyi bağlantı kur",
    "Projenin gelecek dönem beklentilerini daha detaylı açıkla"
  ];
  const componentRefs = useRef({});
  const scrollTimerRef = useRef(null);
  const hasFetchedData = useRef(false); // Fetch kontrolü için Ref
  
  // Rapor sonlandırma için onay dialog
  const [showFinalizeDialog, setShowFinalizeDialog] = useState(false);
  const [finalizing, setFinalizing] = useState(false);

  // const [error, setError] = useState(null); // Reducer'a taşındı
  const [reportData, setReportData] = useState(null); // Bu state kullanılıyor mu? Kontrol edilecek.

  // Component state tanımlamalarına eklemeler
  // const [pdfLoading, setPdfLoading] = useState(false);
  
  // Sahte dosya oluşturucu helper
  const initializeFakePdf = (content, filename, component, questionId) => {
    console.log(`initializeFakePdf çağrıldı - bileşen: ${component}, dosya: "${filename}"`);
    
    if (!content || content.trim() === '') {
      console.log(`${component} - PDF içeriği boş olduğu için initializeFakePdf işlemi atlanıyor`);
      return;
    }
    
    // Dosya adını componentData içine kaydet
    handleAnswerChange(component, questionId, filename || 'Kaydedilmiş PDF');
    
    // PDF içeriğini componentData içine kaydet
    handleAnswerChange(component, questionId + '_content', content);
    
    console.log(`${component} - PDF dosyası ve içeriği state'e kaydedildi: ${filename}`);
  };
  
  // Tarayıcıdan tamamen çıkış için uyarı gösterme (browser window/tab close)
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      // Sadece rapor oluşturulduysa ve sonlandırılmadıysa uyarı göster
      if (activeReport && activeReport.report_generated && !activeReport.is_finalized) {
        // Tarayıcı uyarısı için standart metin
        const message = 'Raporunuz sonlandırılmadı. Sayfadan ayrılırsanız, daha sonra tekrar düzenlemeye devam edebilirsiniz.';
        e.returnValue = message; // Modern tarayıcılar için
        return message; // Eski tarayıcılar için
      }
    };

    // Sadece tarayıcı kapatma event'i için listener ekle
    window.addEventListener('beforeunload', handleBeforeUnload);
    
    // Temizleme fonksiyonu
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [activeReport]);

  // fetchData useEffect'i sadece ilk mount'ta çalışacak
  useEffect(() => {
    const fetchData = async () => {
      // Eğer veri zaten çekilmişse tekrar çalıştırma
      if (hasFetchedData.current) {
        console.log('useEffect [fetchData] - Zaten çalıştırıldı, tekrar çalıştırılmıyor.');
        return;
      }
      // Bayrağı true yap ki bir daha çalışmasın
      hasFetchedData.current = true;
      console.log('useEffect [fetchData] - İlk defa çalıştırılıyor...');

      try {
        dispatch({ type: 'SET_LOADING', payload: true });

        // Aktif raporu kontrol et
        const reportDataFromApi = await projectService.getActiveReport(projectName);
        console.log('useEffect - Fetched active report data:', reportDataFromApi);
        
        if (!reportDataFromApi) {
          toast.warning('Aktif rapor bulunamadı, ana sayfaya yönlendiriliyorsunuz');
          navigate(`/project/${projectName}`);
          return;
        }
        
        // Bileşenleri getir
        const fetchedComponents = await componentService.getComponents();
        
        if (!fetchedComponents || fetchedComponents.length === 0) {
          toast.error('Bileşenler yüklenemedi, lütfen daha sonra tekrar deneyin');
          dispatch({ type: 'SET_ERROR', payload: 'Bileşenler yüklenemedi.' });
          return;
        }
        
        // Tüm bileşenlerin sorularını ve cevaplarını getir
        const fetchedComponentData = {};
        
        for (const component of fetchedComponents) {
          try {
            const questions = await componentService.getQuestions(component);
            
            if (!Array.isArray(questions) || questions.length === 0) {
              toast.warning(`${component} bileşeni için soru bulunamadı.`);
              fetchedComponentData[component] = {
                questions: [],
                answers: {}
              };
              continue;
            }
            
            // Kaydedilmiş cevapları yükle
            let savedAnswers = {};
            if (reportDataFromApi && reportDataFromApi.components && reportDataFromApi.components[component]) {
              savedAnswers = reportDataFromApi.components[component].answers || {};
            }
            
            fetchedComponentData[component] = {
              questions: questions,
              answers: savedAnswers
            };

            // Bu bileşende PDF içerikleri varsa yükle
            if (reportDataFromApi && reportDataFromApi.components && reportDataFromApi.components[component] && reportDataFromApi.components[component].pdf_contents) {
              const pdfContents = reportDataFromApi.components[component].pdf_contents;
              
              // Her PDF için
              for (const pdfInfo of pdfContents) {
                if (pdfInfo.content && pdfInfo.questionId) {
                  // PDF içeriği ve dosya adını ilgili soru ID'sine yerleştir
                  fetchedComponentData[component].answers[pdfInfo.questionId] = pdfInfo.fileName || 'Kaydedilmiş PDF';
                  fetchedComponentData[component].answers[pdfInfo.questionId + '_content'] = pdfInfo.content;
                  
                  console.log(`${component} bileşeninde PDF yüklendi: ${pdfInfo.fileName}`);
                }
              }
            }
          } catch (error) {
            console.error(`${component} bileşeni soruları yüklenirken hata:`, error);
            toast.error(`${component} bileşeni soruları yüklenirken hata oluştu: ${error.message || 'Bilinmeyen hata'}`);
            fetchedComponentData[component] = {
              questions: [],
              answers: {}
            };
          }
        }
        
        dispatch({
          type: 'SET_INITIAL_DATA',
          payload: {
            components: fetchedComponents,
            componentData: fetchedComponentData,
            activeReport: reportDataFromApi,
          },
        });
      } catch (error) {
         toast.error(error.message || 'Veri yüklenirken bir hata oluştu.');
         dispatch({ type: 'SET_ERROR', payload: error.message || 'Bilinmeyen hata' });
      }
    };

    fetchData();
  }, []);

  // Validasyon durumları için state
  const [validationStates, setValidationStates] = useState({});
  const [savingStates, setSavingStates] = useState({});

  // Input validasyon fonksiyonu
  const validateInput = (value, question = {}) => {
    // If question object is missing, treat as non-required, no length limits
    if (!question || typeof question !== 'object') {
      return { isValid: true, message: '' };
    }
    if (question.required && !value) {
      return { isValid: false, message: 'Bu alan zorunludur' };
    }
    if (question.type === 'text' && question.minLength && value.length < question.minLength) {
      return { isValid: false, message: `En az ${question.minLength} karakter girilmelidir` };
    }
    return { isValid: true, message: '' };
  };

  // Debounce'lu kaydetme fonksiyonu
  const debouncedSave = useDebounce(async (component, questionId, value) => {
    const key = `${component}-${questionId}`;
    try {
      setSavingStates(prev => ({ ...prev, [key]: true }));
      
      await componentService.saveComponentData(
        projectName,
        component,
        { [questionId]: value }
      );
      
      // Başarılı kaydetme durumunu işaretle
      setValidationStates(prev => ({
        ...prev,
        [key]: { isValid: true, message: '', saved: true }
      }));
      
      console.log(`${component} bileşeni için ${questionId} sorusunun cevabı kaydedildi.`);
    } catch (error) {
      console.error(`${component} bileşeni verisi kaydedilirken hata:`, error);
      setValidationStates(prev => ({
        ...prev,
        [key]: { isValid: false, message: 'Kaydetme hatası', saved: false }
      }));
      toast.error(`Veri kaydedilirken hata oluştu: ${error.message || 'Bilinmeyen hata'}`);
    } finally {
      setSavingStates(prev => ({ ...prev, [key]: false }));
    }
  }, 500); // 500ms debounce

  const handleAnswerChange = useCallback((component, questionId, value, question) => {
    // State'i hemen güncelle
    dispatch({ 
      type: 'UPDATE_ANSWER', 
      payload: { component, questionId, value } 
    });

    // Validasyon yap
    const validationResult = validateInput(value, question);
    const key = `${component}-${questionId}`;
    
    setValidationStates(prev => ({
      ...prev,
      [key]: { ...validationResult, saved: false }
    }));

    // Backend'e kaydetmeyi debounce ile yap
    debouncedSave(component, questionId, value);
  }, [debouncedSave]);

  // Enter tuşu ile alt input'a geçme fonksiyonu
  const handleKeyDown = useCallback((component, currentQuestionIndex, event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      
      // Mevcut bileşenin sorularını bul
      const questions = componentData[component]?.questions || [];
      
      // Bir sonraki sorunun input'unu bul
      const nextQuestion = questions[currentQuestionIndex + 1];
      if (nextQuestion) {
        // Bir sonraki input'a odaklan
        const nextInput = document.querySelector(`[data-question-id="${nextQuestion.id}"]`);
        if (nextInput) {
          nextInput.focus();
        }
      }
    }
  }, [componentData]);

  // Bileşen için PDF dosyası yükleme
  const handleComponentPdfUpload = async (component, questionId, event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  // Validation
  if (file.type !== 'application/pdf') {
    toast.error('Lütfen sadece PDF dosyası yükleyin.');
    return;
  }
  
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
  if (file.size > MAX_FILE_SIZE) {
    toast.error('Dosya boyutu 10MB\'dan küçük olmalıdır.');
    return;
  }
  
  const loadingKey = `${component}-${questionId}`;
  dispatch({ type: 'SET_PDF_LOADING', payload: { key: loadingKey, isLoading: true } });
  
  try {
    // Upload PDF
    const uploadResult = await componentService.uploadPDF(projectName, component, file, questionId);
    
    if (!uploadResult.success) {
      throw new Error('PDF yükleme başarısız: ' + (uploadResult.message || 'Bilinmeyen hata'));
    }
    
    // Update state with the complete file array from backend
    if (uploadResult.files && Array.isArray(uploadResult.files)) {
      dispatch({
        type: 'UPDATE_ANSWER',
        payload: { component, questionId, value: uploadResult.files }
      });
    }
    
    toast.success(`${file.name} başarıyla yüklendi`);
    
  } catch (error) {
    console.error(`${component} - PDF işleme hatası:`, error);
    toast.error(`PDF yüklenirken hata oluştu: ${error.message || 'Bilinmeyen hata'}`);
  } finally {
    dispatch({ type: 'SET_PDF_LOADING', payload: { key: loadingKey, isLoading: false } });
  }
};

  
  // Bileşen görseli yükleme
  const handleComponentImageUpload = async (component, questionId, event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  // Validation
  if (!file.type.match('image.*')) {
    toast.error('Lütfen sadece resim dosyaları yükleyin.');
    return;
  }
  
  const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
  if (file.size > MAX_FILE_SIZE) {
    toast.error('Görsel boyutu 5MB\'dan küçük olmalıdır.');
    return;
  }
  
  const loadingKey = `${component}-${questionId}-image`;
  dispatch({ type: 'SET_IMAGE_LOADING', payload: { key: loadingKey, isLoading: true } });
  
  try {
    const imageIndex = 0; // For now, we're not using index
    
    const result = await componentService.uploadComponentImage(
      projectName,
      component,
      file,
      imageIndex,
      questionId
    );
    
    if (!result || !result.success) {
      throw new Error('Görsel yükleme başarısız oldu');
    }
    
    // Update state with the complete file array from backend
    if (result.files && Array.isArray(result.files)) {
      dispatch({
        type: 'UPDATE_ANSWER',
        payload: { component, questionId, value: result.files }
      });
    }
    
    toast.success(`${file.name} başarıyla yüklendi`);
    
  } catch (error) {
    console.error(`${component} - Görsel yükleme hatası:`, error);
    toast.error(`Görsel yüklenirken hata oluştu: ${error.message || 'Bilinmeyen hata'}`);
  } finally {
    dispatch({ type: 'SET_IMAGE_LOADING', payload: { key: loadingKey, isLoading: false } });
  }
};
  

const handleRemoveComponentImage = async (component, questionId, fileToRemove) => {
  try {
    // Debug log to see what we're trying to remove
    console.log('Removing file:', fileToRemove);
    
    // Validate fileToRemove
    if (!fileToRemove || typeof fileToRemove !== 'object') {
      toast.error('Geçersiz dosya bilgisi');
      return;
    }
    
    // Ensure we have required fields
    const filename = fileToRemove.filename || '';
    const filepath = fileToRemove.path || '';
    
    if (!filename || !filepath) {
      toast.error('Dosya bilgileri eksik');
      console.error('Missing file info:', { filename, filepath, fileToRemove });
      return;
    }

    // Remove the file from backend
    const formData = new FormData();
    formData.append('component', component);
    formData.append('question_id', questionId);
    formData.append('filename', filename);
    formData.append('file_path', filepath);
    
    // Log what we're sending
    console.log('Sending removal request:', {
      component,
      question_id: questionId,
      filename,
      file_path: filepath
    });
    
    const response = await axios.post(
      `/project/${encodeURIComponent(projectName)}/remove-file`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      }
    );
    
    if (response.data.success) {
      // Update local state with the updated file list from backend
      dispatch({
        type: 'UPDATE_ANSWER',
        payload: { 
          component, 
          questionId, 
          value: response.data.files || []
        }
      });
      
      toast.info('Görsel kaldırıldı');
    } else {
      throw new Error(response.data.message || 'Dosya kaldırılamadı');
    }
  } catch (error) {
    console.error(`${component} - Görsel kaldırma hatası:`, error);
    toast.error(`Görsel kaldırılırken hata oluştu: ${error.message || 'Bilinmeyen hata'}`);
  }
};
  const handleRemoveComponentPdf = async (component, questionId, fileToRemove) => {
  try {
    // Debug log to see what we're trying to remove
    console.log('Removing PDF:', fileToRemove);
    
    // Validate fileToRemove
    if (!fileToRemove || typeof fileToRemove !== 'object') {
      toast.error('Geçersiz PDF dosya bilgisi');
      return;
    }
    
    // Ensure we have required fields
    const filename = fileToRemove.filename || '';
    const filepath = fileToRemove.path || '';
    
    if (!filename || !filepath) {
      toast.error('PDF dosya bilgileri eksik');
      console.error('Missing PDF info:', { filename, filepath, fileToRemove });
      return;
    }

    // Remove the file from backend
    const formData = new FormData();
    formData.append('component', component);
    formData.append('question_id', questionId);
    formData.append('filename', filename);
    formData.append('file_path', filepath);
    
    // Log what we're sending
    console.log('Sending PDF removal request:', {
      component,
      question_id: questionId,
      filename,
      file_path: filepath
    });
    
    const response = await axios.post(
      `/project/${encodeURIComponent(projectName)}/remove-file`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      }
    );
    
    if (response.data.success) {
      // Update local state with the updated file list from backend
      dispatch({
        type: 'UPDATE_ANSWER',
        payload: { 
          component, 
          questionId, 
          value: response.data.files || []
        }
      });
      
      toast.info('PDF kaldırıldı');
    } else {
      throw new Error(response.data.message || 'PDF dosyası kaldırılamadı');
    }
  } catch (error) {
    console.error(`${component} - PDF kaldırma hatası:`, error);
    toast.error(`PDF kaldırılırken hata oluştu: ${error.message || 'Bilinmeyen hata'}`);
  }
};
  
  const validateRequiredFields = () => {
    let isValid = true;
    let missingComponents = [];

    Object.keys(componentData).forEach(component => {
      const { answers } = componentData[component];
      
      // PDF alanı zorunlu, görsel opsiyonel
      if (!answers['pdf_upload'] || answers['pdf_upload'] === '') {
        isValid = false;
        missingComponents.push(component);
      }
    });

    if (!isValid) {
      toast.error(`Lütfen ${missingComponents.join(', ')} bileşenlerine ait zorunlu PDF alanlarını doldurun.`);
    }

    return isValid;
  };

  // Rapor oluşturma fonksiyonunu


const handleGenerateReport = async () => {
  // Simple validation - just check if PDFs and images are uploaded
  let hasRequiredFiles = true;
  let missingComponents = [];

  Object.keys(componentData).forEach(component => {
    const { answers } = componentData[component];
    
    // Check if PDF is uploaded (required)
    const pdfData = ensureArray(answers['pdf_upload']);
    if (!pdfData || pdfData.length === 0) {
      hasRequiredFiles = false;
      missingComponents.push(component);
    }
  });

  if (!hasRequiredFiles) {
    toast.error(`Please upload PDF files for: ${missingComponents.join(', ')}`);
    return;
  }

  setSavingReport(true);
  
  try {
    // Show info message
    toast.info('Report generation started. This process runs in the background.');
    
    // First, save all component data to ensure files are properly recorded
    const savedComponents = [];
    for (const component of components) {
      try {
        console.log(`Saving ${component} component data...`);
        await componentService.saveComponentData(
          projectName,
          component,
          componentData[component].answers
        );
        console.log(`${component} component saved successfully.`);
        savedComponents.push(component);
      } catch (error) {
        console.error(`Error saving ${component} component:`, error);
        toast.error(`Failed to save ${component} data: ${error.message}`);
      }
    }
    
    if (savedComponents.length === 0) {
      throw new Error("No component data could be saved. Please try again.");
    }
    
    // Now call the simplified report generation
    console.log('Calling simplified report generation...');
    
    try {
      console.log('AI Prompt:', aiPrompt);
      const result = await reportService.generateReportSimplified(projectName,aiPrompt || null);
      
      // Update the active report state
      const updatedReport = await projectService.getActiveReport(projectName);
      dispatch({ type: 'SET_ACTIVE_REPORT', payload: updatedReport });
      
      console.log('Report generated successfully:', result);
      toast.success('Report generated successfully and added to showcase.');
      
    } catch (error) {
      console.error('Report generation error:', error);
      toast.error(`Failed to generate report: ${error.message}`);
      throw error;
    }
    
  } catch (error) {
    console.error('Report generation process failed:', error);
    toast.error(`Report could not be generated: ${error.message}`);
  } finally {
    setSavingReport(false);
  }
};

  // E-posta gönderme işlemi
  const handleSendEmail = async (componentName) => {
    // Hangi bileşen için e-posta gönderiliyor
    const componentSpecificEmail = {
      'İşletme': 'İşletme departmanına',
      'Finans': 'Finans departmanına',
      'İnşaat': 'İnşaat departmanına', 
      'Kurumsal İletişim': 'Kurumsal İletişim departmanına'
    };
    
    setEmailSending(true);
    
    try {
      await mailService.sendEmailRequest(componentName, projectName);
      toast.success(`${componentSpecificEmail[componentName] || componentName + ' bileşeni için'} bilgi talebi e-postası başarıyla gönderildi`);
    } catch (error) {
      toast.error(`E-posta gönderilirken hata oluştu: ${error.message}`);
    } finally {
      setEmailSending(false);
    }
  };

  // Bilgi İste butonuna tıklandığında
  const sendEmailRequest = (componentName) => {
    handleSendEmail(componentName);
  };
  
  // Raporu sonlandır
  const handleFinalizeReport = async () => {
    setFinalizing(true);
    
    try {
      await reportService.finalizeReport(projectName);
      toast.success("Rapor başarıyla sonlandırıldı");
      navigate(`/project/${projectName}`);
    } catch (error) {
      toast.error(`Rapor sonlandırılırken hata: ${error.message}`);
    } finally {
      setFinalizing(false);
      setShowFinalizeDialog(false);
    }
  };

  // Raporu indirme işlemi
  const handleDownloadReport = async () => {
    try {
      toast.info('Rapor indiriliyor...');
      
      // DÜZELTME: reportId'yi kontrol et ve reportService.downloadReport çağrısına ekle
      const reportId = activeReport?.report_id || activeReport?.id;
      console.log("[Download Report] ActiveReport:", activeReport);
      console.log("[Download Report] Report ID:", reportId);
      
      if (!reportId) {
        console.error("[Download Report] Error: Report ID not found in activeReport:", activeReport);
        toast.error("Rapor ID bulunamadı. Lütfen raporu yeniden oluşturun veya sayfayı yenileyin.");
        return;
      }
      
      // Blob olarak PDF'i al - reportId parametresini ekliyoruz
      console.log(`[Download Report] Calling reportService.downloadReport(${projectName}, ${reportId})`);
      const blob = await reportService.downloadReport(projectName, reportId);
      
      // Blob tipini kontrol et - hata durumunu yakala
      if (!(blob instanceof Blob)) {
        console.error('[Download Report] Return data is not a Blob:', blob);
        if (typeof blob === 'object') {
          console.error('[Download Report] Returned content:', JSON.stringify(blob));
        }
        throw new Error('PDF doğru formatta alınamadı');
      }
      
      // Blob'dan URL oluştur
      const url = URL.createObjectURL(blob);
      
      // URL'yi kullanarak indirme işlemini başlat
      const link = document.createElement('a');
      link.href = url;
      
      // Mevcut PDF dosya adını kullan veya varsayılan ad oluştur
      const fileName = activeReport?.pdfFileName || `${projectName}_report.pdf`;
      link.download = fileName;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // URL'yi temizle
      URL.revokeObjectURL(url);
      
      toast.success(`Rapor indirme işlemi başlatıldı: ${fileName}`);
    } catch (error) {
      console.error('[Download Report] Error:', error);
      toast.error(`Rapor indirilirken hata: ${error.message}`);
    }
  };

  // PDF önizleme için state'ler
  const [pdfUrl, setPdfUrl] = useState(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  // PDF URL'ini güncelle
  useEffect(() => {
    if (activeReport?.report_generated) {
      const getPdfUrl = async () => {
        try {
          // activeReport'tan reportId'yi al
          const reportId = activeReport.id || activeReport.report_id;
          if (!reportId) {
            throw new Error('Rapor ID bulunamadı');
          }

          const blob = await reportService.downloadReport(projectName, reportId);
          if (!(blob instanceof Blob)) {
            throw new Error('PDF doğru formatta alınamadı');
          }
          
          const url = URL.createObjectURL(blob);
          setPdfUrl(url);
          
          // Yeni pencerede aç
          if (isPreviewOpen) {
            window.open(url, '_blank');
            setIsPreviewOpen(false);
          }
          
          // Cleanup function
          return () => URL.revokeObjectURL(url);
        } catch (error) {
          console.error('PDF yüklenirken hata:', error);
          toast.error(error.message || 'PDF önizleme yüklenemedi');
        }
      };
      
      getPdfUrl();
    }
  }, [activeReport?.report_generated, projectName, activeReport, isPreviewOpen]);

  // Rename handleDeleteReport to handleResetReportGeneration
  const handleResetReportGeneration = async () => {
    console.log("[Reset Report] Button clicked. Current activeReport state:", activeReport);

    // Ensure projectName is available (should be from useParams)
    if (!projectName) {
      console.error("[Reset Report] Error: Project name is missing.");
      toast.error("Proje adı bulunamadı, işlem yapılamıyor.");
      return;
    }
    console.log(`[Reset Report] Proceeding with Project Name: ${projectName}`);

    if (window.confirm('Oluşturulan PDF raporunu silip yeniden oluşturmaya hazır hale getirmek istediğinizden emin misiniz?')) {
      console.log("[Reset Report] User confirmed.");
      setSavingReport(true); // Indicate loading/processing state
      console.log("[Reset Report] Setting savingReport to true.");
      try {
        // DÜZELTME: Daha detaylı loglama ekle
        console.log("[Reset Report] Encoded project name for API call:", encodeURIComponent(projectName));
        console.log(`[Reset Report] API endpoint: /project/${encodeURIComponent(projectName)}/reset-active-report`);
        console.log("[Reset Report] Calling reportService.resetActiveReport()...");
        
        // Call the service function, relying only on projectName
        const result = await reportService.resetActiveReport(projectName);
        
        // DÜZELTME: Yanıtı daha detaylı kontrol et
        console.log("[Reset Report] API call result:", result);
        
        if (!result) {
          console.error("[Reset Report] API returned empty or undefined result");
          throw new Error("Sunucu yanıtı boş veya tanımsız");
        }

        // Update local state with the reset report data from backend
        if (result && result.active_report) {
           console.log("[Reset Report] Dispatching SET_ACTIVE_REPORT with payload:", result.active_report);
           dispatch({ type: 'SET_ACTIVE_REPORT', payload: result.active_report });
        } else {
            console.warn("[Reset Report] API result did not contain expected active_report data. Resetting state locally.");
            // Fallback: If backend doesn't return the updated report, try setting a basic reset state
            // This assumes the backend *did* reset but didn't return the object properly.
            // A better fallback might be refetching, but let's try a simple local reset first.
             dispatch({ 
                type: 'SET_ACTIVE_REPORT', 
                // Create a minimal representation of a reset active report
                payload: activeReport ? { ...activeReport, report_generated: false, pdfFileName: null, pdf_path: null } : null 
            });
             console.log("[Reset Report] Dispatched SET_ACTIVE_REPORT with locally constructed reset state.");
             // Consider adding a refetch here if this minimal approach is insufficient
             toast.warning("Rapor sıfırlandı ancak güncel durum sunucudan alınamadı.");
        }
        
        toast.success('Rapor PDF\\\'i silindi (veya zaten yoktu). Raporu yeniden oluşturabilirsiniz.');
        // No navigation needed, stay on the page
      } catch (error) {
        // DÜZELTME: Daha detaylı hata bilgisi
        console.error('[Reset Report] Error during API call or state update:', error);
        
        // Axios hatalarını daha detaylı logla
        if (error.response) {
          console.error('[Reset Report] Error response status:', error.response.status);
          console.error('[Reset Report] Error response data:', error.response.data);
        } else if (error.request) {
          console.error('[Reset Report] Error request (no response):', error.request);
        }
        
        toast.error(`Rapor sıfırlanırken bir hata oluştu: ${error.message || 'Bilinmeyen Hata'}`);
      } finally {
        console.log("[Reset Report] Setting savingReport back to false.");
        setSavingReport(false); // Reset loading state
      }
    } else {
      console.log("[Reset Report] User cancelled.");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <p className="ml-3 text-blue-600">Rapor verileri yükleniyor...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 max-w-2xl mx-auto">
        <h2 className="text-xl font-bold mb-4 text-red-600">Hata</h2>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={() => navigate(`/project/${projectName}`)}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Proje Sayfasına Dön
        </button>
      </div>
    );
  }

  if (components.length === 0) {
    return (
      <div className="text-center py-8 max-w-2xl mx-auto">
        <h2 className="text-xl font-bold mb-4 text-red-600">Bileşen Yüklenemedi</h2>
        <p className="text-gray-600 mb-4">Rapor bileşenleri yüklenirken bir sorun oluştu. Lütfen daha sonra tekrar deneyin.</p>
        <button 
          onClick={() => navigate(`/project/${projectName}`)} 
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Proje Sayfasına Dön
        </button>
      </div>
    );
  }

  // Rapor sonlandırma için onay dialog
  const FinalizeDialog = () => (
    <div className="fixed inset-0 flex items-center justify-center z-50 bg-black bg-opacity-50">
      <div className="bg-white p-6 rounded-lg shadow-xl max-w-md">
        <h3 className="text-xl font-bold mb-4">Raporu Sonlandır</h3>
        <p className="mb-6 text-gray-600">
          Raporu sonlandırmak üzeresiniz. Bu işlem geri alınamaz ve rapor üzerinde daha fazla değişiklik yapılamaz.
          Devam etmek istediğinize emin misiniz?
        </p>
        <div className="flex justify-end space-x-4">
          <button 
            onClick={() => setShowFinalizeDialog(false)} 
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-100"
            disabled={finalizing}
          >
            İptal
          </button>
          <button 
            onClick={handleFinalizeReport} 
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 flex items-center"
            disabled={finalizing}
          >
            {finalizing && (
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            )}
            {finalizing ? 'Sonlandırılıyor...' : 'Raporu Sonlandır'}
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Başlık Bilgisi */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 text-center">Rapor Oluşturma</h1>
        <p className="text-gray-600 text-center mb-2">Proje: {projectName}</p>
        <p className="text-center text-sm text-red-500 mb-4">PDF alanları doldurulması zorunludur.</p>
        
        {/* Üst bar navigasyon butonları */}
        <div className="flex justify-center space-x-4 mt-6">
          <button
            onClick={() => navigate(`/project/${projectName}`)}
            className="px-4 py-2 text-sm border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            Proje Sayfasına Dön
          </button>
        </div>
      </div>

      <div>
        {/* Ana İçerik - Bileşenler */}
        <div className="max-w-4xl mx-auto"> {/* Increased max-width since we have more space now */}
          <div className="space-y-8 mb-8">
            {components.map((component, index) => (
              <div
                key={component}
                className="bg-white rounded-lg shadow-lg p-6"
                ref={el => componentRefs.current[component] = el}
                id={`component-${component}`}
              >
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-2xl font-bold text-gray-800">{component}</h2>
                  <button
                    onClick={() => sendEmailRequest(component)}
                    className="inline-flex items-center px-3 py-1 border border-blue-300 text-sm font-medium rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100"
                    disabled={emailSending}
                  >
                    {emailSending ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Gönderiliyor...
                      </>
                    ) : (
                      <>
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        Bilgi İste
                      </>
                    )}
                  </button>
                </div>
                
                {/* Simplified component rendering with just PDF and image upload fields */}
                <div className="space-y-6">
                  {/* PDF Upload Section */}
                  <div className="space-y-2 border-b pb-6">
                    <label className="block text-sm font-medium text-gray-700">
                      PDF Rapor
                      <span className="text-red-500 ml-1">*</span>
                    </label>
                    <div className="mt-1">
                      <div className="flex flex-col space-y-3">
                        <div className="space-y-2">
                          {(() => {
                            const pdfQuestionId = "pdf_upload";
                            const isLoadingPdf = pdfLoadingStates[`${component}-${pdfQuestionId}`] || false;
                            const pdfData = ensureArray(componentData[component]?.answers[pdfQuestionId]);

                            // Yükleme durumunda loading spinner göster
                            if (isLoadingPdf) {
                              return (
                                <div className="flex items-center text-sm text-blue-600">
                                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                  </svg>
                                  PDF işleniyor...
                                </div>
                              );
                            }

                            // PDF yüklenmişse dosya bilgilerini göster
                            if (pdfData && Array.isArray(pdfData)) {
                              return (
                                <div className="space-y-2">
                                  {pdfData.map((file, index) => (
                                    <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-md border border-gray-200">
                                      <div className="flex items-center">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                        </svg>
                                        <span className="text-sm font-medium text-gray-700">
                                          {file.filename}
                                        </span>
                                      </div>
                                      <button
                                        type="button"
                                        onClick={() => handleRemoveComponentPdf(component, pdfQuestionId, file)}
                                        className="ml-2 flex-shrink-0 text-red-500 hover:text-red-700"
                                        title="Dosyayı kaldır"
                                      >
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                        </svg>
                                      </button>
                                    </div>
                                  ))}
                                  
                                  {/* Always show upload button even when files exist to allow multiple uploads */}
                                  <input
                                    type="file"
                                    accept="application/pdf"
                                    onChange={(e) => handleComponentPdfUpload(component, pdfQuestionId, e)}
                                    className="block w-full text-sm text-gray-500
                                      file:mr-4 file:py-2 file:px-4
                                      file:rounded-md file:border-0
                                      file:text-sm file:font-semibold
                                      file:bg-blue-50 file:text-blue-700
                                      hover:file:bg-blue-100"
                                    required={true}
                                    disabled={isLoadingPdf}
                                  />
                                </div>
                              );
                            }

                            // Hiçbir dosya yoksa sadece yükleme alanını göster
                            return (
                              <input
                                type="file"
                                accept="application/pdf"
                                onChange={(e) => handleComponentPdfUpload(component, pdfQuestionId, e)}
                                className="block w-full text-sm text-gray-500
                                  file:mr-4 file:py-2 file:px-4
                                  file:rounded-md file:border-0
                                  file:text-sm file:font-semibold
                                  file:bg-blue-50 file:text-blue-700
                                  hover:file:bg-blue-100"
                                required={true}
                                disabled={isLoadingPdf}
                              />
                            );
                          })()}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Image Upload Section */}
                  <div className="space-y-2 border-b pb-6">
                    <label className="block text-sm font-medium text-gray-700">
                      Görseller
                    </label>
                    <div className="mt-1">
                      <div className="flex flex-col space-y-3">
                        <div className="space-y-2">
                          {(() => {
                            const imageQuestionId = "image_upload";
                            const isLoadingImage = imageLoadingStates[`${component}-${imageQuestionId}-image`] || false;
                            const imageData = ensureArray(componentData[component]?.answers[imageQuestionId]);

                            // Yükleme durumunda loading spinner göster
                            if (isLoadingImage) {
                              return (
                                <div className="flex items-center text-sm text-blue-600">
                                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                  </svg>
                                  Görsel yükleniyor...
                                </div>
                              );
                            }

                            // Görsel yüklenmişse dosya bilgilerini göster
                            if (imageData && Array.isArray(imageData)) {
                              return (
                                <div className="space-y-2">
                                  {imageData.map((file, index) => (
                                    <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-md border border-gray-200">
                                      <div className="flex items-center">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                        </svg>
                                        <span className="text-sm font-medium text-gray-700">
                                          {file.filename.length > 20 ? file.filename.substring(0, 17) + '...' : file.filename}
                                        </span>
                                      </div>
                                      <button
                                        type="button"
                                        onClick={() => handleRemoveComponentImage(component, imageQuestionId, file)}
                                        className="ml-2 flex-shrink-0 text-red-500 hover:text-red-700"
                                        title="Görseli kaldır"
                                      >
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                      </svg>
                                      </button>
                                    </div>
                                  ))}
                                  
                                  {/* Always show upload button to allow multiple uploads */}
                                  <div>
                                    <input
                                      type="file"
                                      accept="image/*"
                                      onChange={(e) => handleComponentImageUpload(component, imageQuestionId, e)}
                                      id={`image-upload-${component}-${imageQuestionId}`}
                                      className="hidden"
                                      disabled={isLoadingImage}
                                    />
                                    <label
                                      htmlFor={`image-upload-${component}-${imageQuestionId}`}
                                      className="inline-flex items-center px-3 py-2 border border-green-300 text-sm font-medium rounded-md text-green-700 bg-green-50 hover:bg-green-100 cursor-pointer"
                                    >
                                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                      </svg>
                                      Görsel Yükle
                                    </label>
                                  </div>
                                </div>
                              );
                            }

                            // Hiçbir görsel yoksa sadece yükleme alanını göster
                            return (
                              <div>
                                <input
                                  type="file"
                                  accept="image/*"
                                  onChange={(e) => handleComponentImageUpload(component, imageQuestionId, e)}
                                  id={`image-upload-${component}-${imageQuestionId}`}
                                  className="hidden"
                                  disabled={isLoadingImage}
                                />
                                <label
                                  htmlFor={`image-upload-${component}-${imageQuestionId}`}
                                  className="inline-flex items-center px-3 py-2 border border-green-300 text-sm font-medium rounded-md text-green-700 bg-green-50 hover:bg-green-100 cursor-pointer"
                                >
                                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                  </svg>
                                  Görsel Yükle
                                </label>
                              </div>
                            );
                          })()}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            <div className="mt-8 mb-8">
            <div className="max-w-4xl mx-auto">
              <button
                onClick={() => setShowAiSection(!showAiSection)}
                className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200 hover:border-purple-300 transition-all duration-300"
              >
                <div className="flex items-center">
                  <svg className="w-6 h-6 text-purple-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <span className="text-lg font-semibold text-purple-700">AI İle Raporu Özelleştir</span>
                </div>
                <svg 
                  className={`w-5 h-5 text-purple-600 transform transition-transform duration-300 ${showAiSection ? 'rotate-180' : ''}`} 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {showAiSection && (
                <div className="mt-4 p-6 bg-white rounded-lg shadow-lg border border-gray-200 animate-fade-in">
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Raporunuz için özel talimatlar
                    </label>
                    <div className="relative">
                      <textarea
                        value={aiPrompt}
                        onChange={(e) => {
                          setAiPrompt(e.target.value);
                          setCharCount(e.target.value.length);
                        }}
                        placeholder="Raporunuzun nasıl oluşturulmasını istediğinizi detaylı bir şekilde açıklayın..."
                        className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-300 ${
                          isAiPromptExpanded ? 'h-48' : 'h-32'
                        }`}
                        maxLength={MAX_CHAR_COUNT}
                        onFocus={() => setIsAiPromptExpanded(true)}
                        onBlur={() => setIsAiPromptExpanded(false)}
                      />
                      <div className="absolute bottom-2 right-2 text-xs text-gray-500">
                        {charCount}/{MAX_CHAR_COUNT}
                      </div>
                    </div>
                  </div>

                  <div className="mb-4">
                    <p className="text-sm text-gray-600 mb-2">Örnek talimatlar:</p>
                    <div className="flex flex-wrap gap-2">
                      {promptSuggestions.map((suggestion, index) => (
                        <button
                          key={index}
                          onClick={() => {
                            setAiPrompt(suggestion);
                            setCharCount(suggestion.length);
                          }}
                          className="px-3 py-1 text-xs bg-purple-100 text-purple-700 rounded-full hover:bg-purple-200 transition-colors duration-200"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  </div>

                  {aiPrompt && (
                    <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                      <p className="text-sm text-purple-700">
                        <span className="font-semibold">Seçilen talimat:</span> {aiPrompt}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
          </div>
            </div>
        
          </div>

          {/* Rapor İşlemleri ve Sonuç Bölümü */}
          <div className="mt-8">
            {/* Oluşturulan Rapor Görüntüleme Bölümü */}
            {activeReport && activeReport.report_generated && (
              <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
                <h2 className="text-lg font-bold text-gray-800 mb-4">Oluşturulan Rapor</h2>
                <p className="text-gray-600 mb-4">
                  Raporunuz başarıyla oluşturuldu. Aşağıdaki butonlarla raporu görüntüleyebilir, indirebilir veya sonlandırabilirsiniz.
                </p>
                
                {/* PDF Dosya adı gösterimi */}
                {activeReport.pdfFileName && (
                  <div className="bg-gray-50 rounded-md p-3 mb-4">
                    <p className="text-sm text-gray-600">PDF Dosya Adı:</p>
                    <p className="text-md font-medium text-gray-800">{activeReport.pdfFileName}</p>
                    <p className="text-xs text-gray-500 mt-1">Dosya adı otomatik olarak [proje adı]__[rapor tarihi].pdf formatında oluşturulmuştur.</p>
                  </div>
                )}
                
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={handleDownloadReport}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Raporu İndir
                  </button>

              <button
                onClick={handleResetReportGeneration}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700"
                disabled={savingReport || !activeReport?.report_generated}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Oluşturulan Raporu Sil
              </button>

              <button
                onClick={() => setIsPreviewOpen(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                Önizleme
                  </button>
                  
                  {!activeReport.is_finalized && (
                    <button
                      onClick={() => setShowFinalizeDialog(true)}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Raporu Sonlandır
                    </button>
                  )}
                </div>
                
                {activeReport.is_finalized ? (
                  <p className="mt-4 text-sm font-medium text-green-600">
                    Bu rapor sonlandırılmış ve düzenlenemez durumda.
                  </p>
                ) : (
                  <p className="mt-4 text-sm text-amber-600">
                    Rapor düzenlenebilir durumda. Düzenlemeyi tamamladıktan sonra sonlandırabilirsiniz.
                  </p>
                )}
              </div>
            )}

            {/* Ana Butonlar */}
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => navigate(`/project/${projectName}`)}
                className="px-6 py-3 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
            Geri
              </button>
              
              <button
                onClick={handleGenerateReport}
                disabled={savingReport || (activeReport && activeReport.is_finalized)}
                className="px-6 py-3 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 flex items-center"
              >
                {savingReport && (
                  <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
                {savingReport ? 'Rapor Oluşturuluyor...' : (activeReport && activeReport.report_generated) ? 'Raporu Yeniden Oluştur' : 'Raporu Oluştur'}
              </button>
        </div>
      </div>

      {/* Sonlandırma onay dialog'u */}
      {showFinalizeDialog && <FinalizeDialog />}
    </div>
  );
};

export default ReportBuilder;
