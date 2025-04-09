import React, { useState } from 'react';
import '../styles/Sidebar.css';
import logo from '../assets/maxlogo.png'; // Import the image file
import { NavLink } from 'react-router-dom';

const Sidebar = ({ onToggle }) => {
  const [collapsed, setCollapsed] = useState(false); // State to manage collapse
  const menuItems = [
    { id: 1, name: 'Dashboard', icon: 'fa-chart-line', link: '/' },
    { id: 2, name: 'Queries', icon: 'fa-comments', link: '/queries' },
    { id: 3, name: 'Tasks', icon: 'fa-tasks', link: '/tasks' },
    { id: 4, name: 'Settings', icon: 'fa-cog', link: '/settings' },
  ];

  const handleToggle = () => {
    setCollapsed(!collapsed);
    onToggle(!collapsed); // Notify parent about the collapsed state
  };

  return (
    <div className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-logo">
        <img src={logo} alt="CRM Logo" />
      </div>
      <h2 className="sidebar-title">{!collapsed && 'Auto CRM System'}</h2>
      <button className="collapse-button" onClick={handleToggle}>
        {collapsed ? '>' : '<'}
      </button>
      <ul className="sidebar-menu">
        {menuItems.map((item) => (
          <li key={item.id} className="sidebar-item">
            <NavLink
              to={item.link}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? 'active' : ''}`
              }
            >
              <i className={`fas ${item.icon}`}></i>
              {!collapsed && item.name}
            </NavLink>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Sidebar;