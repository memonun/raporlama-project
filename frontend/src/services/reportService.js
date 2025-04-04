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
      console.log('Gönderilen bileşen verileri:', componentsData);
      
      const response = await axiosInstance.post(`/project/generate-report`, { 
        project_name: projectName,
        components_data: componentsData,
        user_input: userInput,
        pdf_content: pdfContent
      });
      
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

    try {
      console.log(`reportService.extractPdfContent: ${pdfFile.name} dosyasından içerik çıkarılıyor...`);
      
      // FormData ile dosya gönderimi
      const formData = new FormData();
      formData.append('file', pdfFile);
      
      const response = await axiosInstance.post('/extract-pdf', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      console.log('PDF içeriği başarıyla çıkarıldı');
      return response.data.content;
    } catch (error) {
      console.error('PDF içeriği çıkarma hatası:', error);
      
      if (error.response) {
        console.error('API Yanıt Detayı:', error.response.data);
        console.error('Durum Kodu:', error.response.status);
        
        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
      }
      
      throw new Error('PDF içeriği çıkarılırken bir hata oluştu');
    }
  },

  /**
   * PDF içeriğini proje verisine kaydetmek için
   * @param {string} projectName - Proje adı
   * @param {string} pdfContent - PDF içeriği
   * @returns {Promise<Object>} İşlem sonucu
   */
  savePdfContent: async (projectName, pdfContent) => {
    if (!projectName) {
      console.error('reportService.savePdfContent: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }
    
    try {
      console.log(`reportService.savePdfContent: ${projectName} projesi için PDF içeriği kaydediliyor...`);
      
      // PDF içeriğini component verisi olarak kaydet
      const response = await axiosInstance.post('/component/save-data', {
        project_name: projectName,
        component_name: 'pdf_content', // Backend'de özel olarak işlenecek
        answers: {
          content: pdfContent
        }
      });
      
      console.log('PDF içeriği başarıyla kaydedildi');
      return response.data;
    } catch (error) {
      console.error('PDF içeriği kaydetme hatası:', error);
      
      if (error.response) {
        console.error('API Yanıt Detayı:', error.response.data);
        console.error('Durum Kodu:', error.response.status);
        
        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
      }
      
      throw new Error('PDF içeriği kaydedilirken bir hata oluştu.');
    }
  }
};

export default reportService; 