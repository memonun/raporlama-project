/**
 * Tarih formatlama ve diğer tarih işlemleri için yardımcı fonksiyonlar
 */

/**
 * Tarih string'ini yerelleştirilmiş format ile formatlar.
 * Örnek: 2023-12-31 -> 31.12.2023
 * ISO formatındaki string'i (2023-12-31T14:30:00.000Z) daha okunabilir hale getirir
 *
 * @param {string} dateString - Formatlanacak tarih string'i
 * @param {boolean} includeTime - Saat bilgisini de dahil et
 * @returns {string} Formatlanmış tarih
 */
export const formatDate = (dateString, includeTime = false) => {
  if (!dateString) return '-';
  
  try {
    const date = new Date(dateString);
    
    // Geçersiz tarih kontrolü
    if (isNaN(date.getTime())) {
      return dateString;
    }
    
    const options = {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    };
    
    if (includeTime) {
      options.hour = '2-digit';
      options.minute = '2-digit';
    }
    
    return date.toLocaleDateString('tr-TR', options);
  } catch (error) {
    console.error('Tarih formatlama hatası:', error);
    return dateString;
  }
};

/**
 * Tarih oluştur ve formatla (Bugünden kaç gün önce/sonra)
 *
 * @param {number} daysDiff - Bugünden farkı (gün olarak)
 * @returns {string} YYYY-MM-DD formatında tarih
 */
export const createDateString = (daysDiff = 0) => {
  const date = new Date();
  date.setDate(date.getDate() + daysDiff);
  
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  
  return `${year}-${month}-${day}`;
};

/**
 * İki tarih arasındaki farkı hesaplar (gün olarak)
 *
 * @param {string|Date} date1 - Karşılaştırılacak ilk tarih
 * @param {string|Date} date2 - Karşılaştırılacak ikinci tarih
 * @returns {number} İki tarih arasındaki fark (gün)
 */
export const daysBetween = (date1, date2) => {
  const d1 = date1 instanceof Date ? date1 : new Date(date1);
  const d2 = date2 instanceof Date ? date2 : new Date(date2);
  
  // Saat, dakika ve saniye bilgilerini sıfırla
  d1.setHours(0, 0, 0, 0);
  d2.setHours(0, 0, 0, 0);
  
  // Farkı hesapla
  const diffTime = Math.abs(d2 - d1);
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  return diffDays;
}; 