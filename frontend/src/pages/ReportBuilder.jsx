import React, { useState, useEffect, useRef, useCallback, useReducer } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectService, componentService, mailService, reportService } from '../services/api';
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
    
    // En yakın bileşeni bul (ekranın orta noktasına göre)
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
  const validateInput = (value, question) => {
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
      formData.append('file', file);
      
      console.log(`${component} - FormData oluşturuldu, PDF içeriğini çıkarmak için API isteği gönderiliyor`);
      
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

      // Yeni PDF obje formatını oluştur
      const pdfObject = {
        fileName: file.name,
        content: extractedContent,
        questionId: questionId
      };

      // Obje'yi JSON string'ine çevir
      const pdfJsonString = JSON.stringify(pdfObject);

      // State'i güncelle ve backend'e kaydet
      dispatch({ 
        type: 'UPDATE_ANSWER', 
        payload: { component, questionId, value: pdfJsonString } 
      });

      await componentService.saveComponentData(
        projectName,
        component,
        { [questionId]: pdfJsonString }
      );
      
      // Başarı mesajı
      toast.success(`${file.name} başarıyla yüklendi ve içeriği ${component} bileşenine kaydedildi.`);
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
  
  // Bileşen PDF dosyasını kaldırma
  const handleRemoveComponentPdf = async (component, questionId) => {
    try {
      // Önce state'i güncelle
      handleAnswerChange(component, questionId, ''); // Boş string ata

      // Backend'e boş değeri kaydet
      await componentService.saveComponentData(
        projectName,
        component,
        { [questionId]: '' } // Boş string göndererek temizle
      );
      
      console.log(`${component} bileşeninden PDF dosyası kaldırıldı (${questionId})`);
      toast.info('PDF dosyası kaldırıldı');
    } catch (error) {
      console.error(`${component} - PDF kaldırma hatası:`, error);
      toast.error(`PDF kaldırılırken hata oluştu: ${error.message || 'Bilinmeyen hata'}`);
    }
  };
  
  const validateRequiredFields = () => {
    let isValid = true;
    let missingComponents = [];

    Object.keys(componentData).forEach(component => {
      const { questions, answers } = componentData[component];
      
      // PDF alanı zorunlu, diğerleri opsiyonel
      const pdfQuestion = questions.find(q => q.type === 'file' && q.required);
      
      if (pdfQuestion && (!answers[pdfQuestion.id] || answers[pdfQuestion.id] === null)) {
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
      
      // Blob olarak PDF'i al
      const blob = await reportService.downloadReport(projectName);
      
      // Blob tipini kontrol et - hata durumunu yakala
      if (!(blob instanceof Blob)) {
        console.error('Dönen veri Blob değil:', blob);
        if (typeof blob === 'object') {
          console.error('Dönen içerik:', JSON.stringify(blob));
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
      console.error('PDF indirme hatası:', error);
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
                
                {componentData[component] && componentData[component].questions.length > 0 ? (
                  <div className="space-y-6">
                    {componentData[component].questions.map((question, index) => {
                      const isLoadingPdf = pdfLoadingStates[`${component}-${question.id}`] || false;
                      return (
                        <div key={question.id} className="space-y-2 border-b pb-6">
                          <label className="block text-sm font-medium text-gray-700">
                            {question.text}
                            {question.required && <span className="text-red-500 ml-1">*</span>}
                          </label>
                          
                          {/* Input render bölümü */}
                          {question.type === 'text' && (
                            <div className="relative">
                              <input
                                type="text"
                                value={componentData[component].answers[question.id] || ''}
                                onChange={(e) => handleAnswerChange(component, question.id, e.target.value, question)}
                                onKeyDown={(e) => handleKeyDown(component, index, e)}
                                data-question-id={question.id}
                                className={`mt-1 block w-full rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
                                  validationStates[`${component}-${question.id}`]?.isValid === false
                                    ? 'border-red-300'
                                    : validationStates[`${component}-${question.id}`]?.saved
                                    ? 'border-green-300'
                                    : 'border-gray-300'
                                }`}
                                placeholder={question.placeholder || ''}
                                required={question.required}
                                disabled={savingStates[`${component}-${question.id}`]}
                              />
                              
                              {/* Validasyon ve kaydetme durumu göstergeleri */}
                              <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center">
                                {savingStates[`${component}-${question.id}`] && (
                                  <svg className="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                  </svg>
                                )}
                                
                                {!savingStates[`${component}-${question.id}`] && validationStates[`${component}-${question.id}`]?.saved && (
                                  <svg className="h-4 w-4 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                  </svg>
                                )}
                              </div>
                              
                              {/* Hata mesajı */}
                              {validationStates[`${component}-${question.id}`]?.isValid === false && (
                                <p className="mt-1 text-sm text-red-600">
                                  {validationStates[`${component}-${question.id}`].message}
                                </p>
                              )}
                            </div>
                          )}
                          
                          {question.type === 'textarea' && (
                            <div className="relative">
                              <textarea
                                value={componentData[component].answers[question.id] || ''}
                                onChange={(e) => handleAnswerChange(component, question.id, e.target.value, question)}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter' && !e.shiftKey) {
                                    handleKeyDown(component, index, e);
                                  }
                                }}
                                data-question-id={question.id}
                                rows={4}
                                className={`mt-1 block w-full rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
                                  validationStates[`${component}-${question.id}`]?.isValid === false
                                    ? 'border-red-300'
                                    : validationStates[`${component}-${question.id}`]?.saved
                                    ? 'border-green-300'
                                    : 'border-gray-300'
                                }`}
                                placeholder={question.placeholder || ''}
                                required={question.required}
                                disabled={savingStates[`${component}-${question.id}`]}
                              />
                              
                              {/* Validasyon ve kaydetme durumu göstergeleri */}
                              <div className="absolute right-2 top-2 flex items-center">
                                {savingStates[`${component}-${question.id}`] && (
                                  <svg className="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                  </svg>
                                )}
                                
                                {!savingStates[`${component}-${question.id}`] && validationStates[`${component}-${question.id}`]?.saved && (
                                  <svg className="h-4 w-4 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                  </svg>
                                )}
                              </div>
                              
                              {/* Hata mesajı */}
                              {validationStates[`${component}-${question.id}`]?.isValid === false && (
                                <p className="mt-1 text-sm text-red-600">
                                  {validationStates[`${component}-${question.id}`].message}
                                </p>
                              )}
                            </div>
                          )}
                          
                          {question.type === 'select' && (
                            <div className="relative">
                              <select
                                value={componentData[component].answers[question.id] || ''}
                                onChange={(e) => handleAnswerChange(component, question.id, e.target.value, question)}
                                onKeyDown={(e) => handleKeyDown(component, index, e)}
                                data-question-id={question.id}
                                className={`mt-1 block w-full rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
                                  validationStates[`${component}-${question.id}`]?.isValid === false
                                    ? 'border-red-300'
                                    : validationStates[`${component}-${question.id}`]?.saved
                                    ? 'border-green-300'
                                    : 'border-gray-300'
                                }`}
                                required={question.required}
                                disabled={savingStates[`${component}-${question.id}`]}
                              >
                                <option value="">Seçiniz</option>
                                {Array.isArray(question.options) && question.options.map(option => (
                                  <option key={option.value} value={option.value}>
                                    {option.label}
                                  </option>
                                ))}
                              </select>
                              
                              {/* Validasyon ve kaydetme durumu göstergeleri */}
                              <div className="absolute right-8 top-1/2 transform -translate-y-1/2 flex items-center pointer-events-none">
                                {savingStates[`${component}-${question.id}`] && (
                                  <svg className="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                  </svg>
                                )}
                                
                                {!savingStates[`${component}-${question.id}`] && validationStates[`${component}-${question.id}`]?.saved && (
                                  <svg className="h-4 w-4 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                  </svg>
                                )}
                              </div>
                              
                              {/* Hata mesajı */}
                              {validationStates[`${component}-${question.id}`]?.isValid === false && (
                                <p className="mt-1 text-sm text-red-600">
                                  {validationStates[`${component}-${question.id}`].message}
                                </p>
                              )}
                            </div>
                          )}
                          
                          {question.type === 'file' && (
                            <div className="mt-1">
                              <div className="flex flex-col space-y-2">
                                {(() => {
                                  const answerString = componentData[component]?.answers[question.id];
                                  let pdfData = null;

                                  if (answerString && typeof answerString === 'string') {
                                    try {
                                      pdfData = JSON.parse(answerString);
                                    } catch (e) {
                                      console.error('PDF JSON parse hatası:', e);
                                    }
                                  }

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
                                  if (pdfData && pdfData.fileName) {
                                    return (
                                      <div className="flex items-center justify-between p-2 bg-gray-50 rounded-md border border-gray-200">
                                        <div className="flex items-center">
                                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                          </svg>
                                          <span className="text-sm font-medium text-gray-700">
                                            {pdfData.fileName}
                                          </span>
                                        </div>
                                        <button
                                          type="button"
                                          onClick={() => handleRemoveComponentPdf(component, question.id)}
                                          className="ml-2 flex-shrink-0 text-red-500 hover:text-red-700"
                                          title="Dosyayı kaldır"
                                        >
                                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                          </svg>
                                        </button>
                                      </div>
                                    );
                                  }
                                  
                                  // Hiçbir durum yoksa dosya yükleme alanını göster
                                  return (
                                    <input
                                      type="file"
                                      accept="application/pdf"
                                      onChange={(e) => handleComponentPdfUpload(component, question.id, e)}
                                      className="block w-full text-sm text-gray-500
                                        file:mr-4 file:py-2 file:px-4
                                        file:rounded-md file:border-0
                                        file:text-sm file:font-semibold
                                        file:bg-blue-50 file:text-blue-700
                                        hover:file:bg-blue-100"
                                      required={question.required}
                                      disabled={isLoadingPdf}
                                    />
                                  );
                                })()}
                              </div>
                            </div>
                          )}
                          
                          {question.description && (
                            <p className="mt-1 text-sm text-gray-500">{question.description}</p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-gray-500">Bu bileşen için soru bulunamadı.</p>
                )}
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
            İptal
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
