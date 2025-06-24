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
  activeSection: '', // Mevcut useState: activeSection
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
        activeSection: action.payload.components.length > 0 ? action.payload.components[0] : '',
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
    case 'SET_ACTIVE_SECTION':
         return { ...state, activeSection: action.payload };
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
    activeSection,
   } = state;

  // Mevcut useState hook'ları (henüz reducer'a taşınmayanlar)
  // const [components, setComponents] = useState([]); // Reducer'a taşındı
  // const [componentData, setComponentData] = useState({}); // Reducer'a taşındı
  // const [loading, setLoading] = useState(true); // Reducer'a taşındı
  const [savingReport, setSavingReport] = useState(false);
  // const [activeReport, setActiveReport] = useState(null); // Reducer'a taşındı
  const [emailSending, setEmailSending] = useState(false);
  // const [activeSection, setActiveSection] = useState(''); // Reducer'a taşındı

  // const [pdfLoading, setPdfLoading] = useState(false); // pdfLoadingStates ile değiştirildi


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

  // Scroll takibini basitleştir ve daha güvenilir hale getir
  const determineActiveSection = useCallback(() => {
    if (loading || components.length === 0) return;
    
    // Ekranın orta noktasını bul
    const viewportHeight = window.innerHeight;
    const viewportMiddle = viewportHeight / 2;
    
    // En yakın bileşeni bul (ekranın ortasına göre)
    let closestComponent = null;
    let closestDistance = Infinity;
    
    for (const component of components) {
      const element = componentRefs.current[component];
      if (!element) continue;
      
      const rect = element.getBoundingClientRect();
      
      // Bileşenin ortasının ekranın ortasına olan uzaklığı
      const componentMiddle = (rect.top + rect.bottom) / 2;
      const distance = Math.abs(componentMiddle - viewportMiddle);
      
      // Daha yakınsa, bu bileşeni seç
      if (distance < closestDistance) {
        closestDistance = distance;
        closestComponent = component;
      }
    }
    
    // En yakın bileşen varsa ve aktif bileşenden farklıysa güncelle
    if (closestComponent && closestComponent !== activeSection) {
      dispatch({ type: 'SET_ACTIVE_SECTION', payload: closestComponent });
    }
  }, [loading, components, activeSection]);
  
  // Throttled scroll handler - performans için
  const handleScroll = useCallback(() => {
    // Mevcut zamanlayıcıyı temizle
    if (scrollTimerRef.current) {
      clearTimeout(scrollTimerRef.current);
    }
    
    // 50ms gecikmeyle aktif bölümü belirle (throttling)
    scrollTimerRef.current = setTimeout(() => {
      determineActiveSection();
    }, 50);
  }, [determineActiveSection]);
  
  // Scroll olayını dinle
  useEffect(() => {
    if (loading) return;
    
    // Her scroll olayında throttled handler'ı çağır
    window.addEventListener('scroll', handleScroll);
    
    // İlk yüklemede aktif bölümü belirle
    determineActiveSection();
    
    // Temizlik
    return () => {
      window.removeEventListener('scroll', handleScroll);
      if (scrollTimerRef.current) {
        clearTimeout(scrollTimerRef.current);
      }
    };
  }, [loading, handleScroll, determineActiveSection]);

  // Bileşene scroll işlemi
  const scrollToComponent = (component) => {
    dispatch({ type: 'SET_ACTIVE_SECTION', payload: component });
    if (componentRefs.current[component]) {
      componentRefs.current[component].scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
      });
    }
  };
  
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
    // Tarayıcı konsoluna test mesajı
    console.log(`%c ${component} - PDF YÜKLEME BAŞLATILDI! (${questionId})`, 'background: red; color: white; font-size: 16px;');
    
    const file = event.target.files[0];
    if (!file) {
      console.log(`${component} - Dosya seçilmedi`);
      return;
    }
    
    console.log(`${component} - Seçilen dosya: ${file.name}, ${file.type}, ${file.size} bytes`);
    
    // PDF dosya türünü kontrol et
    if (file.type !== 'application/pdf') {
      console.error(`${component} - Geçersiz dosya türü: ${file.type}`);
      toast.error('Lütfen sadece PDF dosyası yükleyin.');
      return;
    }
    
    // Dosya boyutunu kontrol et (10MB limit)
    const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
    if (file.size > MAX_FILE_SIZE) {
      console.error(`${component} - Dosya boyutu çok büyük: ${file.size} bytes`);
      toast.error('Dosya boyutu 10MB\'dan küçük olmalıdır.');
      return;
    }
    
    const loadingKey = `${component}-${questionId}`;
    dispatch({ type: 'SET_PDF_LOADING', payload: { key: loadingKey, isLoading: true } });
    
    try {
      console.log(`${component} - PDF içeriği çıkarma işlemi başlatılıyor...`);
      
      // FormData oluştur
      const formData = new FormData();
      formData.append('file', file); // Backend expects the field name to be 'file'
      formData.append('project_name', projectName);
      formData.append('component_name', component);

      // PDF dosyasını yükle
      console.log(`${component} - PDF yüklemek için componentService.uploadPDF kullanılıyor`);
      const uploadResult = await componentService.uploadPDF(projectName, component, file, questionId);
      
      if (!uploadResult.success) {
        throw new Error('PDF yükleme başarısız: ' + (uploadResult.message || 'Bilinmeyen hata'));
      }
      
      console.log(`${component} - PDF yükleme başarılı:`, uploadResult);
      
      // PDF içeriğini çıkarmak için API'ya istek gönder
      const response = await reportService.extractPdf(formData, {
        timeout: 60000 // 60 saniye timeout
      });
      
      console.log(`${component} - API yanıtı alındı:`, response.data);
      
      if (!response.data || !response.data.content) {
        throw new Error('PDF içeriği boş döndü veya hatalı format');
      }
      
      // PDF içeriğini component answers içine kaydet (özel bir alan olarak)
      const extractedContent = response.data.content;
      console.log(`${component} - PDF içeriği çıkarıldı (${extractedContent.length} karakter)`);
      
      // İçeriği kontrol et
      if (extractedContent.trim() === '') {
        throw new Error('PDF içeriği boş olarak çıkarıldı. Lütfen farklı bir PDF dosyası deneyin.');
      }

      // Mevcut dosya listesini al veya yeni liste oluştur
      let currentFiles = [];
      
      // uploadResult.files varsa kullan, yoksa componentData'dan al
      if (uploadResult.files && Array.isArray(uploadResult.files)) {
        currentFiles = uploadResult.files;
      } else {
        // Mevcut dosyaları state'den al
        const componentAnswers = componentData[component]?.answers || {};
        const existingValue = componentAnswers[questionId];
        
        if (existingValue) {
          // String ise JSON.parse et
          if (typeof existingValue === 'string') {
            try {
              const parsed = JSON.parse(existingValue);
              if (Array.isArray(parsed)) {
                currentFiles = parsed;
              } else if (typeof parsed === 'object') {
                currentFiles = [parsed]; // Tek nesne ise diziye dönüştür
              }
            } catch (e) {
              // JSON parse hatası, yeni dizi kullan
              console.warn('JSON parse error for existing files:', e);
            }
          } else if (Array.isArray(existingValue)) {
            currentFiles = existingValue;
          } else if (typeof existingValue === 'object') {
            currentFiles = [existingValue]; // Tek nesne ise diziye dönüştür
          }
        }
        
        // Yeni PDF bilgisini oluştur ve ekle
        const newFileInfo = {
          filename: file.name,
          path: uploadResult.filePath || "",
          type: "pdf",
          uploaded_at: new Date().toISOString()
        };
        
        currentFiles.push(newFileInfo);
      }
      
      // Başarı mesajı
      toast.success(`${file.name} başarıyla yüklendi ve ${component} bileşenine kaydedildi.`);

      // --- update state with full PDF list ---
      dispatch({
        type: 'UPDATE_ANSWER',
        payload: { component, questionId, value: currentFiles }
      });
      // -----------------------------------------
      
    } catch (error) {
      console.error(`${component} - PDF işleme hatası:`, error);
      toast.error(`PDF yüklenirken hata oluştu: ${error.message || 'Bilinmeyen hata'}`);
      
      // Hata durumunda cevabı temizle
      dispatch({ 
        type: 'UPDATE_ANSWER', 
        payload: { component, questionId, value: '' } 
      });
      
      // Hata detaylarını loglama
      if (error.response) {
        console.error(`${component} - API yanıt detayı:`, error.response.data);
        console.error(`${component} - Status kodu:`, error.response.status);
      }
    } finally {
      dispatch({ type: 'SET_PDF_LOADING', payload: { key: loadingKey, isLoading: false } });
    }
  };
  
  // Bileşen görseli yükleme
  const handleComponentImageUpload = async (component, questionId, event) => {
    const file = event.target.files[0];
    if (!file) {
      console.log(`${component} - Görsel seçilmedi`);
      return;
    }
    
    console.log(`${component} - Seçilen görsel: ${file.name}, ${file.type}, ${file.size} bytes`);
    
    // Görsel dosya tipini kontrol et
    if (!file.type.match('image.*')) {
      console.error(`${component} - Geçersiz dosya türü: ${file.type}`);
      toast.error('Lütfen sadece resim dosyaları yükleyin.');
      return;
    }
    
    // Dosya boyutunu kontrol et (5MB limit)
    const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
    if (file.size > MAX_FILE_SIZE) {
      console.error(`${component} - Dosya boyutu çok büyük: ${file.size} bytes`);
      toast.error('Görsel boyutu 5MB\'dan küçük olmalıdır.');
      return;
    }
    
    const loadingKey = `${component}-${questionId}-image`;
    dispatch({ type: 'SET_IMAGE_LOADING', payload: { key: loadingKey, isLoading: true } });
    
    try {
      console.log(`${component} - Görsel yükleme işlemi başlatılıyor...`);
      
      // Görsel indeksi tespit et (bu örnekte ilk görsel yüklendiğini varsayıyoruz)
      const imageIndex = 0;
      
      const result = await componentService.uploadComponentImage(
        projectName,
        component,
        file,
        imageIndex,
        questionId // Soru ID'sini ekledik
      );
      
      console.log(`${component} - Görsel yükleme sonucu:`, result);
      
      if (!result || !result.success) {
        throw new Error('Görsel yükleme başarısız oldu');
      }
      
      // Başarı mesajı
      toast.success(`${file.name} başarıyla yüklendi`);
      
      // Yeni dosya dizisini componentData içine kaydet
      if (result.files && Array.isArray(result.files)) {
        dispatch({ 
          type: 'UPDATE_ANSWER', 
          payload: { 
            component, 
            questionId, 
            value: result.files            // store as array
          } 
        });
      } else {
        // Eski davranış ile uyumluluk için
        const imageName = result.file_name || file.name;
        
        dispatch({ 
          type: 'UPDATE_ANSWER', 
          payload: { 
            component, 
            questionId, 
            value: [{
              filename: imageName,
              path: result.filePath || "",
              type: "image"
            }]
          } 
        });
      }
      
    } catch (error) {
      console.error(`${component} - Görsel yükleme hatası:`, error);
      toast.error(`Görsel yüklenirken hata oluştu: ${error.message || 'Bilinmeyen hata'}`);
      
      // Hata detaylarını loglama
      if (error.response) {
        console.error(`${component} - API yanıt detayı:`, error.response.data);
        console.error(`${component} - Status kodu:`, error.response.status);
      }
    } finally {
      dispatch({ type: 'SET_IMAGE_LOADING', payload: { key: loadingKey, isLoading: false } });
    }
  };
  
  // Bileşen görseli kaldırma
  const handleRemoveComponentImage = async (component, questionId, imageIndex = 0) => {
    try {
      // Görsel referansını temizle
      dispatch({ 
        type: 'UPDATE_ANSWER', 
        payload: { 
          component, 
          questionId: `${questionId}_image_${imageIndex}`, 
          value: '' 
        } 
      });
      
      // Backend'e boş değeri kaydet
      await componentService.saveComponentData(
        projectName,
        component,
        { [`${questionId}_image_${imageIndex}`]: '' } // Boş string göndererek temizle
      );
      
      console.log(`${component} bileşeninden görsel kaldırıldı (${questionId})`);
      toast.info('Görsel kaldırıldı');
    } catch (error) {
      console.error(`${component} - Görsel kaldırma hatası:`, error);
      toast.error(`Görsel kaldırılırken hata oluştu: ${error.message || 'Bilinmeyen hata'}`);
    }
  };

  const handleRemoveComponentPdf = async (component, questionId, fileToRemove) => {
    try {
      const form = new FormData();
      form.append('component', component);
      form.append('question_id', questionId);
      form.append('filename', fileToRemove.filename);
      form.append('path', fileToRemove.path);

      // backend: remove from JSON
      await axios.post(`/project/${encodeURIComponent(projectName)}/remove-file`, form);

      // update local array
      const updatedFiles = ensureArray(componentData[component].answers[questionId])
        .filter(f => !(f.filename === fileToRemove.filename && f.path === fileToRemove.path));

      dispatch({
        type: 'UPDATE_ANSWER',
        payload: { component, questionId, value: updatedFiles }
      });
    } catch (e) {
      toast.error('PDF silinirken hata: ' + (e.message || 'bilinmeyen'));
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
    if (!validateRequiredFields()) {
      return;
    }
    
    setSavingReport(true);
    
    try {
      // Arka planda işlem başlatıldı bildirimi
      toast.info('Rapor oluşturma işlemi başlatıldı. Bu işlem arka planda gerçekleşecektir.');
      
      // Tüm bileşenlerin güncel verilerini kaydet (her ihtimale karşı)
      const savedComponents = [];
      for (const component of components) {
        try {
          console.log(`${component} bileşen verileri kaydediliyor...`);
          await componentService.saveComponentData(
            projectName,
            component,
            componentData[component].answers // Tüm cevapları gönder
          );
          console.log(`${component} bileşeni başarıyla kaydedildi.`);
          savedComponents.push(component);
        } catch (error) {
          console.error(`${component} bileşeni verileri kaydedilirken hata:`, error);
          toast.error(`${component} bileşeni verileri kaydedilemedi: ${error.message}`);
          // İşleme devam et, diğer bileşenleri de kaydetmeye çalış
        }
      }
      
      if (savedComponents.length === 0) {
        throw new Error("Hiçbir bileşen verisi kaydedilemedi. Lütfen tekrar deneyin.");
      }
      
      // Bileşen verilerini backend'e gönderilecek formata getir
      const componentsDataForBackend = {};
      savedComponents.forEach(component => {
        // Sadece "answers" objesini al, içindeki PDF objeleriyle birlikte
        componentsDataForBackend[component] = {
            answers: componentData[component].answers
        }; 
      });
      
      console.log("Rapor oluşturmak için backend'e gönderilecek veriler:", componentsDataForBackend);
      
      // Raporu oluştur
      try {
        console.log('Rapor oluşturma isteği gönderiliyor:', { projectName });
        
        // generateReport fonksiyonunu çağır (artık user_input ve pdf_content null)
        const result = await reportService.generateReport(
          projectName, 
          componentsDataForBackend, // Eski formatta veri
          null, 
          null  
        );
        
        // PDF dosya adını al
        const pdfPath = result.pdf_path;
        const pdfFileName = pdfPath ? pdfPath.split('/').pop() : null;
        
        // Rapor başarıyla oluşturulduğunda aktif raporu güncelle
        const updatedReport = await projectService.getActiveReport(projectName);
        dispatch({ type: 'SET_ACTIVE_REPORT', payload: { ...updatedReport, pdfFileName: pdfFileName } });
        
        console.log('Rapor başarıyla oluşturuldu:', updatedReport);
        toast.success('Rapor başarıyla oluşturuldu ve vitrine eklendi.');
        
      } catch (error) {
        console.error('Rapor oluşturma hatası:', error);
        let errorMessage = 'Bilinmeyen bir hata';
        
        if (error.message) {
          errorMessage = error.message;
        } else if (Array.isArray(error)) {
          errorMessage = error.map(e => e?.message || e).join(', ');
        } else if (typeof error === 'object') {
          errorMessage = JSON.stringify(error);
        } else {
          errorMessage = String(error);
        }
        
        toast.error(`Rapor oluşturulamadı: ${errorMessage}`);
        throw error; // Hatayı yukarı taşı
      }
      
    } catch (error) {
      console.error('Rapor oluşturma işlemi başarısız:', error);
      
      let errorMessage = 'Bilinmeyen bir hata';
      
      if (error.message) {
        errorMessage = error.message;
      } else if (Array.isArray(error)) {
        errorMessage = error.map(e => e?.message || e).join(', ');
      } else if (typeof error === 'object') {
        errorMessage = JSON.stringify(error);
      } else {
        errorMessage = String(error);
      }
      
      toast.error(`Rapor oluşturulamadı: ${errorMessage}`);
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

      <div className="flex flex-col lg:flex-row">
        {/* Ana İçerik - Bileşenler */}
        <div className="flex-1 max-w-3xl mx-auto">
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
                                        onClick={() => handleRemoveComponentImage(component, imageQuestionId, index)}
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
          </div>
            </div>
            
        {/* Sağ Panel - Bileşenler Listesi */}
        <div className="w-64 ml-8 hidden lg:block">
          <div className="bg-white rounded-lg shadow-lg p-4 sticky top-8">
            <ul className="space-y-2">
              {components.map(component => (
                <li key={`toc-${component}`}>
                    <button
                    onClick={() => scrollToComponent(component)}
                    className={`w-full text-left px-3 py-2 rounded-md transition-all duration-200 ${
                      activeSection === component
                        ? 'bg-blue-100 text-blue-700 font-medium text-lg'
                        : 'text-gray-700 hover:bg-gray-100 text-sm'
                    }`}
                  >
                    {component}
                    </button>
                </li>
              ))}
            </ul>
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
