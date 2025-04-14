import React, { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import '../styles/DetailsScreen.css';
import config from '../config/config';
import Sidebar2 from './Sidebar2';
import { formatTime, formatDate } from '../utils/formatTime';

const DetailsScreen = () => {
  const { id } = useParams();
  const [email, setEmail] = useState(null);
  const [threadMessages, setThreadMessages] = useState([]);
  const [replyContent, setReplyContent] = useState('');
  const [replyingTo, setReplyingTo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sendingReply, setSendingReply] = useState(false);
  const [error, setError] = useState(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const [messageType, setMessageType] = useState('email'); // 'email' or 'whatsapp'

  // Auto-resize textarea as user types
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [replyContent]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [threadMessages, isExpanded]);

  const fetchDetails = async () => {
    try {
      const endpoint = messageType === 'email' 
        ? `${config.API_URL}/api/email-details/${id}/`
        : `${config.API_URL}/api/whatsapp-details/${id}/`;
      
      const response = await fetch(endpoint);
      if (!response.ok) throw new Error('Failed to fetch details');
      const result = await response.json();
      
      setEmail(result.message || null);
      setThreadMessages(result.message?.thread_messages || []);
    } catch (error) {
      console.error('Error:', error);
      setError('Failed to load conversation');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [id, messageType]);

  const handleReply = async (messageId = null) => {
    if (!replyContent.trim()) {
      setError('Please write your reply before sending');
      return;
    }

    setSendingReply(true);
    setError(null);

    try {
      const response = await fetch(`${config.API_URL}/api/reply-email/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email_query_id: email.id,
          content: replyContent,
          message_id: messageId
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to send reply');
      }

      const result = await response.json();
      setThreadMessages(prev => [...prev, {
        id: result.reply.gmail_message_id,
        sender: 'You',
        body: result.reply.content,
        date: result.reply.sent_at,
        isOutgoing: true
      }]);

      setReplyContent('');
      setReplyingTo(null);
    } catch (error) {
      setError(error.message);
    } finally {
      setSendingReply(false);
      textareaRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleReply(replyingTo);
    }
  };

  if (loading) {
    return (
      <div className="details-screen loading">
        <div className="loading-spinner-container">
          <div className="loading-spinner"></div>
          <p>Loading conversation...</p>
        </div>
      </div>
    );
  }

  if (!email) {
    return (
      <div className="details-screen error">
        <div className="error-message">
          <p>Could not load this conversation</p>
          <button 
            className="retry-button"
            onClick={fetchDetails}
          >
            <span className="refresh-icon">↻</span> Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="details-screen">
      <Sidebar2 emailQueryId={id} />
      <div className="details-content">
        <header className="chat-header">
          <div className="header-main">
            <div className="header-info">
              <div className="subject-row">
                <h2>{email.subject}</h2>
                <button 
                  className="expand-button"
                  onClick={() => setIsExpanded(!isExpanded)}
                  aria-label={isExpanded ? "Collapse header" : "Expand header"}
                >
                  {isExpanded ? '−' : '+'}
                </button>
              </div>
              
              {isExpanded && (
                <div className="expanded-header">
                  <div className="meta-row">
                    <span className="meta-label">From:</span>
                    <span className="meta-value">{email.sender}</span>
                  </div>
                  <div className="meta-row">
                    <span className="meta-label">Date:</span>
                    <span className="meta-value">{formatDate(email.date)}</span>
                  </div>
                  {email.to && (
                    <div className="meta-row">
                      <span className="meta-label">To:</span>
                      <span className="meta-value">{email.to}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
            
            <div className="header-actions">
              <button 
                className="refresh-button"
                onClick={fetchDetails}
                aria-label="Refresh conversation"
              >
                <span className="refresh-icon">↻</span>
              </button>
            </div>
          </div>
        </header>

        <div className="chat-container">
          <div className="conversation-view">
            <div className="messages-container">
              {threadMessages.map((message, index) => (
                <div 
                  key={message.id || index} 
                  className={`message-wrapper ${message.isOutgoing ? 'outgoing' : 'incoming'}`}
                >
                  <div className="message-bubble">
                    <div className="message-header">
                      <span className="message-sender">
                        {message.sender}
                        {index === 0 && <span className="original-label"> (original)</span>}
                      </span>
                      <span className="message-time" title={new Date(message.date).toString()}>
                        {formatTime(message.date)}
                      </span>
                    </div>
                    <div className="message-content">
                      {message.body.split('\n').map((line, idx) => (
                        line ? <p key={idx}>{line}</p> : <br key={idx} />
                      ))}
                    </div>
                    {!message.isOutgoing && (
                      <div className="message-actions">
                        <button 
                          className="action-button reply"
                          onClick={() => {
                            setReplyingTo(message.id);
                            textareaRef.current?.focus();
                          }}
                        >
                          <span className="reply-icon">↩</span> Reply
                        </button>
                        {index > 0 && (
                          <button 
                            className="action-button quote"
                            onClick={() => {
                              setReplyContent(prev => `> ${message.body.replace(/\n/g, '\n> ')}\n\n${prev}`);
                              setReplyingTo(message.id);
                              textareaRef.current?.focus();
                            }}
                          >
                            <span className="quote-icon">❝</span> Quote
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>

          <div className="composer-container">
            {error && (
              <div className="error-banner">
                <span className="error-icon">⚠</span>
                <span className="error-message">{error}</span>
                <button 
                  className="close-error" 
                  onClick={() => setError(null)}
                  aria-label="Close error message"
                >
                  ×
                </button>
              </div>
            )}
            
            {replyingTo && (
              <div className="reply-banner">
                <span className="reply-icon">↩</span>
                <span>Replying to message</span>
                <button 
                  className="cancel-reply" 
                  onClick={() => setReplyingTo(null)}
                >
                  Cancel
                </button>
              </div>
            )}

            <div className="composer">
              <textarea
                ref={textareaRef}
                placeholder="Type your reply here..."
                className="composer-input"
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={sendingReply}
                rows={1}
                aria-label="Reply message input"
              />
              <div className="composer-actions">
                <div className="character-count">
                  {replyContent.length}/5000
                </div>
                <button 
                  className={`send-button ${sendingReply ? 'sending' : ''}`}
                  onClick={() => handleReply(replyingTo)}
                  disabled={sendingReply || !replyContent.trim()}
                  aria-label="Send reply"
                >
                  {sendingReply ? (
                    <>
                      <span className="loading-spinner"></span>
                      <span>Sending...</span>
                    </>
                  ) : (
                    <>
                      <span className="send-icon">→</span>
                      <span>Send</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetailsScreen;