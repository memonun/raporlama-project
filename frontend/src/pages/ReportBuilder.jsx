import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectService, componentService, mailService } from '../services/api';
import { reportService } from '../services/reportService';
import { axiosInstance } from '../services/api';
import { useToast } from '../context/ToastContext';

const ReportBuilder = () => {
  const { projectName } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [components, setComponents] = useState([]);
  const [componentData, setComponentData] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeReport, setActiveReport] = useState(null);
  const [savingReport, setSavingReport] = useState(false);
  const [activeSection, setActiveSection] = useState('');
  const [emailSending, setEmailSending] = useState(false);
  const componentRefs = useRef({});
  const scrollTimerRef = useRef(null);
  
  // Rapor sonlandırma için onay dialog
  const [showFinalizeDialog, setShowFinalizeDialog] = useState(false);
  const [finalizing, setFinalizing] = useState(false);

  const [error, setError] = useState(null);
  const [reportData, setReportData] = useState(null);

  // Component state tanımlamalarına eklemeler
  const [userInput, setUserInput] = useState('');
  const [pdfFile, setPdfFile] = useState(null);
  const [pdfContent, setPdfContent] = useState('');
  const [pdfLoading, setPdfLoading] = useState(false);
  
  // Sahte dosya oluşturucu helper
  const initializeFakePdf = (content) => {
    if (!content) return;
    
    const fakeFile = {
      name: 'Kaydedilmiş PDF',
      size: content.length,
      type: 'application/pdf',
    };
    setPdfFile(fakeFile);
    setPdfContent(content);
    console.log('initializeFakePdf - Sahte PDF objesi oluşturuldu:', fakeFile);
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

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Aktif raporu kontrol et
        const reportData = await projectService.getActiveReport(projectName);
        console.log('useEffect - Fetched active report data:', reportData);
        
        if (!reportData) {
          toast.warning('Aktif rapor bulunamadı, ana sayfaya yönlendiriliyorsunuz');
          navigate(`/project/${projectName}`);
          return;
        }
        
        setActiveReport(reportData);
        
        // PDF içeriğini al ve state'e yükle
        if (reportData.pdf_content) {
          console.log('useEffect - Saved PDF content found:', reportData.pdf_content.substring(0, 100) + '...');
          // initializeFakePdf helper fonksiyonunu kullan
          initializeFakePdf(reportData.pdf_content);
        } else {
           console.log('useEffect - No saved pdf_content found in reportData.');
        }
        
        // Bileşenleri getir
        const componentsData = await componentService.getComponents();
        
        if (!componentsData || componentsData.length === 0) {
          toast.error('Bileşenler yüklenemedi, lütfen daha sonra tekrar deneyin');
          return;
        }
        
        setComponents(componentsData);
        if (componentsData.length > 0) {
          setActiveSection(componentsData[0]);
        }
        
        // Tüm bileşenlerin sorularını ve cevaplarını getir
        const componentDataObj = {};
        
        for (const component of componentsData) {
          try {
            const questions = await componentService.getQuestions(component);
            
            if (!Array.isArray(questions) || questions.length === 0) {
              toast.warning(`${component} bileşeni için soru bulunamadı.`);
              componentDataObj[component] = {
                questions: [],
                answers: {}
              };
              continue;
            }
            
            // Kaydedilmiş cevapları yükle
            let savedAnswers = {};
            if (reportData && reportData.components && reportData.components[component]) {
              savedAnswers = reportData.components[component].answers || {};
            }
            
            componentDataObj[component] = {
              questions: questions,
              answers: savedAnswers
            };
          } catch (error) {
            console.error(`${component} bileşeni soruları yüklenirken hata:`, error);
            toast.error(`${component} bileşeni soruları yüklenirken hata oluştu: ${error.message || 'Bilinmeyen hata'}`);
            componentDataObj[component] = {
              questions: [],
              answers: {}
            };
          }
        }
        
        setComponentData(componentDataObj);
      } catch (error) {
        toast.error(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [projectName, navigate, toast]);

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
      setActiveSection(closestComponent);
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
    setActiveSection(component);
    if (componentRefs.current[component]) {
      componentRefs.current[component].scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
      });
    }
  };
  
  const handleAnswerChange = (component, questionId, value) => {
    setComponentData(prev => ({
      ...prev,
      [component]: {
        ...prev[component],
        answers: {
          ...prev[component].answers,
          [questionId]: value
        }
      }
    }));
  };

  // Bileşen için PDF dosyası yükleme
  // const handleComponentPdfUpload = async (component, questionId, event) => {
  //   // ... implementation ...
  // };
  
  // Bileşen PDF dosyasını kaldırma
  // const handleRemoveComponentPdf = (component, questionId) => {
  //   // ... implementation ...
  // };

  const validateRequiredFields = () => {
    let isValid = true;
    let missingComponents = [];

    Object.keys(componentData).forEach(component => {
      const { questions, answers } = componentData[component];
      
      // PDF alanı zorunlu, diğerleri opsiyonel
      const pdfQuestion = questions.find(q => q.type === 'file' && q.required);
      
      if (pdfQuestion && (!answers[pdfQuestion.id] || answers[pdfQuestion.id] === '')) {
        isValid = false;
        missingComponents.push(component);
      }
    });

    if (!isValid) {
      toast.error(`Lütfen ${missingComponents.join(', ')} bileşenlerine ait zorunlu PDF alanlarını doldurun.`);
    }

    return isValid;
  };

  // PDF dosyasını yükleyip içeriğini çıkaran fonksiyon
  const handlePdfUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    // Sadece PDF dosyalarını kabul et
    if (file.type !== 'application/pdf') {
      toast.error('Lütfen sadece PDF dosyası yükleyin.');
      return;
    }
    
    setPdfFile(file);
    setPdfLoading(true);
    
    try {
      // PDF içeriğini çıkar
      const extractedContent = await reportService.extractPdfContent(file);
      console.log('handlePdfUpload - PDF içeriği çıkarıldı:', extractedContent.substring(0, 100) + '...');
      
      // PDF içeriğini state'e ve backend'e kaydet
      setPdfContent(extractedContent);
      
      // PDF içeriğini projeye kalıcı olarak kaydet
      try {
        await reportService.savePdfContent(projectName, extractedContent);
        console.log('handlePdfUpload - PDF içeriği proje verisine kaydedildi');
      } catch (saveError) {
        console.error('PDF içeriği kalıcı kaydetme hatası:', saveError);
        toast.warning('PDF içeriği kalıcı olarak kaydedilemedi, sayfa yenilenirse kaybolabilir.');
      }
      
      toast.success('PDF içeriği başarıyla çıkarıldı');
    } catch (error) {
      console.error('PDF yükleme hatası:', error);
      toast.error(`PDF işleme hatası: ${error.message}`);
      setPdfFile(null);
    } finally {
      setPdfLoading(false);
    }
  };

  // PDF dosyasını kaldırma işlevi
  const handleRemovePdf = () => {
    // PDF state'lerini temizle
    setPdfFile(null);
    setPdfContent('');
    
    // PDF içeriğini backend'den de temizle
    try {
      reportService.savePdfContent(projectName, '');
      console.log('handleRemovePdf - PDF içeriği backend\'den silindi');
    } catch (error) {
      console.error('PDF içeriği backend\'den silme hatası:', error);
      toast.warning('PDF içeriği kalıcı olarak silinirken hata oluştu.');
    }
  };

  // Rapor oluşturma fonksiyonunu güncelleme
  const handleGenerateReport = async () => {
    if (!validateRequiredFields()) {
      return;
    }
    
    setSavingReport(true);
    
    try {
      // Arka planda işlem başlatıldı bildirimi
      toast.info('Rapor oluşturma işlemi başlatıldı. Bu işlem arka planda gerçekleşecektir.');
      
      // Tüm bileşenlerin verilerini kaydet
      const savedComponents = [];
      for (const component of components) {
        try {
          console.log(`${component} bileşen verileri kaydediliyor...`);
          await componentService.saveComponentData(
            projectName,
            component,
            componentData[component].answers
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
      
      // Bileşen verilerini hazırla
      const componentsData = {};
      savedComponents.forEach(component => {
        componentsData[component] = componentData[component].answers;
      });
      
      console.log('Rapor oluşturmak için bileşen verileri:', componentsData);
      console.log('PDF içeriği gönderilecek mi?', pdfContent ? 'Evet' : 'Hayır');
      
      // Raporu oluştur
      try {
        // Genişletilmiş generateReport fonksiyonunu kullan (üç veri kaynağı ile)
        const result = await reportService.generateReport(
          projectName, 
          componentsData,
          userInput || null,  // Kullanıcı girdisi varsa gönder, yoksa null
          pdfContent || null  // PDF içeriği varsa gönder, yoksa null
        );
        
        // PDF dosya adını al
        const pdfPath = result.pdf_path;
        const pdfFileName = pdfPath ? pdfPath.split('/').pop() : null;
        
        // Rapor başarıyla oluşturulduğunda aktif raporu güncelle
        const updatedReport = await projectService.getActiveReport(projectName);
        setActiveReport({
          ...updatedReport,
          pdfFileName: pdfFileName
        });
        
        console.log('Rapor başarıyla oluşturuldu:', updatedReport);
        toast.success('Rapor başarıyla oluşturuldu ve vitrine eklendi.');
        
      } catch (error) {
        console.error('Rapor oluşturma hatası:', error);
        toast.error(`Rapor oluşturulamadı: ${error.message}`);
        throw error; // Hatayı yukarı taşı
      }
      
    } catch (error) {
      console.error('Rapor oluşturma işlemi başarısız:', error);
      toast.error(`Rapor oluşturulamadı: ${error.message}`);
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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <p className="ml-3 text-blue-600">Rapor verileri yükleniyor...</p>
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
            {components.map(component => (
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
                    {componentData[component].questions.map(question => (
                      <div key={question.id} className="space-y-2 border-b pb-6">
                        <label className="block text-sm font-medium text-gray-700">
                          {question.text}
                          {question.required && <span className="text-red-500 ml-1">*</span>}
                        </label>
                        
                        {question.type === 'text' && (
                          <input
                            type="text"
                            value={componentData[component].answers[question.id] || ''}
                            onChange={(e) => handleAnswerChange(component, question.id, e.target.value)}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                            placeholder={question.placeholder || ''}
                            required={question.required}
                          />
                        )}
                        
                        {question.type === 'textarea' && (
                          <textarea
                            value={componentData[component].answers[question.id] || ''}
                            onChange={(e) => handleAnswerChange(component, question.id, e.target.value)}
                            rows={4}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                            placeholder={question.placeholder || ''}
                            required={question.required}
                          />
                        )}
                        
                        {question.type === 'select' && (
                          <select
                            value={componentData[component].answers[question.id] || ''}
                            onChange={(e) => handleAnswerChange(component, question.id, e.target.value)}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                            required={question.required}
                          >
                            <option value="">Seçiniz</option>
                            {Array.isArray(question.options) && question.options.map(option => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                        )}
                        
                        {question.type === 'file' && (
                          <div className="mt-1">
                            <div className="flex flex-col space-y-2">
                              {componentData[component]?.answers[question.id] ? (
                                // Yüklenmiş dosyayı göster
                                <div className="flex items-center justify-between p-2 bg-gray-50 rounded-md border border-gray-200">
                                  <div className="flex items-center">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                    <span className="text-sm font-medium text-gray-700">
                                      {/* Display the string value directly */}
                                      {componentData[component].answers[question.id]}
                                    </span>
                                  </div>
                                  <button
                                    type="button"
                                    onClick={() => handleAnswerChange(component, question.id, '')}
                                    className="ml-2 flex-shrink-0 text-red-500 hover:text-red-700"
                                    title="Dosyayı kaldır"
                                  >
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                    </svg>
                                  </button>
                                </div>
                              ) : (
                                // Dosya yükleme alanı
                                <input
                                  type="file"
                                  accept="application/pdf"
                                  onChange={(e) => handleAnswerChange(component, question.id, e.target.files[0]?.name)}
                                  className="block w-full text-sm text-gray-500
                                    file:mr-4 file:py-2 file:px-4
                                    file:rounded-md file:border-0
                                    file:text-sm file:font-semibold
                                    file:bg-blue-50 file:text-blue-700
                                    hover:file:bg-blue-100"
                                  required={question.required}
                                />
                              )}
                            </div>
                          </div>
                        )}
                        
                        {question.description && (
                          <p className="mt-1 text-sm text-gray-500">{question.description}</p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">Bu bileşen için soru bulunamadı.</p>
                )}
              </div>
            ))}
          </div>

          {/* Ek Rapor Girdileri Bölümü - Kullanıcı notu ve PDF yükleme için */}
          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 className="text-xl font-bold text-gray-800 mb-4">Ek Rapor Girdileri</h2>
            
            {/* Kullanıcı Notu */}
            <div className="mb-6">
              <h3 className="text-md font-semibold text-gray-700 mb-2">Kullanıcı Notu</h3>
              <p className="text-sm text-gray-500 mb-2">
                Rapora eklemek istediğiniz ek notları buraya yazabilirsiniz. Bu alan opsiyoneldir.
              </p>
              <textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                rows={4}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                placeholder="Rapora eklemek istediğiniz ek notlar..."
              />
            </div>
            
            {/* PDF Yükleme */}
            <div>
              <h3 className="text-md font-semibold text-gray-700 mb-2">PDF Dosyası</h3>
              <p className="text-sm text-gray-500 mb-2">
                Rapora dahil etmek istediğiniz bir PDF dosyası yükleyebilirsiniz. Bu alan opsiyoneldir.
              </p>
              
              {!pdfFile?.name ? (
                <div className="mt-2">
                  <label className="block text-sm font-medium text-gray-700">
                    PDF Dosyası Seçin
                  </label>
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={handlePdfUpload}
                    className="block w-full text-sm text-gray-500
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-md file:border-0
                      file:text-sm file:font-semibold
                      file:bg-blue-50 file:text-blue-700
                      hover:file:bg-blue-100"
                  />
                </div>
              ) : (
                <div className="mt-2 p-3 bg-gray-50 rounded-md">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-800">{pdfFile.name}</p>
                      <p className="text-xs text-gray-500">{(pdfFile.size / 1024).toFixed(2)} KB</p>
                    </div>
                    
                    <button
                      onClick={handleRemovePdf}
                      className="ml-2 flex-shrink-0 text-red-500 hover:text-red-700 focus:outline-none"
                      title="Dosyayı kaldır"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </div>
                  
                  {pdfLoading ? (
                    <div className="mt-2 flex items-center text-sm text-blue-600">
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      İçerik çıkarılıyor...
                    </div>
                  ) : (
                    <p className="mt-2 text-xs text-green-600">
                      PDF içeriği başarıyla çıkarıldı ({pdfContent.length} karakter)
                    </p>
                  )}
                </div>
              )}
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

      {/* Sonlandırma onay dialog'u */}
      {showFinalizeDialog && <FinalizeDialog />}
    </div>
  );
};

export default ReportBuilder; 