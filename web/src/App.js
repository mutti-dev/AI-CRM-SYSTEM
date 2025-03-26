import React from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import Queries from './components/Queries';
import DetailsScreen from './components/DetailsScreen';
import Dashboard from './components/Dashboard';
import Tasks from './components/Tasks';
import Settings from './components/Settings';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <Router>
      <div className="App">
        <div className="App-container">
          <Sidebar />
          <main className="App-main">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/queries" element={<Queries />} />
              <Route path="/tasks" element={<Tasks />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/details/:id" element={<DetailsScreen />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;