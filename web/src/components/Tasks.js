import React, { useEffect, useState } from 'react';
import '../styles/Tasks.css';
import config from '../config/config';

const Tasks = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const response = await fetch(`${config.API_URL}/api/assign-task/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({}), // Add any required payload here
        });
        if (!response.ok) {
          throw new Error('Failed to fetch tasks');
        }
        const result = await response.json();
        setTasks(result.tasks || []);
      } catch (error) {
        console.error('Error fetching tasks:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, []);

  if (loading) {
    return <div className="tasks">Loading...</div>;
  }

  return (
    <div className="tasks">
      <h2>Tasks</h2>
      {tasks.length === 0 ? (
        <p>No tasks available.</p>
      ) : (
        <ul>
          {tasks.map((task) => (
            <li key={task.id}>
              <strong>{task.title}</strong>: {task.description}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default Tasks;
