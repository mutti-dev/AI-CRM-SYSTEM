import React, { useState } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import Sidebar2 from './components/Sidebar2';
import Queries from './components/Queries';
import DetailsScreen from './components/DetailsScreen';
import Dashboard from './components/Dashboard';
import Tasks from './components/Tasks';
import Settings from './components/Settings';
import UploadDataset from './components/UploadDataset';
import { Routes, Route, useLocation } from 'react-router-dom';
import TicketTabs from './components/TicketTabs';

function App() {
  const location = useLocation();
  const [isSidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="App">
      {/* <TicketTabs /> */}
      <div className="App-container">
        {location.pathname.startsWith('/details') ? (
          <Sidebar2 onToggle={setSidebarCollapsed} />
        ) : (
          <Sidebar onToggle={setSidebarCollapsed} />
        )}
        <main
          className={`App-main ${isSidebarCollapsed ? 'expanded' : ''}`}
        >
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/queries" element={<Queries />} />
            <Route path="/tasks" element={<Tasks />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/details/:id" element={<DetailsScreen />} />
            <Route path="/upload-dataset" element={<UploadDataset />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default App;