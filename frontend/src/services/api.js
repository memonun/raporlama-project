import axios from "axios";


// Development mode için API URL'ini düzenle
const API_BASE_URL = "http://localhost:8000";

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Proje servisi
export const projectService = {
  // Tüm projeleri getir
  getProjects: async () => {
    try {
      console.log("projectService.getProjects: Tüm projeler getiriliyor");
      const response = await axiosInstance.get("/projects");
      return response.data;
    } catch (error) {
      console.error("Projeler getirme hatası:", error);
      throw new Error("Projeler getirilirken bir hata oluştu");
    }
  },

  // Proje detaylarını getir
  getProjectDetails: async (projectName) => {
    if (!projectName) {
      console.error("projectService.getProjectDetails: Proje adı belirtilmedi");
      throw new Error("Proje adı belirtilmedi");
    }

    try {
      console.log(
        `projectService.getProjectDetails: ${projectName} projesi detayları getiriliyor`
      );
      const response = await axiosInstance.get(
        `/project/${encodeURIComponent(projectName)}`
      );
      return response.data;
    } catch (error) {
      console.error("Proje detayları getirme hatası:", error);
      if (error.response && error.response.status === 404) {
        throw new Error(`"${projectName}" projesi bulunamadı`);
      }
      throw new Error("Proje detayları getirilirken bir hata oluştu");
    }
  },

  // Projeyi sil
  deleteProject: async (projectName) => {
    if (!projectName) {
      console.error("projectService.deleteProject: Proje adı belirtilmedi");
      throw new Error("Proje adı belirtilmedi");
    }

    try {
      console.log(
        `projectService.deleteProject: ${projectName} projesi siliniyor`
      );
      const response = await axiosInstance.post("/project/delete", {
        project_name: projectName,
      });
      return response.data;
    } catch (error) {
      console.error("Proje silme hatası:", error);
      if (error.response && error.response.status === 404) {
        throw new Error(`"${projectName}" projesi bulunamadı`);
      }
      throw new Error("Proje silinirken bir hata oluştu");
    }
  },

  // Projeyi arşivle
  archiveProject: async (projectName) => {
    if (!projectName) {
      console.error("projectService.archiveProject: Proje adı belirtilmedi");
      throw new Error("Proje adı belirtilmedi");
    }

    try {
      console.log(
        `projectService.archiveProject: ${projectName} projesi arşivleniyor`
      );
      const response = await axiosInstance.post("/project/archive", {
        project_name: projectName,
      });
      return response.data;
    } catch (error) {
      console.error("Proje arşivleme hatası:", error);
      if (error.response && error.response.status === 404) {
        throw new Error(`"${projectName}" projesi bulunamadı`);
      }
      throw new Error("Proje arşivlenirken bir hata oluştu");
    }
  },

  // Aktif raporu getir
  getActiveReport: async (projectName) => {
    if (!projectName) {
      console.error("projectService.getActiveReport: Proje adı belirtilmedi");
      throw new Error("Proje adı belirtilmedi");
    }

    try {
      console.log(
        `projectService.getActiveReport: ${projectName} projesi için aktif rapor getiriliyor`
      );

      const response = await axiosInstance.get(
        `/project/${projectName}/report/active`
      );

      // Eğer aktif rapor varsa ve finalized değilse döndür
      if (response.data && !response.data.is_finalized) {
        console.log("Aktif rapor getirme başarılı:", response.data);
        return response.data;
      } else if (response.data && response.data.is_finalized) {
        console.log(
          "Aktif rapor finalized olduğu için null dönülüyor:",
          response.data
        );
        return null;
      }

      console.log("Aktif rapor getirme başarılı:", response.data);
      return response.data;
    } catch (error) {
      console.error("Aktif rapor getirme hatası:", error);

      if (error.response) {
        console.error("API Yanıt Detayı:", error.response.data);
        console.error("Durum Kodu:", error.response.status);

        // 404 hatası rapor bulunamadığında normaldir
        if (error.response.status === 404) {
          return null;
        }

        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
      }

      throw new Error("Aktif rapor getirilirken bir hata oluştu");
    }
  },
};

// Bileşen servisi
export const componentService = {
  // Tüm bileşenleri getir
  getComponents: async () => {
    try {
      console.log("componentService.getComponents: Tüm bileşenler getiriliyor");
      const response = await axiosInstance.get("/components");
      if (response.data && response.data.components) {
        return response.data.components;
      }
      return response.data;
    } catch (error) {
      console.error("Bileşenler getirme hatası:", error);
      throw new Error("Bileşenler getirilirken bir hata oluştu");
    }
  },

  // Bileşen sorularını getir
  getQuestions: async (componentName) => {
    if (!componentName) {
      console.error("componentService.getQuestions: Bileşen adı belirtilmedi");
      throw new Error("Bileşen adı belirtilmedi");
    }

    try {
      console.log(
        `componentService.getQuestions: ${componentName} bileşeni soruları getiriliyor`
      );
      // Backend'in döndüğü yanıt formatına dikkat et:
      // response.data yapısı { questions: [...] } şeklinde
      const response = await axiosInstance.get(
        `/component/${encodeURIComponent(componentName)}/questions`
      );

      // Response içinde questions array kontrolü
      if (response.data && Array.isArray(response.data.questions)) {
        console.log(
          `${componentName} soruları başarıyla yüklendi:`,
          response.data.questions
        );
        return response.data.questions;
      }
      // API doğrudan bir array dönerse
      else if (Array.isArray(response.data)) {
        console.log(
          `${componentName} soruları başarıyla yüklendi (array olarak):`,
          response.data
        );
        return response.data;
      }
      // Beklenmeyen bir format ise boş array dön
      else {
        console.warn(
          `${componentName} soruları beklenmeyen formatta:`,
          response.data
        );
        return [];
      }
    } catch (error) {
      console.error(`${componentName} soruları yüklenirken hata:`, error);
      if (error.response) {
        console.error("API yanıtı:", error.response.data);
        console.error("Status kodu:", error.response.status);
      }
      throw new Error("Sorular getirilirken bir hata oluştu");
    }
  },

  // Bileşen cevaplarını kaydet
  saveComponentData: async (projectName, componentName, answers) => {
    if (!projectName) {
      console.error(
        "componentService.saveComponentData: Proje adı belirtilmedi"
      );
      throw new Error("Proje adı belirtilmedi");
    }

    if (!componentName) {
      console.error(
        "componentService.saveComponentData: Bileşen adı belirtilmedi"
      );
      throw new Error("Bileşen adı belirtilmedi");
    }

    try {
      console.log(
        `componentService.saveComponentData: ${projectName} projesi ${componentName} bileşeni cevapları kaydediliyor`
      );
      console.log("Gönderilen cevaplar:", answers);
      
      // Convert array values to JSON strings for backend compatibility
      const processedAnswers = {};
      Object.entries(answers).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          // Convert arrays to JSON strings
          processedAnswers[key] = JSON.stringify(value);
        } else if (typeof value === 'object' && value !== null) {
          // Convert objects to JSON strings
          processedAnswers[key] = JSON.stringify(value);
        } else {
          // Keep strings and primitives as-is
          processedAnswers[key] = value;
        }
      });
      
      // Send as JSON, not FormData
      const response = await axiosInstance.post("/component/save-data", {
        project_name: projectName,
        component_name: componentName,
        answers: processedAnswers
      });

      console.log(
        `${componentName} bileşeni verileri başarıyla kaydedildi:`,
        response.data
      );
      return response.data;
    } catch (error) {
      console.error(
        `${componentName} bileşeni verileri kaydetme hatası:`,
        error
      );

      // API yanıtından daha detaylı hata mesajını al
      if (error.response) {
        console.error("API Yanıt Detayı:", error.response.data);
        console.error("Durum Kodu:", error.response.status);

        // HTTP durumuna göre özel hata mesajları
        if (error.response.status === 404) {
          if (error.response.data?.detail?.includes("Proje bulunamadı")) {
            throw new Error(
              `Proje bulunamadı: ${projectName}. Proje mevcut değil veya silinmiş olabilir.`
            );
          }
          throw new Error(
            `Kaynak bulunamadı: ${
              error.response.data?.detail || "Bilinmeyen 404 hatası"
            }`
          );
        }

        if (error.response.status === 400) {
          throw new Error(
            `Veri hatası: ${
              error.response.data?.detail || "Bilinmeyen veri hatası"
            }`
          );
        }

        if (error.response.status === 500) {
          throw new Error(
            `Sunucu hatası: ${
              error.response.data?.detail || "Bilinmeyen sunucu hatası"
            }. Lütfen daha sonra tekrar deneyin.`
          );
        }

        // Eğer backend'den gelen özel bir hata mesajı varsa kullan
        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
      }

      // Genel hata
      throw new Error(
        `${componentName} verileri kaydedilirken bir hata oluştu. Lütfen tekrar deneyin.`
      );
    }
  },

  // Bileşen görseli yükle
  uploadComponentImage: async (
    projectName,
    componentName,
    imageFile,
    imageIndex = 0,
    questionId = null
  ) => {
    if (!projectName) {
      console.error(
        "componentService.uploadComponentImage: Proje adı belirtilmedi"
      );
      throw new Error("Proje adı belirtilmedi");
    }

    if (!componentName) {
      console.error(
        "componentService.uploadComponentImage: Bileşen adı belirtilmedi"
      );
      throw new Error("Bileşen adı belirtilmedi");
    }

    if (!imageFile || !(imageFile instanceof File)) {
      console.error(
        "componentService.uploadComponentImage: Geçerli bir görsel dosyası belirtilmedi"
      );
      throw new Error("Geçerli bir görsel dosyası belirtilmedi");
    }

    if (!questionId) {
      console.error(
        "componentService.uploadComponentImage: Soru ID belirtilmedi"
      );
      throw new Error("Soru ID belirtilmedi");
    }

    try {
      console.log(
        `componentService.uploadComponentImage: ${projectName} projesi ${componentName} bileşeni için görsel yükleniyor`
      );

      // FormData oluştur
      const formData = new FormData();
      formData.append("component_name", componentName);
      formData.append("image_index", imageIndex);
      formData.append("image", imageFile);
      formData.append("question_id", questionId);

      // API isteğini gönder
      const response = await axiosInstance.post(
        `/project/${encodeURIComponent(projectName)}/upload-component-image`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      console.log(
        `${componentName} bileşeni için görsel başarıyla yüklendi:`,
        response.data
      );
      return response.data;
    } catch (error) {
      console.error(`${componentName} bileşeni görseli yükleme hatası:`, error);

      // API yanıtından daha detaylı hata mesajını al
      if (error.response) {
        console.error("API Yanıt Detayı:", error.response.data);

        // Eğer backend'den gelen özel bir hata mesajı varsa kullan
        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
      }

      // Genel hata
      throw new Error(
        `${componentName} bileşeni için görsel yüklenirken bir hata oluştu`
      );
    }
  },

  // PDF dosyası yükle
  uploadPDF: async (projectName, componentName, pdfFile, questionId = null) => {
    if (!projectName) {
      console.error("componentService.uploadPDF: Proje adı belirtilmedi");
      throw new Error("Proje adı belirtilmedi");
    }

    if (!componentName) {
      console.error("componentService.uploadPDF: Bileşen adı belirtilmedi");
      throw new Error("Bileşen adı belirtilmedi");
    }

    if (!pdfFile || !(pdfFile instanceof File)) {
      console.error("componentService.uploadPDF: Geçerli bir PDF dosyası belirtilmedi");
      throw new Error("Geçerli bir PDF dosyası belirtilmedi");
    }

    if (!questionId) {
      console.error("componentService.uploadPDF: Soru ID belirtilmedi");
      throw new Error("Soru ID belirtilmedi");
    }

    try {
      console.log(`componentService.uploadPDF: ${projectName} projesi ${componentName} bileşeni için PDF yükleniyor`);

      // FormData oluştur
      const formData = new FormData();
      formData.append("component", componentName);
      formData.append("question_id", questionId);
      formData.append("file", pdfFile);

      // API isteğini gönder
      const response = await axiosInstance.post(
        `/project/${encodeURIComponent(projectName)}/upload-pdf`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      console.log(`${componentName} bileşeni için PDF başarıyla yüklendi:`, response.data);
      return response.data;
    } catch (error) {
      console.error(`${componentName} bileşeni PDF yükleme hatası:`, error);

      // API yanıtından daha detaylı hata mesajını al
      if (error.response) {
        console.error("API Yanıt Detayı:", error.response.data);

        // Eğer backend'den gelen özel bir hata mesajı varsa kullan
        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
      }

      // Genel hata
      throw new Error(`${componentName} bileşeni için PDF yüklenirken bir hata oluştu`);
    }
  },
};

// Mail servisleri
export const mailService = {
  sendEmailRequest: async (componentName, projectName) => {
    try {
      const response = await axiosInstance.post("/send-email", {
        component_name: componentName,
        project_name: projectName,
      });
      return response.data;
    } catch (error) {
      console.error("E-posta gönderme hatası:", error);
      throw new Error("Mail gönderilirken bir hata oluştu");
    }
  },

  sendReportByEmail: async (projectName, reportId, emailAddresses) => {
    try {
      // Replace any spaces with underscores in the project name
      const formattedProjectName = projectName.replace(/\s+/g, "_");

      const response = await axiosInstance.post(
        `/project/${formattedProjectName}/report/${reportId}/send-email`,
        {
          project_name: formattedProjectName,
          report_id: reportId,
          email_addresses: emailAddresses,
        }
      );
      return response.data;
    } catch (error) {
      console.error("Rapor e-posta gönderme hatası:", error);
      throw new Error("Rapor e-posta olarak gönderilirken bir hata oluştu");
    }
  },
};

// Rapor servisi
export const reportService = {
  // PDF İçeriğini Çıkarma
  extractPdf: async (formData, axiosOptions = {}) => {
    try {
      console.log("reportService.extractPdf: PDF içeriği çıkarılıyor");
      
      const response = await axiosInstance.post(
        "/extract-pdf",
        formData,
        {
          ...axiosOptions,
          headers: {
            ...axiosOptions.headers,
            "Content-Type": "multipart/form-data",
          },
        }
      );
      
      console.log("PDF içeriği başarıyla çıkarıldı:", response.data);
      return response;
    } catch (error) {
      console.error("PDF içeriği çıkarma hatası:", error);
      
      if (error.response) {
        console.error("API Yanıt Detayı:", error.response.data);
        console.error("Durum Kodu:", error.response.status);
        
        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
      }
      
      throw new Error("PDF içeriği çıkarılırken bir hata oluştu");
    }
  },

  // Add this simplified function to reportService in api.js

// Simplified report generation - only needs project name
generateReportSimplified: async (projectName) => {
  if (!projectName) {
    console.error("reportService.generateReportSimplified: Project name not provided");
    throw new Error("Project name is required");
  }

  try {
    console.log(`reportService.generateReportSimplified: Generating report for ${projectName}`);
    
    // Simple POST request with just the project name in the URL
    const response = await axiosInstance.post(
      `/project/${encodeURIComponent(projectName)}/generate-report`
    );

    console.log("Report generation response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Report generation error:", error);

    if (error.response) {
      console.error("API Response:", error.response.data);
      console.error("Status Code:", error.response.status);

      if (error.response.data && error.response.data.detail) {
        throw new Error(error.response.data.detail);
      }
      
      if (error.response.status === 404) {
        throw new Error("Project not found or PDFs missing");
      }
      
      if (error.response.status === 400) {
        throw new Error("No active report found for this project");
      }
    }

    throw new Error("Failed to generate report. Please try again.");
  }
},

  // Tamamlanmamış raporları getir
  getUnfinalizedReports: async (projectName) => {
    if (!projectName) {
      console.error(
        "reportService.getUnfinalizedReports: Proje adı belirtilmedi"
      );
      throw new Error("Proje adı belirtilmedi");
    }

    try {
      console.log(
        `reportService.getUnfinalizedReports: ${projectName} projesinin tamamlanmamış raporları getiriliyor`
      );
      const response = await axiosInstance.get(
        `/project/${encodeURIComponent(projectName)}/unfinalized-reports`
      );
      return response.data.reports || [];
    } catch (error) {
      console.error("Tamamlanmamış raporlar getirme hatası:", error);
      return []; // Hata durumunda boş array döndür
    }
  },

  // Yeni rapor oluştur (başlatır)
  createReport: async (projectName) => {
    if (!projectName) {
      console.error("reportService.createReport: Proje adı belirtilmedi");
      throw new Error("Proje adı belirtilmedi");
    }

    try {
      console.log(
        `reportService.createReport: ${projectName} projesi için yeni rapor başlatılıyor`
      );

      const requestData = {
        project_name: projectName,
      };

      console.log("Gönderilen veri:", requestData);

      const response = await axiosInstance.post(
        "/project/create-report",
        requestData,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      console.log("Rapor başlatma başarılı:", response.data);
      return response.data;
    } catch (error) {
      console.error("Rapor başlatma hatası:", error);

      if (error.response) {
        console.error("API Yanıt Detayı:", error.response.data);
        console.error("Durum Kodu:", error.response.status);

        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
        if (error.response.status === 409) {
          throw new Error(
            "Aktif bir raporunuz bulunuyor. Lütfen mevcut raporu tamamlayın veya silin."
          );
        }
      }

      throw new Error("Yeni rapor oluşturulurken bir hata oluştu");
    }
  },

  // Rapor indir
  downloadReport: async (projectName, reportId) => {
    if (!projectName) {
      console.error("reportService.downloadReport: Proje adı belirtilmedi");
      throw new Error("Proje adı belirtilmedi");
    }
    if (!reportId) {
      console.error("reportService.downloadReport: Rapor ID'si belirtilmedi");
      throw new Error("Rapor ID'si belirtilmedi");
    }

    try {
      console.log(
        `reportService.downloadReport: ${projectName} projesi için ${reportId} ID'li PDF indiriliyor`
      );

      const endpoint = `/project/${projectName}/report/${reportId}/download`;

      const response = await axiosInstance.get(endpoint, {
        responseType: "blob",
      });

      console.log("PDF indirme başarılı");
      return response.data;
    } catch (error) {
      console.error("PDF indirme hatası:", error);

      if (error.response) {
        console.error(
          "API Yanıt Detayı:",
          error.response.status,
          error.response.data
        );

        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
        if (error.response.status === 404) {
          throw new Error("Rapor veya PDF dosyası bulunamadı");
        } else if (error.response.status === 400) {
          throw new Error("Rapor henüz oluşturulmamış veya istek geçersiz");
        }
      }

      throw new Error(
        "Rapor indirilirken bir hata oluştu: " +
          (error.message || "Bilinmeyen hata")
      );
    }
  },



  
 // Update the deleteReport function to handle both active and finalized reports
  deleteReport: async (projectName, reportId = null) => {
    if (!projectName) {
      console.error("reportService.deleteReport: Proje adı belirtilmedi");
      throw new Error("Proje adı belirtilmedi");
    }

    try {
      let endpoint;
      
      // If reportId is provided, it's a specific report (finalized)
      // Otherwise, it's the active report
      if (reportId) {
        console.log(`reportService.deleteReport: ${projectName} projesi için ${reportId} ID'li rapor siliniyor`);
        // For finalized reports, you might need a different endpoint
        // For now, using the delete-finalized-report endpoint
        const response = await axiosInstance.post("/project/delete-finalized-report", {
          project_name: projectName,
          file_name: reportId // Using report_id as file_name
        });
        console.log("Rapor silme başarılı:", response.data);
        return response.data;
      } else {
        console.log(`reportService.deleteReport: ${projectName} projesi için aktif rapor siliniyor`);
        endpoint = `/project/${encodeURIComponent(projectName)}/delete-report`;
        const response = await axiosInstance.delete(endpoint);
        console.log("Aktif rapor silme başarılı:", response.data);
        return response.data;
      }
    } catch (error) {
      console.error("reportService.deleteReport - Detaylı Hata:", error);
      let errorMessage = "Rapor silinirken bir hata oluştu";

      if (error.response) {
        console.error("reportService.deleteReport - API Yanıt Detayı:", error.response.data);
        console.error("reportService.deleteReport - Durum Kodu:", error.response.status);

        if (error.response.data && error.response.data.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response.status === 404) {
          errorMessage = "Silinecek rapor veya proje bulunamadı.";
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      throw new Error(errorMessage);
    }
  },
  // Reset active report generation status and delete PDF
  resetActiveReport: async (projectName) => {
    if (!projectName) {
      console.error("reportService.resetActiveReport: Proje adı belirtilmedi");
      throw new Error("Proje adı belirtilmedi");
    }
    try {
      const response = await axiosInstance.post(
        `/project/${encodeURIComponent(projectName)}/reset-active-report`
      );
      console.log("Aktif rapor sıfırlama başarılı:", response.data);
      return response.data; // Should return { message: "...", active_report: {...} }
    } catch (error) {
      console.error("reportService.resetActiveReport - Hata:", error);
      let errorMessage = "Aktif rapor sıfırlanırken bir hata oluştu";
      if (error.response && error.response.data && error.response.data.detail) {
        errorMessage = error.response.data.detail;
      }
      throw new Error(errorMessage);
    }
  },

  // Raporu sonlandır
  finalizeReport: async (projectName) => {
    if (!projectName) {
      console.error("reportService.finalizeReport: Proje adı belirtilmedi");
      throw new Error("Proje adı belirtilmedi");
    }

    try {
      console.log(
        `reportService.finalizeReport: ${projectName} projesi raporu sonlandırılıyor`
      );

      const response = await axiosInstance.post("/project/finalize-report", {
        project_name: projectName,
      });

      return response.data;
    } catch (error) {
      console.error("Rapor sonlandırma hatası:", error);

      if (error.response) {
        console.error("API Yanıt Detayı:", error.response.data);
        console.error("Durum Kodu:", error.response.status);

        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
      }

      throw new Error("Rapor sonlandırılırken bir hata oluştu");
    }
  },

  // Sonlandırılmış raporları getir
  getFinalizedReports: async (projectName) => {
    if (!projectName) {
      console.error(
        "reportService.getFinalizedReports: Proje adı belirtilmedi"
      );
      throw new Error("Proje adı belirtilmedi");
    }

    try {
      console.log(
        `reportService.getFinalizedReports: ${projectName} projesi için sonlandırılmış raporlar getiriliyor`
      );

      const response = await axiosInstance.get(
        `/project/${projectName}/finalized-reports`
      );

      console.log(
        "Sonlandırılmış raporlar başarıyla getirildi:",
        response.data
      );
      return response.data;
    } catch (error) {
      console.error("Sonlandırılmış raporları getirme hatası:", error);

      if (error.response) {
        console.error("API Yanıt Detayı:", error.response.data);
        console.error("Durum Kodu:", error.response.status);

        if (error.response.status === 404) {
          return [];
        }

        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
      }

      throw new Error("Sonlandırılmış raporlar getirilirken bir hata oluştu");
    }
  },

  // Sonlandırılmış raporu sil
  deleteFinalizedReport: async (projectName, fileName) => {
    if (!projectName) {
      console.error(
        "reportService.deleteFinalizedReport: Proje adı belirtilmedi"
      );
      throw new Error("Proje adı belirtilmedi");
    }

    if (!fileName) {
      console.error(
        "reportService.deleteFinalizedReport: Dosya adı belirtilmedi"
      );
      throw new Error("Dosya adı belirtilmedi");
    }

    try {
      console.log(
        `reportService.deleteFinalizedReport: ${projectName} projesi için ${fileName} raporu siliniyor`
      );

      const response = await axiosInstance.post(
        "/project/delete-finalized-report",
        {
          project_name: projectName,
          file_name: fileName,
        }
      );

      console.log("Finalized rapor silme başarılı:", response.data);
      return response.data;
    } catch (error) {
      console.error("Finalized rapor silme hatası:", error);

      if (error.response) {
        console.error("API Yanıt Detayı:", error.response.data);
        console.error("Durum Kodu:", error.response.status);

        if (error.response.data && error.response.data.detail) {
          throw new Error(error.response.data.detail);
        } else if (error.response.status === 404) {
          throw new Error("Silinecek rapor veya proje bulunamadı.");
        }
      }

      throw new Error("Finalized rapor silinirken bir hata oluştu.");
    }
  },
};

export { axiosInstance };

export default {
  projectService,
  componentService,
  mailService,
  reportService,
};
