import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/navigation/Sidebar';
import { Navbar } from '../components/navigation/Navbar';

export const DashboardLayout: React.FC = () => {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleScenarioExecuted = () => {
    // Increment refresh key to trigger data re-fetch in active views
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content">
        <Navbar onScenarioExecuted={handleScenarioExecuted} />
        <main key={refreshKey} style={{ flex: 1 }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};
