import React from 'react';
import '../styles/Sidebar.css';
import logo from '../assets/maxlogo.png'; // Import the image file
import { NavLink } from 'react-router-dom';

const Sidebar = () => {
  const menuItems = [
    { id: 1, name: 'Dashboard', icon: 'fa-chart-line', link: '/' },
    { id: 2, name: 'Queries', icon: 'fa-comments', link: '/queries' },
    { id: 3, name: 'Tasks', icon: 'fa-tasks', link: '/tasks' },
    { id: 4, name: 'Settings', icon: 'fa-cog', link: '/settings' },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <img src={logo} alt="CRM Logo" />
      </div>
      <h2 className="sidebar-title">Auto CRM System</h2>
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
              {item.name}
            </NavLink>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Sidebar;