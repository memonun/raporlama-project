import { createContext, useContext, useState, useCallback } from 'react';
import Toast from '../components/Toast';

// Toast Context oluşturma
const ToastContext = createContext(null);

// Benzersiz ID oluşturma fonksiyonu
const generateUniqueId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

/**
 * Toast Provider Component
 * @param {Object} props - Component props 
 * @returns {React.ReactNode}
 */
export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  // Success Toast gösterme
  const showSuccess = useCallback((message, title = 'Başarılı!', duration = 3000) => {
    const id = generateUniqueId();
    setToasts(prev => [...prev, { id, type: 'success', message, title, duration }]);
    return id;
  }, []);

  // Error Toast gösterme
  const showError = useCallback((message, title = 'Hata!', duration = 5000) => {
    const id = generateUniqueId();
    setToasts(prev => [...prev, { id, type: 'error', message, title, duration }]);
    return id;
  }, []);

  // Warning Toast gösterme
  const showWarning = useCallback((message, title = 'Uyarı!', duration = 4000) => {
    const id = generateUniqueId();
    setToasts(prev => [...prev, { id, type: 'warning', message, title, duration }]);
    return id;
  }, []);

  // Info Toast gösterme
  const showInfo = useCallback((message, title = 'Bilgi', duration = 3000) => {
    const id = generateUniqueId();
    setToasts(prev => [...prev, { id, type: 'info', message, title, duration }]);
    return id;
  }, []);

  // Toast kapatma
  const closeToast = useCallback((id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  // Context değerleri
  const value = {
    // Orijinal metot isimleri
    showSuccess, 
    showError, 
    showWarning, 
    showInfo, 
    closeToast,
    
    // Kısa metot isimleri (aynı işlevlere alias olarak)
    success: showSuccess,
    error: showError,
    warning: showWarning,
    info: showInfo
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map(toast => (
          <Toast
            key={toast.id}
            type={toast.type}
            message={toast.message}
            title={toast.title}
            duration={toast.duration}
            onClose={() => closeToast(toast.id)}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
};

/**
 * Toast Context'e erişim için hook
 * @returns {Object} Toast fonksiyonları
 */
export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast hook, ToastProvider içinde kullanılmalıdır');
  }
  
  return context;
};

// API hata yakalama yardımcı fonksiyonu
export const handleApiError = (error, toast) => {
  console.error('API Hatası:', error);
  
  if (!toast) return;
  
  if (error.response) {
    // Backend'den gelen hata
    const statusCode = error.response.status;
    const errorMessage = error.response.data?.detail || error.message;
    
    switch (statusCode) {
      case 400:
        toast.error(`Geçersiz istek: ${errorMessage}`);
        break;
      case 401:
        toast.error('Oturum süresi dolmuş olabilir, lütfen tekrar giriş yapın');
        break;
      case 403:
        toast.error('Bu işlem için yetkiniz bulunmuyor');
        break;
      case 404:
        toast.error(`Kaynak bulunamadı: ${errorMessage}`);
        break;
      case 409:
        toast.warning(`Çakışma: ${errorMessage}`);
        break;
      case 422:
        toast.error(`Doğrulama hatası: ${errorMessage}`);
        break;
      case 500:
        toast.error('Sunucu hatası oluştu, lütfen daha sonra tekrar deneyin');
        break;
      default:
        toast.error(`İşlem başarısız: ${errorMessage}`);
    }
  } else if (error.request) {
    // İstek yapıldı ama cevap alınamadı
    toast.error('Sunucuya ulaşılamıyor, internet bağlantınızı kontrol edin');
  } else {
    // İstek oluşturulurken bir hata oluştu
    toast.error(`İstek oluşturulamadı: ${error.message}`);
  }
}; 