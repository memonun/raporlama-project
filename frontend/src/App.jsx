import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ProjectSelection from './pages/ProjectSelection';
import ProjectDetail from './pages/ProjectDetail';
import ReportBuilder from './pages/ReportBuilder';
import FinalReport from './pages/FinalReport';
import NewReport from './pages/NewReport';
import { ToastProvider } from './context/ToastContext';

function App() {
  return (
    <Router>
      <ToastProvider>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            <Route path="/" element={<ProjectSelection />} />
            <Route path="/project/:projectName" element={<ProjectDetail />} />
            <Route path="/project/:projectName/report/create" element={<ReportBuilder />} />
            <Route path="/project/:projectName/report/view" element={<FinalReport />} />
            <Route path="/new-report" element={<NewReport />} />
            <Route path="/new-report/:projectName" element={<NewReport />} />
          </Routes>
        </div>
      </ToastProvider>
    </Router>
  );
}

export default App; 