import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectService, reportService } from '../services/api';
import { useToast } from '../context/ToastContext';

const FinalReport = () => {
  const { projectName } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        const reportData = await projectService.getActiveReport(projectName);
        setReport(reportData);
      } catch (error) {
        toast.error(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [projectName, toast]);

  const handleDownload = async () => {
    try {
      const pdfUrl = await reportService.downloadReport(projectName);
      window.open(pdfUrl, '_blank');
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Bu raporu silmek istediğinizden emin misiniz?')) {
      try {
        await reportService.deleteReport(projectName);
        toast.success('Rapor başarıyla silindi');
        navigate(`/project/${projectName}`);
      } catch (error) {
        toast.error(error.message);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600">Rapor bulunamadı</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Rapor Detayları</h1>
          <div className="flex space-x-4">
            <button
              onClick={handleDownload}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              PDF İndir
            </button>
            <button
              onClick={handleDelete}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              Raporu Sil
            </button>
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h2 className="text-lg font-semibold mb-2">Proje Bilgileri</h2>
            <p className="text-gray-600">Proje Adı: {projectName}</p>
            <p className="text-gray-600">Oluşturulma Tarihi: {new Date(report.created_at).toLocaleDateString()}</p>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <h2 className="text-lg font-semibold mb-2">Bileşenler</h2>
            {Object.entries(report.components || {}).map(([componentName, componentData]) => (
              <div key={componentName} className="mb-4">
                <h3 className="font-medium text-gray-800">{componentName}</h3>
                <div className="mt-2 space-y-2">
                  {Object.entries(componentData.answers || {}).map(([questionId, answer]) => (
                    <div key={questionId} className="text-sm">
                      <span className="font-medium text-gray-700">Soru {questionId}:</span>
                      <p className="text-gray-600">{answer}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FinalReport; 