import React from 'react';
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

function App() {
  const location = useLocation();

  return (
    <div className="App">
      <div className="App-container">
        {/* Show Sidebar only if not on DetailsScreen */}
        {location.pathname.startsWith('/details') ? <Sidebar2 /> : <Sidebar />}
        <main className="App-main">
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