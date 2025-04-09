import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import '../styles/DetailsScreen.css';
import config from '../config/config';
import Sidebar2 from './Sidebar2';
import { formatTime } from '../utils/formatTime';

const DetailsScreen = () => {
  const { id } = useParams();
  const [email, setEmail] = useState(null);
  const [replies, setReplies] = useState([]); // Initialize as an empty array
  const [replyContent, setReplyContent] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEmailDetails = async () => {
      try {
        const response = await fetch(`${config.API_URL}/api/email-details/${id}/`);
        if (!response.ok) {
          throw new Error('Failed to fetch email details');
        }
        const result = await response.json();
        setEmail(result.email || null); // Ensure email is set to null if not found
      } catch (error) {
        console.error('Error fetching email details:', error);
      }
    };

    const fetchReplies = async () => {
      try {
        const response = await fetch(`${config.API_URL}/api/email-replies/${id}/`);
        if (!response.ok) {
          throw new Error('Failed to fetch email replies');
        }
        const result = await response.json();
        setReplies(result.replies || []); // Ensure replies is an empty array if not found
      } catch (error) {
        console.error('Error fetching email replies:', error);
      }
    };

    const fetchData = async () => {
      setLoading(true);
      await Promise.all([fetchEmailDetails(), fetchReplies()]);
      setLoading(false);
    };

    fetchData();
  }, [id]);

  const handleReply = async () => {
    try {
      const response = await fetch(`${config.API_URL}/api/reply-email/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email_query_id: email.id,
          content: replyContent,
        }),
      });
      if (!response.ok) {
        throw new Error('Failed to send reply');
      }
      const result = await response.json();
      alert('Reply sent successfully!');
      setReplyContent('');
      // Refresh replies after sending
      setReplies((prevReplies) => [...prevReplies, result.reply || {}]); // Ensure reply is valid
    } catch (error) {
      console.error('Error sending reply:', error);
      alert('Failed to send reply');
    }
  };

  if (loading) {
    return <div className="details-screen">Loading...</div>;
  }

  if (!email) {
    return <div className="details-screen">Email not found</div>;
  }

  return (
    <div className="details-screen">
      {/* <Sidebar2 emailQueryId={id} /> */}
      <div className="details-content">
        <header className="chat-header">
          <h2>Subject: {email.subject}</h2>
          <p>From: {email.sender}</p>
        </header>
        <div className="chat-container">
          <div className="messages-container">
            <div className="message received">
              <div className="message-content">{email.body}</div>
              <div className="timestamp">{formatTime(email.received_at)}</div>
            </div>
            {replies.map((reply, index) => (
              reply && reply.content ? ( // Validate reply and content before rendering
                <div key={index} className="message sent">
                  <div className="message-content">{reply.content}</div>
                  <div className="timestamp">{formatTime(reply.sent_at)}</div>
                </div>
              ) : null
            ))}
          </div>
          <div className="input-container">
            <input
              type="text"
              placeholder="Type your reply here..."
              className="message-input"
              value={replyContent}
              onChange={(e) => setReplyContent(e.target.value)}
            />
            <button className="send-button" onClick={handleReply}>
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetailsScreen;