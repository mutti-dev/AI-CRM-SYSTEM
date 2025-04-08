import React, { useEffect, useState } from 'react';
import '../styles/Tasks.css';
import config from '../config/config';

const Tasks = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const response = await fetch(`${config.API_URL}/api/tasks-with-email-history/`);
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
        tasks.map((task) => (
          <div key={task.id} className="task-card">
            <h3>{task.title}</h3>
            <p><strong>Description:</strong> {task.description}</p>
            <p><strong>Status:</strong> {task.status}</p>
            <p><strong>Due Date:</strong> {task.due_date || 'N/A'}</p>
            <p><strong>Assigned Agent:</strong> {task.assigned_agent || 'N/A'}</p>
            <p><strong>Assigned Team:</strong> {task.assigned_team || 'N/A'}</p>
            <h4>Email Query</h4>
            <p><strong>Subject:</strong> {task.email_query.subject}</p>
            <p><strong>Content:</strong> {task.email_query.content}</p>
            <p><strong>Customer Email:</strong> {task.email_query.customer_email}</p>
            <p><strong>Received At:</strong> {task.email_query.received_at}</p>
            <h4>Email History</h4>
            {task.email_history.length === 0 ? (
              <p>No email history available.</p>
            ) : (
              <ul>
                {task.email_history.map((email) => (
                  <li key={email.id}>
                    <p><strong>Responder:</strong> {email.responder__user__first_name} {email.responder__user__last_name}</p>
                    <p><strong>Content:</strong> {email.content}</p>
                    <p><strong>Sent At:</strong> {email.sent_at}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))
      )}
    </div>
  );
};

export default Tasks;