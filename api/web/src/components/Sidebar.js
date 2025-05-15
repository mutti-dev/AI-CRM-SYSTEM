import React, { useState } from 'react';
import '../styles/Sidebar.css';
import logo from '../assets/maxlogo.png';
import { NavLink } from 'react-router-dom';
// Import SVG components
import Whatsapp from '../assets/svgs/Whatsapp';
import Email from '../assets/svgs/Email';
import Tasks from '../assets/svgs/Tasks';
import Settings from '../assets/svgs/Settings';
import Dashboard from '../assets/svgs/Dashboard';


const Sidebar = ({ onToggle }) => {
  const [collapsed, setCollapsed] = useState(false);
  const menuItems = [
    { id: 1, name: 'Dashboard', icon: <Dashboard height={30} width={30} />, link: '/' },
    { id: 2, name: 'Email Queries', icon: <Email height={30} width={30}/>, link: '/queries' },
    { id: 3, name: 'WhatsApp Queries', icon: <Whatsapp height={30} width={30}/>, link: '/whatsapp-messages' },
    { id: 4, name: 'Tasks', icon: <Tasks height={30} width={30}/>, link: '/tasks' },
    { id: 5, name: 'Settings', icon: <Settings height={30} width={30}/>, link: '/settings' },
  ];

  const handleToggle = () => {
    setCollapsed(!collapsed);
    onToggle(!collapsed);
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
              {/* Render SVG icon */}
              {item.icon}
              {!collapsed && item.name}
            </NavLink>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Sidebar;