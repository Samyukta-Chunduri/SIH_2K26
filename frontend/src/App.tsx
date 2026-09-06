import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from './layouts/DashboardLayout';
import { OverviewPage } from './pages/OverviewPage';
import { QuantumPage } from './pages/QuantumPage';
import { ThreatsPage } from './pages/ThreatsPage';
import { FusionPage } from './pages/FusionPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { BenchmarkingPage } from './pages/BenchmarkingPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<OverviewPage />} />
          <Route path="quantum" element={<QuantumPage />} />
          <Route path="threats" element={<ThreatsPage />} />
          <Route path="fusion" element={<FusionPage />} />
          <Route path="evaluation" element={<EvaluationPage />} />
          <Route path="benchmarking" element={<BenchmarkingPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
