import React, { useEffect, useState } from 'react';
import '../styles/Tasks.css';
import config from '../config/config';
import Sidebar from './Sidebar';

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
            {task.email_query ? (
              <>
                <h4>Email Query</h4>
                <p><strong>Subject:</strong> {task.email_query.subject}</p>
                <p><strong>Content:</strong> {task.email_query.content}</p>
                <p><strong>Customer Email:</strong> {task.email_query.customer_email}</p>
                <p><strong>Received At:</strong> {task.email_query.received_at}</p>
              </>
            ) : (
              <p><strong>Email Query:</strong> N/A</p>
            )}
            {task.email_history && task.email_history.length > 0 ? (
              <>
                <h4>Email History</h4>
                <ul>
                  {task.email_history.map((email) => (
                    <li key={email.id}>
                      <p><strong>Responder:</strong> {email.responder__user__first_name} {email.responder__user__last_name}</p>
                      <p><strong>Content:</strong> {email.content}</p>
                      <p><strong>Sent At:</strong> {email.sent_at}</p>
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              <p>No email history available.</p>
            )}
            {task.whatsapp_query ? (
              <>
                <h4>WhatsApp Query</h4>
                <p><strong>Content:</strong> {task.whatsapp_query.content}</p>
                <p><strong>Customer Name:</strong> {task.whatsapp_query.customer_name}</p>
                <p><strong>Customer Phone:</strong> {task.whatsapp_query.customer_phone}</p>
                <p><strong>Received At:</strong> {task.whatsapp_query.received_at}</p>
              </>
            ) : (
              <p><strong>WhatsApp Query:</strong> N/A</p>
            )}
            {task.whatsapp_history && task.whatsapp_history.length > 0 ? (
              <>
                <h4>WhatsApp History</h4>
                <ul>
                  {task.whatsapp_history.map((whatsapp) => (
                    <li key={whatsapp.id}>
                      <p><strong>Content:</strong> {whatsapp.content}</p>
                      <p><strong>Sent At:</strong> {whatsapp.sent_at}</p>
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              <p>No WhatsApp history available.</p>
            )}
          </div>
        ))
      )}
    </div>
  );
};

export default Tasks;