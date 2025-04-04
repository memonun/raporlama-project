import axios from 'axios';

// Development mode için API URL'ini düzenle
const API_BASE_URL = 'http://localhost:8000';

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Proje servisi
export const projectService = {
  // Tüm projeleri getir
  getProjects: async () => {
    try {
      console.log('projectService.getProjects: Tüm projeler getiriliyor');
      const response = await axiosInstance.get('/projects');
      return response.data;
    } catch (error) {
      console.error('Projeler getirme hatası:', error);
      throw new Error('Projeler getirilirken bir hata oluştu');
    }
  },
  
  // Proje detaylarını getir
  getProjectDetails: async (projectName) => {
    if (!projectName) {
      console.error('projectService.getProjectDetails: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }
    
    try {
      console.log(`projectService.getProjectDetails: ${projectName} projesi detayları getiriliyor`);
      const response = await axiosInstance.get(`/project/${encodeURIComponent(projectName)}`);
      return response.data;
    } catch (error) {
      console.error('Proje detayları getirme hatası:', error);
      if (error.response && error.response.status === 404) {
        throw new Error(`"${projectName}" projesi bulunamadı`);
      }
      throw new Error('Proje detayları getirilirken bir hata oluştu');
    }
  },
  
  // Aktif raporu getir
  getActiveReport: async (projectName) => {
    if (!projectName) {
      console.error('projectService.getActiveReport: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }
    
    try {
      console.log(`projectService.getActiveReport: ${projectName} projesinin aktif raporu getiriliyor`);
      const response = await axiosInstance.get(`/project/${encodeURIComponent(projectName)}/report/active`);
      return response.data;
    } catch (error) {
      console.error('Aktif rapor getirme hatası:', error);
      return null; // Aktif rapor yoksa null döndür
    }
  },
  
  // Tamamlanmamış raporları getir
  getUnfinalizedReports: async (projectName) => {
    if (!projectName) {
      console.error('projectService.getUnfinalizedReports: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }
    
    try {
      console.log(`projectService.getUnfinalizedReports: ${projectName} projesinin tamamlanmamış raporları getiriliyor`);
      const response = await axiosInstance.get(`/project/${encodeURIComponent(projectName)}/unfinalized-reports`);
      return response.data.reports || [];
    } catch (error) {
      console.error('Tamamlanmamış raporlar getirme hatası:', error);
      return []; // Hata durumunda boş array döndür
    }
  },
  
  // Yeni rapor oluştur
  createReport: async (projectName) => {
    if (!projectName) {
      console.error('projectService.createReport: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }
    
    try {
      console.log(`projectService.createReport: ${projectName} projesi için yeni rapor oluşturuluyor`);
      const response = await axiosInstance.post('/project/create-report', {
        project_name: projectName
      });
      return response.data;
    } catch (error) {
      console.error('Rapor oluşturma hatası:', error);
      if (error.response && error.response.status === 409) {
        throw new Error('Aktif bir raporunuz bulunuyor. Lütfen mevcut raporu tamamlayın veya silin.');
      }
      throw new Error('Rapor oluşturulurken bir hata oluştu');
    }
  },
  
  // Projeyi sil
  deleteProject: async (projectName) => {
    if (!projectName) {
      console.error('projectService.deleteProject: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }
    
    try {
      console.log(`projectService.deleteProject: ${projectName} projesi siliniyor`);
      const response = await axiosInstance.post('/project/delete', {
        project_name: projectName
      });
      return response.data;
    } catch (error) {
      console.error('Proje silme hatası:', error);
      if (error.response && error.response.status === 404) {
        throw new Error(`"${projectName}" projesi bulunamadı`);
      }
      throw new Error('Proje silinirken bir hata oluştu');
    }
  },
  
  // Projeyi arşivle
  archiveProject: async (projectName) => {
    if (!projectName) {
      console.error('projectService.archiveProject: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }
    
    try {
      console.log(`projectService.archiveProject: ${projectName} projesi arşivleniyor`);
      const response = await axiosInstance.post('/project/archive', {
        project_name: projectName
      });
      return response.data;
    } catch (error) {
      console.error('Proje arşivleme hatası:', error);
      if (error.response && error.response.status === 404) {
        throw new Error(`"${projectName}" projesi bulunamadı`);
      }
      throw new Error('Proje arşivlenirken bir hata oluştu');
    }
  }
};

// Bileşen servisi
export const componentService = {
  // Tüm bileşenleri getir
  getComponents: async () => {
    try {
      console.log('componentService.getComponents: Tüm bileşenler getiriliyor');
      const response = await axiosInstance.get('/components');
      if (response.data && response.data.components) {
        return response.data.components;
      }
      return response.data;
    } catch (error) {
      console.error('Bileşenler getirme hatası:', error);
      throw new Error('Bileşenler getirilirken bir hata oluştu');
    }
  },
  
  // Bileşen sorularını getir
  getQuestions: async (componentName) => {
    if (!componentName) {
      console.error('componentService.getQuestions: Bileşen adı belirtilmedi');
      throw new Error('Bileşen adı belirtilmedi');
    }
    
    try {
      console.log(`componentService.getQuestions: ${componentName} bileşeni soruları getiriliyor`);
      // Backend'in döndüğü yanıt formatına dikkat et:
      // response.data yapısı { questions: [...] } şeklinde
      const response = await axiosInstance.get(`/component/${encodeURIComponent(componentName)}/questions`);
      
      // Response içinde questions array kontrolü
      if (response.data && Array.isArray(response.data.questions)) {
        console.log(`${componentName} soruları başarıyla yüklendi:`, response.data.questions);
        return response.data.questions;
      } 
      // API doğrudan bir array dönerse
      else if (Array.isArray(response.data)) {
        console.log(`${componentName} soruları başarıyla yüklendi (array olarak):`, response.data);
        return response.data;
      }
      // Beklenmeyen bir format ise boş array dön
      else {
        console.warn(`${componentName} soruları beklenmeyen formatta:`, response.data);
        return [];
      }
    } catch (error) {
      console.error(`${componentName} soruları yüklenirken hata:`, error);
      if (error.response) {
        console.error('API yanıtı:', error.response.data);
        console.error('Status kodu:', error.response.status);
      }
      throw new Error('Sorular getirilirken bir hata oluştu');
    }
  },
  
  // Bileşen cevaplarını kaydet
  saveComponentData: async (projectName, componentName, answers) => {
    if (!projectName) {
      console.error('componentService.saveComponentData: Proje adı belirtilmedi');
      throw new Error('Proje adı belirtilmedi');
    }
    
    if (!componentName) {
      console.error('componentService.saveComponentData: Bileşen adı belirtilmedi');
      throw new Error('Bileşen adı belirtilmedi');
    }
    
    try {
      console.log(`componentService.saveComponentData: ${projectName} projesi ${componentName} bileşeni cevapları kaydediliyor`);
      console.log('Gönderilen cevaplar:', answers);
      
      const response = await axiosInstance.post('/component/save-data', {
        project_name: projectName,
        component_name: componentName,
        answers
      });
      
      console.log(`${componentName} bileşeni verileri başarıyla kaydedildi:`, response.data);
      return response.data;
    } catch (error) {
      console.error(`${componentName} bileşeni verileri kaydetme hatası:`, error);
      
      // API yanıtından daha detaylı hata mesajını al
      if (error.response) {
        console.error('API Yanıt Detayı:', error.response.data);
        console.error('Durum Kodu:', error.response.status);
        
        // HTTP durumuna göre özel hata mesajları
        if (error.response.status === 404) {
          if (error.response.data?.detail?.includes("Proje bulunamadı")) {
            throw new Error(`Proje bulunamadı: ${projectName}. Proje mevcut değil veya silinmiş olabilir.`);
          }
          throw new Error(`Kaynak bulunamadı: ${error.response.data?.detail || 'Bilinmeyen 404 hatası'}`);
        }
        
        if (error.response.status === 400) {
          throw new Error(`Veri hatası: ${error.response.data?.detail || 'Bilinmeyen veri hatası'}`);
        }
        
        if (error.response.status === 500) {
          throw new Error(`Sunucu hatası: ${error.response.data?.detail || 'Bilinmeyen sunucu hatası'}. Lütfen daha sonra tekrar deneyin.`);
        }
        
        // Eğer backend'den gelen özel bir hata mesajı varsa kullan
        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
      }
      
      // Genel hata
      throw new Error(`${componentName} verileri kaydedilirken bir hata oluştu. Lütfen tekrar deneyin.`);
    }
  }
};

// Mail servisleri
export const mailService = {
  sendEmailRequest: async (componentName, projectName) => {
    try {
      const response = await axiosInstance.post('/send-email', {
        component_name: componentName,
        project_name: projectName,
      });
      return response.data;
    } catch (error) {
      console.error('E-posta gönderme hatası:', error);
      throw new Error('Mail gönderilirken bir hata oluştu');
    }
  },
};

export { axiosInstance };

export default {
  projectService,
  componentService,
  mailService
}; 