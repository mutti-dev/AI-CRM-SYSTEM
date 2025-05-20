import React, { useState } from 'react';
import '../styles/TicketTabs.css';
import { useNavigate } from 'react-router-dom';

const TicketTabs = () => {
    const [tabs, setTabs] = useState([]); // Array of open tickets
    const [searchId, setSearchId] = useState(''); // Search input value
    const navigate = useNavigate();

    // Function to open a new ticket tab
    const openTicket = (ticketId) => {
        if (!tabs.some((tab) => tab.id === ticketId)) {
            setTabs([...tabs, { id: ticketId, label: `#${ticketId}` }]);
        }
        navigate(`/details/${ticketId}`); // Navigate to the ticket details page
    };

    // Function to close a ticket tab
    const closeTicket = (ticketId) => {
        setTabs(tabs.filter((tab) => tab.id !== ticketId));
    };

    // Function to handle search and open ticket by ID
    const handleSearch = () => {
        if (searchId.trim()) {
            openTicket(searchId.trim());
            setSearchId(''); // Clear the search input
        }
    };

    return (
        <div className="ticket-tabs-container">
            {/* Search Bar */}
            <div className="ticket-tabs-search">
                <input
                    type="text"
                    placeholder="Search Ticket ID"
                    value={searchId}
                    onChange={(e) => setSearchId(e.target.value)}
                />
                <button onClick={handleSearch}>Search</button>
            </div>

            {/* Tabs */}
            <div className="ticket-tabs">
                {tabs.map((tab) => (
                    <div key={tab.id} className="ticket-tab">
                        <span>{tab.label}</span>
                        <button onClick={() => closeTicket(tab.id)}>&times;</button>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default TicketTabs;
