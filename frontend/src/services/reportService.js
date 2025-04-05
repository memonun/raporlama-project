import { axiosInstance } from './api';

/**
 * Rapor işlemleri için servis fonksiyonları
 */
export const reportService = {
  /**
   * Proje için rapor oluşturur
   * @param {string} projectName - Proje adı
   * @param {Object} componentsData - Bileşen verileri
   * @param {string} userInput - Kullanıcı tarafından girilen ek metin (opsiyonel)
   * @param {string} pdfContent - PDF dosyasından çıkarılan içerik (opsiyonel)
   * @returns {Promise<Object>} Oluşturulan rapor bilgileri
   */
  generateReport: async (projectName, componentsData, userInput = null, pdfContent = null) => {
    if (!projectName) {
      console.error('reportService.generateReport: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }

    try {
      console.log(`reportService.generateReport: ${projectName} projesi için rapor oluşturuluyor`);
      console.log('Gönderilen bileşen verileri (özet):', Object.keys(componentsData));
      
      // Debug için PDF içeriklerini kontrol edelim
      const pdfContentKeys = Object.keys(componentsData).filter(k => k.endsWith('_pdf_contents'));
      if (pdfContentKeys.length > 0) {
        console.log('PDF içerikleri mevcut:', pdfContentKeys);
        pdfContentKeys.forEach(key => {
          const pdfs = componentsData[key];
          console.log(`${key} içinde ${pdfs.length} adet PDF mevcut`);
          console.log('İlk PDF örneği:', JSON.stringify(pdfs[0], null, 2));
        });
      } else {
        console.warn('Hiç PDF içeriği bulunamadı!');
      }
      
      // Veri formatı dönüşümü yapmadan doğrudan API'ye gönder
      const requestPayload = { 
        project_name: projectName,
        components_data: componentsData,
        user_input: userInput,
        pdf_content: pdfContent
      };
      
      console.log('API isteği hazırlandı:', JSON.stringify(requestPayload, null, 2).substring(0, 1000) + '...');
      
      const response = await axiosInstance.post(`/project/generate-report`, requestPayload);
      
      console.log('Rapor oluşturma yanıtı:', response.data);
      return response.data;
    } catch (error) {
      console.error('Rapor oluşturma hatası:', error);
      
      if (error.response) {
        console.error('API Yanıt Detayı:', error.response.data);
        console.error('Durum Kodu:', error.response.status);
        
        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
        if (error.response.status === 404) {
           throw new Error('Rapor oluşturma uç noktası bulunamadı veya proje verisi eksik.');
        } 
        if (error.response.status === 422) {
          throw new Error('İstek formatı hatalı: API validasyon hatası. Geliştirici ile iletişime geçin.');
        }
        if (error.response.status === 500) {
          throw new Error('Rapor oluşturulurken sunucu hatası oluştu. Geliştirici ile iletişime geçin.');
        }
      } else if (error.request) {
        // İstek yapıldı ama yanıt alınamadı
        console.error('Yanıt alınamadı:', error.request);
        throw new Error('Sunucudan yanıt alınamadı. Lütfen internet bağlantınızı kontrol edin.');
      } else if (error.message) {
        // İstek ayarlarında sorun var
        console.error('İstek hatası:', error.message);
        throw new Error(`İstek hatası: ${error.message}`);
      } else {
        // Beklenmeyen hata
        console.error('Beklenmeyen hata:', error);
        throw new Error('Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.');
      }
      
      throw new Error('Rapor oluşturulurken bir sunucu hatası oluştu.');
    }
  },

  /**
   * Belirli bir raporun PDF dosyasını indirir
   * @param {string} projectName - Proje adı
   * @param {string} reportId - İndirilecek raporun ID'si
   * @returns {Promise<Blob>} PDF içeriği blob formatında
   */
  downloadReport: async (projectName, reportId) => {
    if (!projectName) {
      console.error('reportService.downloadReport: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }
    if (!reportId) {
      console.error('reportService.downloadReport: Rapor ID\'si belirtilmedi');
      throw new Error('Rapor ID\'si belirtilmedi');
    }

    try {
      console.log(`reportService.downloadReport: ${projectName} projesi için ${reportId} ID'li PDF indiriliyor`);
      
      const endpoint = `/project/${projectName}/report/${reportId}/download`;
      
      const response = await axiosInstance.get(endpoint, {
        responseType: 'blob'
      });
      
      console.log('PDF indirme başarılı');
      return response.data;
    } catch (error) {
      console.error('PDF indirme hatası:', error);
      
      if (error.response) {
        console.error('API Yanıt Detayı:', error.response.status, error.response.data);
        
        if (error.response.data && error.response.data.detail) {
            throw new Error(error.response.data.detail); 
        }
        if (error.response.status === 404) {
          throw new Error('Rapor veya PDF dosyası bulunamadı');
        } else if (error.response.status === 400) {
          throw new Error('Rapor henüz oluşturulmamış veya istek geçersiz');
        }
      }
      
      throw new Error('PDF indirilirken bir hata oluştu');
    }
  },

  /**
   * Proje için oluşturulmuş raporu siler (Aktif Raporu)
   * @param {string} projectName - Proje adı
   * @returns {Promise<Object>} Silme işlemi sonucu
   */
  deleteReport: async (projectName) => {
    if (!projectName) {
      console.error('reportService.deleteReport: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }

    try {
      console.log(`reportService.deleteReport: ${projectName} projesi için aktif rapor siliniyor`);
      
      // Use DELETE method and include projectName in the path
      const response = await axiosInstance.delete(`/project/${encodeURIComponent(projectName)}/delete-report`);
      
      console.log('Aktif rapor silme başarılı:', response.data);
      return response.data;
    } catch (error) {
      // Log the detailed error object
      console.error('reportService.deleteReport - Detaylı Hata:', error);
      let errorMessage = 'Rapor silinirken bir hata oluştu'; // Default message

      if (error.response) {
        console.error('reportService.deleteReport - API Yanıt Detayı:', error.response.data);
        console.error('reportService.deleteReport - Durum Kodu:', error.response.status);
        
        // Try to get the specific message from backend
        if (error.response.data && error.response.data.detail) {
            errorMessage = error.response.data.detail; 
        } else if (error.response.status === 404) {
            // Provide a more specific message for 404
            errorMessage = 'Silinecek rapor veya proje bulunamadı.';
        }
        // Add more specific status code checks here if needed
      } else if (error.message) {
        // If it's not an Axios error but has a standard message property
        errorMessage = error.message;
      }
      
      // Always throw a standard Error object with a message
      throw new Error(errorMessage);
    }
  },

  /**
   * Proje için yeni bir rapor oluşturur (başlatır)
   * @param {string} projectName - Proje adı
   * @returns {Promise<Object>} Oluşturulan rapor bilgileri
   */
  createReport: async (projectName) => {
    if (!projectName) {
      console.error('reportService.createReport: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }

    try {
      console.log(`reportService.createReport: ${projectName} projesi için yeni rapor başlatılıyor`);
      
      const requestData = {
        project_name: projectName
      };
      
      console.log('Gönderilen veri:', requestData);
      
      const response = await axiosInstance.post('/project/create-report', requestData, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Rapor başlatma başarılı:', response.data);
      return response.data;
    } catch (error) {
      console.error('Rapor başlatma hatası:', error);
      
      if (error.response) {
        console.error('API Yanıt Detayı:', error.response.data);
        console.error('Durum Kodu:', error.response.status);
        
        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
      }
      
      throw new Error('Yeni rapor oluşturulurken bir hata oluştu');
    }
  },

  /**
   * Proje için aktif raporu getirir
   * @param {string} projectName - Proje adı
   * @returns {Promise<Object>} Aktif rapor bilgileri
   */
  getActiveReport: async (projectName) => {
    if (!projectName) {
      console.error('reportService.getActiveReport: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }

    try {
      console.log(`reportService.getActiveReport: ${projectName} projesi için aktif rapor getiriliyor`);
      
      const response = await axiosInstance.get(`/project/${projectName}/report/active`);
      
      // Eğer aktif rapor varsa ve finalized değilse döndür
      if (response.data && !response.data.is_finalized) {
        console.log('Aktif rapor getirme başarılı:', response.data);
        return response.data;
      } else if (response.data && response.data.is_finalized) {
        console.log('Aktif rapor finalized olduğu için null dönülüyor:', response.data);
        return null;
      }
      
      console.log('Aktif rapor getirme başarılı:', response.data);
      return response.data;
    } catch (error) {
      console.error('Aktif rapor getirme hatası:', error);
      
      if (error.response) {
        console.error('API Yanıt Detayı:', error.response.data);
        console.error('Durum Kodu:', error.response.status);
        
        // 404 hatası rapor bulunamadığında normaldir
        if (error.response.status === 404) {
          return null;
        }
        
        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
      }
      
      throw new Error('Aktif rapor getirilirken bir hata oluştu');
    }
  },

  /**
   * Raporu sonlandır
   * @param {string} projectName - Proje adı
   * @returns {Promise<Object>} Sonlandırma işlemi sonucu
   */
  finalizeReport: async (projectName) => {
    if (!projectName) {
      console.error('reportService.finalizeReport: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }
    
    try {
      console.log(`reportService.finalizeReport: ${projectName} projesi raporu sonlandırılıyor`);
      
      const response = await axiosInstance.post('/project/finalize-report', {
        project_name: projectName
      });
      
      return response.data;
    } catch (error) {
      console.error('Rapor sonlandırma hatası:', error);
      throw new Error('Rapor sonlandırılırken bir hata oluştu');
    }
  },

  /**
   * Proje için sonlandırılmış raporları getirir
   * @param {string} projectName - Proje adı
   * @returns {Promise<Array>} Sonlandırılmış raporların listesi
   */
  getFinalizedReports: async (projectName) => {
    if (!projectName) {
      console.error('reportService.getFinalizedReports: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }

    try {
      console.log(`reportService.getFinalizedReports: ${projectName} projesi için sonlandırılmış raporlar getiriliyor`);
      
      const response = await axiosInstance.get(`/project/${projectName}/finalized-reports`);
      
      console.log('Sonlandırılmış raporlar başarıyla getirildi:', response.data);
      return response.data;
    } catch (error) {
      console.error('Sonlandırılmış raporları getirme hatası:', error);
      
      if (error.response) {
        console.error('API Yanıt Detayı:', error.response.data);
        console.error('Durum Kodu:', error.response.status);
        
        if (error.response.status === 404) {
          return [];
        }
        
        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
      }
      
      throw new Error('Sonlandırılmış raporlar getirilirken bir hata oluştu');
    }
  },

  /**
   * Sonlandırılmış (is_finalized: true) bir rapor dosyasını siler
   * @param {string} projectName - Proje adı
   * @param {string} fileName - Silinecek dosya adı
   * @returns {Promise<Object>} Silme işlemi sonucu
   */
  deleteFinalizedReport: async (projectName, fileName) => {
    if (!projectName) {
      console.error('reportService.deleteFinalizedReport: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }
    
    if (!fileName) {
      console.error('reportService.deleteFinalizedReport: Dosya adı belirtilmedi');
      throw new Error('Dosya adı belirtilmedi');
    }

    try {
      console.log(`reportService.deleteFinalizedReport: ${projectName} projesi için ${fileName} raporu siliniyor`);
      
      const response = await axiosInstance.post('/project/delete-finalized-report', {
        project_name: projectName,
        file_name: fileName
      });
      
      console.log('Finalized rapor silme başarılı:', response.data);
      return response.data;
    } catch (error) {
      console.error('Finalized rapor silme hatası:', error);
      
      if (error.response) {
        console.error('API Yanıt Detayı:', error.response.data);
        console.error('Durum Kodu:', error.response.status);
        
        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        } else if (error.response.status === 404) {
          throw new Error('Silinecek rapor veya proje bulunamadı.');
        }
      }
      
      throw new Error('Finalized rapor silinirken bir hata oluştu.');
    }
  },

  /**
   * PDF dosyasındaki içeriği çıkarır
   * @param {File} pdfFile - İçeriği çıkarılacak PDF dosyası
   * @returns {Promise<string>} PDF'den çıkarılan metin içeriği
   */
  extractPdfContent: async (pdfFile) => {
    if (!pdfFile || !(pdfFile instanceof File)) {
      console.error('reportService.extractPdfContent: Geçerli bir dosya belirtilmedi');
      throw new Error('Geçerli bir dosya belirtilmedi');
    }

    // Dosya türü kontrolü
    if (pdfFile.type !== 'application/pdf') {
      console.error('reportService.extractPdfContent: Sadece PDF dosyaları işlenebilir');
      throw new Error('Sadece PDF dosyaları işlenebilir');
    }

    console.log(`[PDF Çıkarma] İşlem başlatılıyor: ${pdfFile.name}, ${pdfFile.size} bytes`);
    
    try {
      // FormData ile dosya gönderimi
      const formData = new FormData();
      formData.append('file', pdfFile);
      
      console.log('[PDF Çıkarma] FormData oluşturuldu, istek gönderiliyor');
      
      const response = await axiosInstance.post('/extract-pdf', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      console.log('[PDF Çıkarma] Başarılı yanıt. İçerik uzunluğu:', 
                 response.data?.content?.length || 'İçerik yok');
      
      if (!response.data || !response.data.content) {
        console.error('[PDF Çıkarma] Yanıtta içerik alanı yok:', response.data);
        throw new Error('PDF içeriği sunucudan boş döndü');
      }
      
      return response.data.content;
    } catch (error) {
      console.error('[PDF Çıkarma] Hata:', error);
      
      if (error.response) {
        console.error('[PDF Çıkarma] API Yanıt Detayı:', error.response.data);
        console.error('[PDF Çıkarma] Status kodu:', error.response.status);
        
        if (error.response.data && error.response.data.detail) {
          throw new Error(`PDF çıkarma hatası: ${error.response.data.detail}`);
        }
      }
      
      throw new Error('PDF içeriği çıkarılırken bir hata oluştu: ' + (error.message || 'Bilinmeyen hata'));
    }
  },

  /**
   * PDF içeriğini proje verisine kaydetmek için
   * @param {string} projectName - Proje adı
   * @param {string} pdfContent - PDF içeriği
   * @param {string} filename - PDF dosyasının adı (opsiyonel)
   * @returns {Promise<Object>} İşlem sonucu
   */
  savePdfContent: async (projectName, pdfContent, filename = null) => {
    if (!projectName) {
      console.error('reportService.savePdfContent: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }
    
    console.log(`[PDF Kaydetme] İşlem başlatılıyor: ${projectName}`);
    console.log(`[PDF Kaydetme] İçerik uzunluğu: ${pdfContent ? pdfContent.length : 0} karakter`);
    console.log(`[PDF Kaydetme] Dosya adı: "${filename || 'belirtilmemiş'}"`);
    
    try {
      // PDF içeriğini component verisi olarak kaydet
      const payload = {
        project_name: projectName,
        component_name: 'pdf_content', // Backend'de özel olarak işlenecek
        answers: {
          content: pdfContent
        }
      };
      
      // Dosya adı varsa ekle
      if (filename) {
        payload.answers.filename = filename;
        console.log(`[PDF Kaydetme] Dosya adı payload'a eklendi: "${filename}"`);
      } else {
        console.log('[PDF Kaydetme] Dosya adı belirtilmediği için eklenmedi');
      }
      
      console.log('[PDF Kaydetme] Backend isteği gönderiliyor:', JSON.stringify(payload).substring(0, 100) + '...');
      
      const response = await axiosInstance.post('/component/save-data', payload);
      
      console.log('[PDF Kaydetme] Backend yanıtı:', response.data);
      return response.data;
    } catch (error) {
      console.error('[PDF Kaydetme] Hata:', error);
      
      if (error.response) {
        console.error('[PDF Kaydetme] API Yanıt Detayı:', error.response.data);
        console.error('[PDF Kaydetme] Status kodu:', error.response.status);
        
        if (error.response.data && error.response.data.detail) {
          throw new Error(`PDF kaydetme hatası: ${error.response.data.detail}`);
        }
      }
      
      throw new Error('PDF içeriği kaydedilirken bir hata oluştu: ' + (error.message || 'Bilinmeyen hata'));
    }
  }
};

export default reportService; 