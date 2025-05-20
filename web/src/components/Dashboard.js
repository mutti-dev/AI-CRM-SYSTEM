import React, { useEffect, useState } from 'react';
import '../styles/Dashboard.css';
import config from '../config/config';
import UploadDataset from './UploadDataset';

const Dashboard = () => {
  const [data, setData] = useState({
    queries: 0,
    replied_queries: 0,
    complex_queries: 0,
    tasks: 0,
    logs: 0,
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${config.API_URL}/api/dashboard-data/`);
        if (!response.ok) {
          throw new Error('Failed to fetch dashboard data');
        }
        const result = await response.json();
        setData(result);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="dashboard">Loading...</div>;
  }

  return (
    <div className="dashboard">
      <h2>Dashboard Overview</h2>
      <div className="dashboard-cards">
        <div className="dashboard-card">
          <h3>Total Queries</h3>
          <p>{data.queries}</p>
        </div>
        <div className="dashboard-card">
          <h3>Replied Queries</h3>
          <p>{data.replied_queries}</p>
        </div>
        <div className="dashboard-card">
          <h3>Complex Queries</h3>
          <p>{data.complex_queries}</p>
        </div>
        <div className="dashboard-card">
          <h3>Total Tasks</h3>
          <p>{data.tasks}</p>
        </div>
        <div className="dashboard-card">
          <h3>Total Logs</h3>
          <p>{data.logs}</p>
        </div>
      </div>
      <div className="upload-dataset-section">
        <h3>Upload Fine-Tuned Dataset</h3>
        <UploadDataset />
      </div>
    </div>
  );
};

export default Dashboard;