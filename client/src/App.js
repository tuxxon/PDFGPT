import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  useEffect(scrollToBottom, [messages]);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert('Please select a file first!');
      return;
    }
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      await axios.post('http://localhost:8000/upload_pdf', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setMessages([...messages, { text: 'PDF uploaded successfully!', sender: 'bot' }]);
    } catch (error) {
      console.error('Error uploading file:', error);
      setMessages([...messages, { text: 'Error uploading PDF.', sender: 'bot' }]);
    }
    setIsUploading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    setMessages([...messages, { text: input, sender: 'user' }]);
    setInput('');
    setIsAsking(true);

    try {
      const response = await axios.post('http://localhost:8000/ask_question', { question: input });
      setMessages(messages => [...messages, { text: response.data.answer, sender: 'bot' }]);
    } catch (error) {
      console.error('Error asking question:', error);
      setMessages(messages => [...messages, { text: 'Error getting answer.', sender: 'bot' }]);
    }
    setIsAsking(false);
  };

  return (
    <div className="App" style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1>PDF QA System</h1>
      <div style={{ marginBottom: '20px' }}>
        <input type="file" onChange={handleFileChange} accept=".pdf" />
        <button onClick={handleUpload} disabled={isUploading}>
          {isUploading ? 'Uploading...' : 'Upload PDF'}
        </button>
      </div>
      <div style={{ height: '400px', border: '1px solid #ccc', overflowY: 'scroll', marginBottom: '20px', padding: '10px' }}>
      {messages.map((message, index) => (
        <div key={index} style={{ 
          marginBottom: '15px',  // 여기를 10px에서 15px로 증가
          textAlign: message.sender === 'user' ? 'right' : 'left' 
        }}>
          <span style={{ 
            background: message.sender === 'user' ? '#007bff' : '#28a745', 
            color: 'white', 
            padding: '8px 12px',  // 패딩을 약간 증가
            borderRadius: '20px',
            display: 'inline-block',  // inline-block으로 변경
            maxWidth: '70%',  // 최대 너비 설정
            wordWrap: 'break-word'  // 긴 단어 줄바꿈
          }}>
            {message.text}
          </span>
        </div>
      ))}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          style={{ width: '70%', marginRight: '10px', padding: '5px' }}
        />
        <button type="submit" disabled={isAsking} style={{ width: '25%', padding: '5px' }}>
          {isAsking ? 'Thinking...' : 'Ask'}
        </button>
      </form>
    </div>
  );
}

export default App;