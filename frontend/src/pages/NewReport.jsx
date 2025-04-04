import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { projectService } from '../services/api';
import Layout from '../components/Layout';
import Card from '../components/Card';
import Button from '../components/Button';
import { useToast } from '../context/ToastContext';

const NewReport = () => {
  const { projectName } = useParams();
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(projectName || '');
  const [reportDate, setReportDate] = useState('');
  const [reportDescription, setReportDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const toast = useToast();

  // Bugünün tarihini YYYY-MM-DD formatında al
  const today = new Date().toISOString().split('T')[0];

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        setLoadingProjects(true);
        // Varsayılan projeleri getir
        const projectsList = await projectService.getDefaultProjects();
        setProjects(projectsList);
        
        // URL'den bir proje adı geldiyse onu seç
        if (projectName && !selectedProject) {
          setSelectedProject(projectName);
        }
      } catch (err) {
        setError('Projeler yüklenirken bir hata oluştu: ' + err.message);
        toast.error(`Projeler yüklenirken hata oluştu: ${err.message}`);
      } finally {
        setLoadingProjects(false);
      }
    };

    fetchProjects();
  }, [projectName, selectedProject, toast]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!selectedProject) {
      setError('Lütfen bir proje seçin');
      toast.error('Lütfen bir proje seçin');
      return;
    }
    
    if (!reportDate) {
      setError('Lütfen rapor tarihi girin');
      toast.error('Lütfen rapor tarihi girin');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      await projectService.createReport(
        selectedProject,
        reportDate,
        reportDescription
      );
      
      toast.success('Rapor başarıyla oluşturuldu!');
      
      // Başarılı oluşturma durumunda rapor oluşturma sayfasına yönlendir
      navigate(`/report/${encodeURIComponent(selectedProject)}/${encodeURIComponent(reportDate)}`);
    } catch (err) {
      setError(err.message);
      toast.error(`Rapor oluşturulurken hata oluştu: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="flex justify-center">
        <Card className="w-full max-w-2xl">
          <h1 className="text-3xl font-bold text-gray-900 mb-6 text-center">
            Yeni Rapor Oluştur
          </h1>
          
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label htmlFor="projectSelect" className="block text-gray-700 font-medium mb-2">
                Proje *
              </label>
              <select
                id="projectSelect"
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loadingProjects || !!projectName}
                required
              >
                <option value="">Proje Seçin</option>
                {projects.map((project) => (
                  <option key={project} value={project}>
                    {project}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="mb-4">
              <label htmlFor="reportDate" className="block text-gray-700 font-medium mb-2">
                Rapor Tarihi *
              </label>
              <input
                type="date"
                id="reportDate"
                value={reportDate}
                onChange={(e) => setReportDate(e.target.value)}
                max={today}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
              <p className="text-sm text-gray-500 mt-1">
                Raporunuz "{selectedProject}_{reportDate}" formatında saklanacaktır.
              </p>
            </div>
            
            <div className="mb-6">
              <label htmlFor="reportDescription" className="block text-gray-700 font-medium mb-2">
                Rapor Açıklaması (İsteğe Bağlı)
              </label>
              <textarea
                id="reportDescription"
                value={reportDescription}
                onChange={(e) => setReportDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Bu rapor hakkında kısa bir açıklama yazın"
                rows={4}
              />
            </div>
            
            <div className="flex justify-end space-x-3">
              <Button
                type="button"
                onClick={() => navigate(projectName ? `/project/${encodeURIComponent(projectName)}` : '/')}
                className="bg-gray-200 hover:bg-gray-300 text-gray-800"
              >
                İptal
              </Button>
              
              <Button
                type="submit"
                disabled={loading || !selectedProject || !reportDate}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {loading ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    İşleniyor...
                  </span>
                ) : 'Rapor Oluştur'}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </Layout>
  );
};

export default NewReport; 