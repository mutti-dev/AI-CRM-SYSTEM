import React, { useState, useEffect } from 'react';
import '../styles/Sidebar2.css';
import config from '../config/config';

const Sidebar2 = ({ emailQueryId, onToggle }) => {
   const [collapsed, setCollapsed] = useState(false); // State to manage collapse
  const [agents, setAgents] = useState([]);
  const [teams, setTeams] = useState([]);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    assignedAgentId: '',
    assignedTeamId: '',
    dueDate: '',
  });
  const [taskMessage, setTaskMessage] = useState('');
  const [teamsMessage, setTeamsMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchAgentsAndTeams = async () => {
      try {
        const agentsResponse = await fetch(`${config.API_URL}/api/agents/`);
        const teamsResponse = await fetch(`${config.API_URL}/api/teams/`);
        if (!agentsResponse.ok || !teamsResponse.ok) {
          throw new Error('Failed to fetch agents or teams');
        }
        const agentsData = await agentsResponse.json();
        const teamsData = await teamsResponse.json();
        setAgents(agentsData.agents || []);
        setTeams(teamsData.teams || []);
      } catch (error) {
        console.error('Error fetching agents or teams:', error);
      }
    };
    

    const fetchTaskDetails = async () => {
      try {
        const response = await fetch(`${config.API_URL}/api/task-details/${emailQueryId}/`);
        if (!response.ok) {
          throw new Error('Failed to fetch task details');
        }
        const taskData = await response.json();
        if (taskData.status === 'success' && taskData.task) {
          setFormData({
            title: taskData.task.title || '',
            description: taskData.task.description || '',
            assignedAgentId: taskData.task.assigned_agent_id || '',
            assignedTeamId: taskData.task.assigned_team_id || '',
            dueDate: taskData.task.due_date || '',
          });
        }
      } catch (error) {
        console.error('Error fetching task details:', error);
      }
    };

    fetchAgentsAndTeams();
    fetchTaskDetails();
  }, [emailQueryId]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setTaskMessage('');
    setTeamsMessage('');
    try {
      const response = await fetch(`${config.API_URL}/api/assign-task/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email_query_id: emailQueryId,
          title: formData.title,
          description: formData.description,
          assigned_team_id: formData.assignedTeamId,
          assigned_agent_id: formData.assignedAgentId,
          due_date: formData.dueDate,
        }),
      });

      const result = await response.json();
      if (response.ok) {
        setTaskMessage('Task assigned successfully!');
        if (result.teams_status === 'success') {
          setTeamsMessage('Task details sent to Teams successfully!');
        } else {
          setTeamsMessage('Failed to send task details to Teams.');
        }
      } else {
        setTaskMessage(`Error: ${result.error}`);
      }
    } catch (error) {
      console.error('Error assigning task:', error);
      setTaskMessage('Failed to assign task.');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = () => {
    setCollapsed(!collapsed);
    onToggle(!collapsed); // Notify parent about the collapsed state
  };


  return (
    <div className="sidebar2">
      {/* Back link to /queries */}
      <a href="/queries" className="sidebar2-back-link">
        ← Back
      </a>
      <button className="collapse-button" onClick={handleToggle}>
        {collapsed ? '>' : '<'}
      </button>
      <h2 className="sidebar2-title">Assign Task</h2>
      <form onSubmit={handleSubmit} className="assign-task-form">
        <div className="form-group">
          <label htmlFor="title">Title</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleInputChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleInputChange}
            required
          ></textarea>
        </div>
        <div className="form-group">
          <label htmlFor="assignedAgentId">Assign to Agent</label>
          <select
            id="assignedAgentId"
            name="assignedAgentId"
            value={formData.assignedAgentId}
            onChange={handleInputChange}
          >
            <option value="">Select an agent</option>
            {agents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="assignedTeamId">Assign to Team</label>
          <select
            id="assignedTeamId"
            name="assignedTeamId"
            value={formData.assignedTeamId}
            onChange={handleInputChange}
          >
            <option value="">Select a team</option>
            {teams.map((team) => (
              <option key={team.id} value={team.id}>
                {team.name}
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="dueDate">Due Date</label>
          <input
            type="date"
            id="dueDate"
            name="dueDate"
            value={formData.dueDate}
            onChange={handleInputChange}
            required
          />
        </div>
        <button type="submit" className="assign-task-button" disabled={loading}>
          {loading ? 'Assigning...' : 'Assign Task'}
        </button>
        {taskMessage && <p className={`form-message ${taskMessage.includes('Error') ? 'error' : 'success'}`}>{taskMessage}</p>}
        {teamsMessage && <p className={`form-message ${teamsMessage.includes('Failed') ? 'error' : 'success'}`}>{teamsMessage}</p>}
      </form>
    </div>
  );
};

export default Sidebar2;
