import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import Card from '../components/Card';
import Button from '../components/Button';
import { toast } from 'react-hot-toast';
import { projectService, reportService, mailService } from '../services/api';
import { Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { FileText, Plus, FileCheck, Clock, Trash2, MoreVertical } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';

/**
 * Safely access nested object properties
 * @param {Object} obj - The object to traverse
 * @param {string|string[]} path - The path to the property, either as a dot-separated string or array
 * @param {*} defaultValue - The value to return if the path doesn't exist
 * @returns {*} The value at the path or the default value
 */
const getSafe = (obj, path, defaultValue = undefined) => {
  if (!obj) return defaultValue;
  
  try {
    const pathArray = Array.isArray(path) ? path : path.split('.');
    return pathArray.reduce((acc, key) => 
      acc && typeof acc === 'object' && acc[key] !== undefined 
        ? acc[key] 
        : defaultValue
    , obj);
  } catch (e) {
    console.warn(`Error accessing path ${path}:`, e);
    return defaultValue;
  }
};

const ProjectDetail = () => {
  const { projectName: rawProjectName } = useParams();
  const navigate = useNavigate();
  
  // Format project name to ensure consistency
  const projectName = rawProjectName.replace(/\s+/g, '_');
  
  // State for project and reports
  const [project, setProject] = useState(null);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [projectLoaded, setProjectLoaded] = useState(false);
  
  // State for PDF preview
  const [showPdfPreview, setShowPdfPreview] = useState(false);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [loadingPdf, setLoadingPdf] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  
  // State for info dialog
  const [showInfoDialog, setShowInfoDialog] = useState(false);
  const [infoDialogContent, setInfoDialogContent] = useState({ title: '', message: '', action: null });

  // State for custom dropdown menu visibility
  const [openMenuId, setOpenMenuId] = useState(null); 

  // State for email dialog
  const [showEmailDialog, setShowEmailDialog] = useState(false);
  const [emailAddresses, setEmailAddresses] = useState('');
  const [sendingEmail, setSendingEmail] = useState(false);
  const [selectedReportForEmail, setSelectedReportForEmail] = useState(null);

  // Load project and reports data
  useEffect(() => {
    const loadData = async () => {
      if (!projectName) return;
      
      try {
        setLoading(true);
        // Proje detaylarını getir
        const projectData = await projectService.getProjectDetails(projectName);
        
        setProject(projectData);
        
        // Raporları birleştir: active_report ve reports[] birlikte
        let allReports = [];
        
        // Eğer active_report varsa listeye ekle
        if (projectData.active_report) {
          allReports.push({
            ...projectData.active_report,
            menuId: uuidv4()
          });
        }
        
        // Eğer reports[] listesi varsa listeye ekle
        if (projectData.reports && Array.isArray(projectData.reports)) {
          allReports = [
            ...allReports,
            ...projectData.reports.map(report => ({
              ...report,
              menuId: uuidv4()
            }))
          ];
        }
        
        console.log('Birleştirilmiş raporlar:', allReports);
        
        // Tüm raporları state'e set et
        setReports(allReports);
        setProjectLoaded(true);
      } catch (error) {
        console.error('Proje verileri yüklenirken hata:', error);
        toast.error(error.message || 'Proje verileri yüklenirken bir hata oluştu');
        setReports([]);
        setProjectLoaded(false);
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, [projectName]);

 const handleCreateReport = async () => {
  try {
    setLoading(true);
    const activeReport = await projectService.getActiveReport(projectName);

    if (activeReport) {
      setInfoDialogContent({
        title: 'Aktif Rapor Mevcut',
        message: 'Zaten devam eden bir raporunuz var. Rapora yönlendirilmek için "Devam Et" butonuna tıklayın.',
        action: () => navigate(`/project/${projectName}/report/create`)
      });
      setShowInfoDialog(true);
    } else {
      const result = await reportService.createReport(projectName);
      setReports(prev => [...prev, { ...result, menuId: uuidv4() }]);
      navigate(`/project/${projectName}/report/create`);
    }
  } catch (error) {
    // ... error handling remains the same
  } finally {
    setLoading(false);
  }
};
  const handleReportClick = async (report) => {
    console.log('handleReportClick triggered for report:', report);
    setSelectedReport(report);
    
    if (report.is_finalized) { 
      console.log('Report is finalized, calling handlePreviewPdf...');
      handlePreviewPdf(report.report_id); // Use report_id directly
    } else {
      console.log('Report is NOT finalized, navigating to builder...');
      navigate(`/project/${projectName}/report/create`);
    }
  };

  const handlePreviewPdf = async (reportId) => {
    if (!projectName) {
      toast.error('Proje bilgisi bulunamadı');
      return;
    }
    if (!reportId) { 
      toast.error('Rapor ID bilgisi eksik');
      return;
    }

    try {
      setLoadingPdf(true);
      const blob = await reportService.downloadReport(projectName, reportId);
      
      if (!(blob instanceof Blob)) {
        throw new Error('PDF doğru formatta alınamadı');
      }
      
      const url = URL.createObjectURL(blob);
      setPdfUrl(url);
      setShowPdfPreview(true);
    } catch (error) {
      console.error('PDF önizleme hatası:', error);
      toast.error(error.message || 'PDF önizleme hatası oluştu');
    } finally {
      setLoadingPdf(false);
    }
  };

  const handleDeleteReport = async (reportId, event) => {
  if (event) {
    event.stopPropagation();
  }
  
  if (!window.confirm('Bu raporu silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.')) {
    return;
  }
  
  try {
    setLoading(true);
    
    // For active reports, we don't pass reportId
    // The backend knows to delete the active report
    await reportService.deleteReport(projectName);
    
    // Update state - remove reports that are not finalized
    setReports(prev => prev.filter(report => report.is_finalized));
    
    toast.success('Aktif rapor başarıyla silindi.', {
      duration: 3000
    });
    
  } catch (error) {
    console.error('handleDeleteReport - Detaylı Hata:', error);
    toast.error(error.message || 'Rapor silinirken bir hata oluştu. Lütfen tekrar deneyin.', {
      duration: 4000
    });
  } finally {
    setLoading(false);
  }
};
  const handleFinalizedReportDelete = async (report, event) => {
  if (event) {
    event.stopPropagation();
  }

  // Debug logging
  console.log('[DELETE] Report object:', report);
  console.log('[DELETE] Report keys:', Object.keys(report || {}));
  console.log('[DELETE] Report ID:', report?.report_id);
  console.log('[DELETE] Report name:', report?.name);
  console.log('[DELETE] Is finalized:', report?.is_finalized);

  const reportIdToDelete = report?.report_id || report?.id || report?.name;

  if (!reportIdToDelete) {
    console.error('[DELETE] No report identifier found:', report);
    toast.error("Silinecek rapor ID'si bulunamadı. Debug bilgisi konsola yazdırıldı.");
    return;
  }
  
  if (!window.confirm('Bu sonlandırılmış raporu silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.')) {
    return;
  }
  
  try {
    setLoading(true);
    console.log('[DELETE] Attempting to delete report:', {
      projectName,
      reportId: reportIdToDelete,
      report: report
    });
    
    await reportService.deleteFinalizedReport(projectName, reportIdToDelete); 
    
    // Update state - use multiple possible ID fields for filtering
    setReports(prev => prev.filter(r => 
      r.report_id !== reportIdToDelete && 
      r.id !== reportIdToDelete && 
      r.name !== reportIdToDelete
    ));
    
    toast.success('Sonlandırılmış rapor başarıyla silindi.', {
      duration: 3000
    });
    
    setOpenMenuId(null);
    
  } catch (error) {
    console.error('[DELETE] Detailed error:', error);
    console.error('[DELETE] Error response:', error.response?.data);
    
    let errorMessage = 'Sonlandırılmış rapor silinirken bir hata oluştu.';
    
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail;
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    toast.error(errorMessage, {
      duration: 4000
    });
    setOpenMenuId(null);
  } finally {
    setLoading(false);
  }
};

  // Function to toggle the custom dropdown menu
  const toggleMenu = (reportId, event) => {
    event.stopPropagation(); // Prevent the card click
    setOpenMenuId(prevId => (prevId === reportId ? null : reportId));
  };

  // Effect to close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      // If click is not on a menu trigger or inside a menu, close it
      if (openMenuId && !event.target.closest('.report-menu-trigger') && !event.target.closest('.report-menu-content')) {
        setOpenMenuId(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [openMenuId]);

  const handleSendEmail = async (e) => {
  e.preventDefault();
  
  if (!emailAddresses.trim()) {
    toast.error('Lütfen en az bir e-posta adresi girin');
    return;
  }

  const emails = emailAddresses.split(',').map(email => email.trim());
  
  const invalidEmails = emails.filter(email => !email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/));
  if (invalidEmails.length > 0) {
    toast.error(`Geçersiz e-posta adresleri: ${invalidEmails.join(', ')}`);
    return;
  }

  setSendingEmail(true);
  try {
    await mailService.sendReportByEmail(
      projectName,
      selectedReportForEmail.report_id, // Use report_id only
      emails
    );
    toast.success('Rapor başarıyla gönderildi');
    setShowEmailDialog(false);
    setEmailAddresses('');
    setSelectedReportForEmail(null);
  } catch (error) {
    toast.error(error.message);
  } finally {
    setSendingEmail(false);
  }
};

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </Layout>
    );
  }

  if (!projectLoaded || !project) {
    return (
      <Layout>
        <div className="text-center py-10">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Proje Bulunamadı</h2>
          <p className="text-gray-700 mb-4">Proje detayları yüklenirken bir sorun oluştu.</p>
          <Button onClick={() => navigate('/')}>Ana Sayfaya Dön</Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="container px-4 py-8 max-w-7xl mx-auto">
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">{projectName}</h1>
          <Button onClick={() => navigate('/')} variant="outline">
            Projeler Listesine Dön
          </Button>
        </div>

        <div className="max-w-7xl mx-auto">
          {/* Aktif Rapor Bölümü */}
          {reports.some(report => !report.is_finalized) && (
            <div className="mb-8 p-4 border border-blue-100 rounded-lg bg-blue-50">
              <h2 className="text-xl font-bold text-blue-700 mb-4">Aktif Raporunuz</h2>
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <Clock className="w-8 h-8 text-blue-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-800">
                      {reports.find(report => !report.is_finalized)?.name || 'Rapor'}
                    </p>
                    <span className="text-xs text-blue-600">Düzenlemeye devam et</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button 
                    onClick={() => navigate(`/project/${projectName}/report/create`)}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    Devam Et
                  </Button>
                  <Button 
                    onClick={(e) => {
                      const activeReport = reports.find(report => !report.is_finalized);
                      if (activeReport) handleDeleteReport(activeReport.report_id, e); // Don't pass report_id for active reports
                    }}
                    variant="outline"
                    className="text-red-500 border-red-200 hover:bg-red-50"
                  >
                    Sil
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Tamamlanmış Raporlar */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              {reports.some(report => !report.is_finalized) 
                ? 'Tamamlanmış Raporlar' 
                : 'Raporlar'}
            </h2>
            
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {/* Yeni Rapor Oluştur - aktif rapor yoksa göster */}
              {!reports.some(report => !report.is_finalized) && (
                <button
                  onClick={handleCreateReport}
                  className="group relative flex flex-col items-center justify-center p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-gray-400 transition-colors bg-white/50 hover:bg-white/80"
                >
                  <Plus className="w-12 h-12 text-gray-400 group-hover:text-gray-600 transition-colors" />
                  <span className="mt-2 text-sm font-medium text-gray-600 group-hover:text-gray-800 transition-colors">
                    Yeni Rapor Oluştur
                  </span>
                </button>
              )}

              {/* Finalized Raporlar Listesi */}
              {reports.filter(report => report.is_finalized).map((report) => {
                const reportId = report.report_id;
                const isMenuOpen = openMenuId === report.menuId;

                return (
                  <div
                    key={report.report_id || report.menuId}
                    onClick={() => handleReportClick(report)}
                    className="group relative flex flex-col p-6 rounded-lg shadow-sm hover:shadow-md transition-all cursor-pointer bg-white border border-gray-100"
                  >
                    {/* Custom 3-dot Menu */}
                    <div className="absolute top-3 right-3">
                      <button 
                        onClick={(e) => toggleMenu(report.menuId, e)}
                        className="report-menu-trigger p-1.5 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100 focus:outline-none transition-colors"
                        aria-haspopup="true"
                        aria-expanded={isMenuOpen}
                      >
                        <MoreVertical className="w-4 h-4" />
                      </button>
                      
                      {/* Custom Dropdown Content */}
                      {isMenuOpen && (
                        <div 
                          className="report-menu-content absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-10 py-1"
                          role="menu"
                          aria-orientation="vertical"
                          aria-labelledby={`menu-button-${report.menuId}`}
                        >
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedReportForEmail(report);
                              setShowEmailDialog(true);
                              setOpenMenuId(null);
                            }}
                            className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900 transition-colors"
                            role="menuitem"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                            </svg>
                            <span>Mail olarak gönder</span>
                          </button>
                          <button
                            onClick={(e) => handleFinalizedReportDelete(report, e)}
                            className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 hover:text-red-700 transition-colors"
                            role="menuitem"
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            <span>Raporu Sil</span>
                          </button>
                        </div>
                      )}
                    </div>
                    
                    {/* Rapor İkonu ve Bilgileri */}
                    <div className="flex flex-col items-center">
                      <div className="mb-4 p-2 rounded-full bg-green-50">
                        <FileCheck className="w-8 h-8 text-green-500 group-hover:text-green-600 transition-colors" />
                      </div>
                      
                      <div className="text-center mb-8">
                        <h3 className="text-sm font-medium text-gray-900 mb-1 break-words w-full">
                          {report.name || `Rapor ${reportId}`}
                        </h3>
                        <p className="text-xs text-gray-500">
                          {new Date(report.created_at || report.date).toLocaleDateString('tr-TR')}
                        </p>
                      </div>
                    </div>
                    
                    {/* Önizleme İndikatörü */}
                    <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
                      <span className="text-xs text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity flex items-center bg-white/80 px-2 py-1 rounded-full shadow-sm">
                        <FileText className="w-3 h-3 mr-1" />
                        Önizle
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* PDF Önizleme Modal */}
        <Dialog open={showPdfPreview} onOpenChange={setShowPdfPreview}>
          <DialogContent className="max-w-[90vw] h-[90vh]">
            <DialogHeader>
              <DialogTitle>PDF Önizleme</DialogTitle>
              <DialogDescription>
                {selectedReport?.name || 'Rapor'} önizlemesi
              </DialogDescription>
            </DialogHeader>
            
            <div className="flex flex-col w-full h-full min-h-[75vh] border border-gray-300 rounded-md overflow-hidden">
              {loadingPdf ? (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
                </div>
              ) : pdfUrl ? (
                <object 
                  data={pdfUrl} 
                  type="application/pdf"
                  className="flex-grow w-full h-full"
                  aria-label="PDF Viewer"
                >
                  <p className="p-4 text-center">Tarayıcınız PDF önizlemesini desteklemiyor.
                    <a href={pdfUrl} download className="text-blue-600 hover:underline ml-1">PDF'yi indirin</a>.
                  </p>
                </object>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <p>PDF yüklenirken bir hata oluştu</p>
                </div>
              )}
            </div>
            
            <DialogFooter className="flex justify-end gap-2 pt-4">
              {/* Add Download Button */} 
              {pdfUrl && (
                <a
                  href={pdfUrl} 
                  download={`${selectedReport?.name || selectedReport?.report_id || projectName}_report.pdf`}
                  className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
                >
                  İndir
                </a>
              )}
              <Button 
                variant="outline"
                onClick={() => {
                  if (pdfUrl) URL.revokeObjectURL(pdfUrl);
                  setPdfUrl(null);
                  setShowPdfPreview(false);
                  setSelectedReport(null);
                }}
              >
                Kapat
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Bilgilendirme Dialog'u */}
        <Dialog open={showInfoDialog} onOpenChange={setShowInfoDialog}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>{infoDialogContent.title}</DialogTitle>
              <DialogDescription>
                {infoDialogContent.message}
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="flex justify-end gap-2">
              {infoDialogContent.action && (
                <Button
                  onClick={() => {
                    infoDialogContent.action();
                    setShowInfoDialog(false);
                  }}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Devam Et
                </Button>
              )}
              <Button
                variant="outline"
                onClick={() => setShowInfoDialog(false)}
              >
                Kapat
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Email Dialog */}
        <Dialog open={showEmailDialog} onOpenChange={setShowEmailDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Raporu E-posta ile Gönder</DialogTitle>
              <DialogDescription>
                Raporun gönderileceği e-posta adreslerini virgülle ayırarak girin.
              </DialogDescription>
            </DialogHeader>
            
            <form onSubmit={handleSendEmail}>
              <div className="mt-4">
                <label htmlFor="emails" className="block text-sm font-medium text-gray-700 mb-1">
                  E-posta Adresleri
                </label>
                <input
                  type="text"
                  id="emails"
                  value={emailAddresses}
                  onChange={(e) => setEmailAddresses(e.target.value)}
                  placeholder="ornek@mail.com, ornek2@mail.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={sendingEmail}
                />
              </div>
              
              <DialogFooter className="mt-6">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowEmailDialog(false);
                    setEmailAddresses('');
                    setSelectedReportForEmail(null);
                  }}
                  disabled={sendingEmail}
                >
                  İptal
                </Button>
                <Button
                  type="submit"
                  disabled={sendingEmail}
                  className="bg-blue-600 text-white hover:bg-blue-700"
                >
                  {sendingEmail ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Gönderiliyor...
                    </>
                  ) : (
                    'Gönder'
                  )}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
};

export default ProjectDetail;