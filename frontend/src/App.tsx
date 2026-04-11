import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import HomePage from './pages/HomePage';
import ResultsPage from './pages/ResultsPage';
import DashboardPage from './pages/DashboardPage';
import type { AnalyzeResponse, LifestyleInput } from './types';

function App() {
  const [analysisData, setAnalysisData] = useState<AnalyzeResponse | null>(null);
  const [lifestyle, setLifestyle] = useState<LifestyleInput>({
    skin_type: 'combination',
    sleep_quality: 3,
    diet_quality: 3,
    stress_level: 3,
    climate_zone: 'tropical',
  });

  const handleAnalysisComplete = (data: AnalyzeResponse, lifestyleInput: LifestyleInput) => {
    setAnalysisData(data);
    setLifestyle(lifestyleInput);
  };

  return (
    <BrowserRouter>
      <Header />
      <Routes>
        <Route
          path="/"
          element={<HomePage onAnalysisComplete={handleAnalysisComplete} />}
        />
        <Route
          path="/results"
          element={<ResultsPage analysisData={analysisData} lifestyle={lifestyle} />}
        />
        <Route
          path="/dashboard"
          element={<DashboardPage />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
