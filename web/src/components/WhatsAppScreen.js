import React, { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import '../styles/WhatsAppScreen.css';
import config from '../config/config';
import Sidebar2 from './Sidebar2';
import { formatTime } from '../utils/formatTime';

const WhatsAppScreen = () => {
  const { id } = useParams();
  const [conversation, setConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [replyContent, setReplyContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [sendingReply, setSendingReply] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchWhatsAppThread = async () => {
    try {
      const response = await fetch(`${config.API_URL}/api/whatsapp-details/${id}/`);
      if (!response.ok) throw new Error('Failed to fetch conversation');
      const data = await response.json();
      setConversation(data.conversation);
      setMessages(data.messages);
    } catch (error) {
      setError('Failed to load WhatsApp conversation');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWhatsAppThread();
  }, [id]);

  const handleSendMessage = async () => {
    if (!replyContent.trim()) {
      setError('Message cannot be empty');
      return;
    }

    setSendingReply(true);
    setError(null);

    try {
      const response = await fetch(`${config.API_URL}/api/whatsapp-reply/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          thread_id: conversation.thread_id,
          content: replyContent
        }),
      });

      if (!response.ok) throw new Error('Failed to send message');

      const result = await response.json();
      setMessages(prev => [...prev, {
        id: result.message_id,
        content: replyContent,
        sent_at: new Date().toISOString(),
        isOutgoing: true
      }]);

      setReplyContent('');
    } catch (error) {
      setError('Failed to send message. Please try again.');
    } finally {
      setSendingReply(false);
    }
  };

  if (loading) {
    return (
      <div className="whatsapp-screen loading">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="whatsapp-screen">
      <Sidebar2 />
      <div className="whatsapp-content">
        <header className="whatsapp-header">
          <div className="contact-info">
            <div className="contact-avatar">
              {conversation?.customer_name?.charAt(0) || '#'}
            </div>
            <div className="contact-details">
              <h2>{conversation?.customer_name || conversation?.phone_number}</h2>
              <span className="status">
                {conversation?.status || 'Active'}
              </span>
            </div>
          </div>
          <div className="header-actions">
            <button onClick={fetchWhatsAppThread} className="refresh-button">
              <span className="refresh-icon">↻</span>
            </button>
          </div>
        </header>

        <div className="messages-wrapper">
          <div className="messages-container">
            {messages.map((message, index) => (
              <div
                key={message.id || index}
                className={`message ${message.isOutgoing ? 'outgoing' : 'incoming'}`}
              >
                <div className="message-bubble">
                  <div className="message-text">{message.content}</div>
                  <div className="message-meta">
                    <span className="message-time">
                      {formatTime(message.sent_at)}
                    </span>
                    {message.isOutgoing && (
                      <span className="message-status">
                        {message.status === 'read' ? '✓✓' : '✓'}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="composer">
            {error && (
              <div className="error-message">
                {error}
                <button onClick={() => setError(null)}>×</button>
              </div>
            )}
            <div className="input-wrapper">
              <textarea
                ref={textareaRef}
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                placeholder="Type a message"
                rows={1}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
              />
              <button
                className={`send-button ${sendingReply ? 'sending' : ''}`}
                onClick={handleSendMessage}
                disabled={sendingReply || !replyContent.trim()}
              >
                {sendingReply ? '...' : '➤'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WhatsAppScreen;
