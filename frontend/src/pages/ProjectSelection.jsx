import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import Button from '../components/Button';

const ProjectSelection = () => {
  const navigate = useNavigate();

  // Proje butonuna tıklandığında ilgili proje detay sayfasına yönlendir
  const handleProjectSelect = (projectName) => {
    navigate(`/project/${encodeURIComponent(projectName)}`);
  };

  // Proje butonları için görsel tasarım stilleri
  const buttonClasses = "flex items-center justify-center h-48 rounded-lg shadow-lg text-white font-bold text-2xl transition-all duration-300 hover:shadow-xl hover:scale-105 cursor-pointer";

  return (
    <Layout>
      <div className="text-center mb-12">
        <h1 className="text-4xl font-extrabold text-gray-900 mb-4">
          Isra Holding Yatırımcı Raporu Sistemi
        </h1>
        <p className="text-xl text-gray-600 mb-6">
          Lütfen bir proje seçin
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
        {/* V Mall */}
        <div 
          className={`${buttonClasses} bg-gradient-to-r from-blue-600 to-blue-800`}
          onClick={() => handleProjectSelect("V Mall")}
        >
          <div className="flex flex-col items-center">
            <span className="text-3xl mb-2">🏬</span>
            <h2>V Mall</h2>
          </div>
        </div>

        {/* V Metroway */}
        <div 
          className={`${buttonClasses} bg-gradient-to-r from-green-600 to-green-800`}
          onClick={() => handleProjectSelect("V Metroway")}
        >
          <div className="flex flex-col items-center">
            <span className="text-3xl mb-2">🚆</span>
            <h2>V Metroway</h2>
          </div>
        </div>

        {/* V Statü */}
        <div 
          className={`${buttonClasses} bg-gradient-to-r from-purple-600 to-purple-800`}
          onClick={() => handleProjectSelect("V Statü")}
        >
          <div className="flex flex-col items-center">
            <span className="text-3xl mb-2">🏢</span>
            <h2>V Statü</h2>
          </div>
        </div>

        {/* V Yeşilada */}
        <div 
          className={`${buttonClasses} bg-gradient-to-r from-teal-600 to-teal-800`}
          onClick={() => handleProjectSelect("V Yeşilada")}
        >
          <div className="flex flex-col items-center">
            <span className="text-3xl mb-2">🌴</span>
            <h2>V Yeşilada</h2>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default ProjectSelection; 