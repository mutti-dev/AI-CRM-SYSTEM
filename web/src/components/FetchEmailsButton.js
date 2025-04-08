import React, { useState } from 'react';
import config from '../config/config';

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
      alert(`Fetched ${result.emails_fetched} new unread emails.`);
    } catch (error) {
      console.error('Error fetching unread emails:', error);
      alert('Failed to fetch unread emails.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleFetchEmails}
      className="fetch-emails-button"
      disabled={loading}
    >
      {loading ? (
        <span className="spinner"></span>
      ) : (
        'Fetch Unread Emails'
      )}
    </button>
  );
};

export default FetchEmailsButton;
