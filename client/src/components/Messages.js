import React, { useRef, useEffect } from 'react';

const Messages = ({ messages }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  useEffect(scrollToBottom, [messages]);

  return (
    <div style={{ height: '400px', border: '1px solid #ccc', overflowY: 'scroll', marginBottom: '20px', padding: '10px' }}>
      {messages.map((message, index) => (
        <div key={index} style={{ 
          marginBottom: '15px',
          textAlign: message.sender === 'user' ? 'right' : 'left' 
        }}>
          <span style={{ 
            background: message.sender === 'user' ? '#007bff' : '#28a745', 
            color: 'white', 
            padding: '8px 12px',
            borderRadius: '10px',
            display: 'inline-block',
            maxWidth: '70%',
            wordWrap: 'break-word'
          }}>
            {message.text}
          </span>
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default Messages;
