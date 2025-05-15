import React, { useState, useEffect } from 'react';
import config from '../config/config';
import Refresh from '../assets/svgs/Refresh';

const FetchEmailsButton = ({ onEmailsFetched }) => {
  const [loading, setLoading] = useState(false);

  const handleFetchEmails = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${config.API_URL}/api/fetch-emails/`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to fetch unread emails');
      }
      const result = await response.json();
      onEmailsFetched(result.emails || []);
      console.log(`Fetched ${result.emails_fetched} new unread emails.`);
    } catch (error) {
      console.error('Error fetching unread emails:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Set an interval to fetch emails every 5 minutes (300000 ms)
    const interval = setInterval(() => {
      handleFetchEmails();
    }, 40000);

    // Cleanup the interval on component unmount
    return () => clearInterval(interval);
  }, []); // Empty dependency array ensures this runs only once on mount

  return (
    <div
      onClick={handleFetchEmails}
      className="fetch-emails-icon"
      style={{ cursor: loading ? 'not-allowed' : 'pointer' }}
    >
      <Refresh
        style={{
          width: '30px',
          height: '30px',
          fill: loading ? '#ccc' : '#0084ff',
          animation: loading ? 'spin 1s linear infinite' : 'none',
        }}
      />
    </div>
  );
};

export default FetchEmailsButton;
