import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState('');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [model, setModel] = useState('use');
  const [language, setLanguage] = useState('english');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  useEffect(scrollToBottom, [messages]);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUrlChange = (event) => {
    setUrl(event.target.value);
  };

  const handleModelChange = (event) => {
    setModel(event.target.value);
  };

  const handleLanguageChange = (event) => {
    setLanguage(event.target.value);
  };

  const handleUpload = async () => {
    if (!file) {
      alert('Please select a file first!');
      return;
    }
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model', model);
    try {
      const response = await axios.post('http://localhost:8000/upload_pdf', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setMessages([...messages, { text: response.data.message, sender: 'bot' }]);
    } catch (error) {
      console.error('Error uploading file:', error);
      setMessages([...messages, { text: 'Error uploading PDF.', sender: 'bot' }]);
    }
    setIsUploading(false);
  };

  const handleUrlUpload = async () => {
    if (!url) {
      alert('Please enter a URL first!');
      return;
    }
    setIsUploading(true);
    try {
      const response = await axios.post('http://localhost:8000/upload_pdf_url', null, {
        params: { url, model }
      });
      setMessages([...messages, { text: response.data.message, sender: 'bot' }]);
    } catch (error) {
      console.error('Error uploading PDF from URL:', error);
      setMessages([...messages, { text: 'Error uploading PDF from URL.', sender: 'bot' }]);
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
      const response = await axios.post('http://localhost:8000/ask_question', 
        { question: input },
        { params: { language: language } }
      );
      setMessages(messages => [...messages, { text: response.data.answer, sender: 'bot' }]);
    } catch (error) {
      console.error('Error asking question:', error);
      setMessages(messages => [...messages, { text: 'Error getting answer.', sender: 'bot' }]);
    }
    setIsAsking(false);
  };

  return (
    <div className="App" style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1>PDFGPT</h1>
      <div style={{ marginBottom: '20px' }}>
        <input type="file" onChange={handleFileChange} accept=".pdf" />
        <select value={model} onChange={handleModelChange} style={{ marginLeft: '10px' }}>
          <option value="use">Universal Sentence Encoder</option>
          <option value="ada">OpenAI Ada</option>
        </select>
        <button onClick={handleUpload} disabled={isUploading} style={{ marginLeft: '10px' }}>
          {isUploading ? 'Uploading...' : 'Upload PDF'}
        </button>
      </div>
      <div style={{ marginBottom: '20px' }}>
        <input 
          type="text" 
          value={url} 
          onChange={handleUrlChange} 
          placeholder="Enter PDF URL"
          style={{ width: '60%', marginRight: '10px' }}
        />
        <button onClick={handleUrlUpload} disabled={isUploading}>
          {isUploading ? 'Uploading...' : 'Upload PDF from URL'}
        </button>
      </div>
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
      <form onSubmit={handleSubmit}>
        <select value={language} onChange={handleLanguageChange} style={{ marginRight: '10px' }}>
          <option value="english">English</option>
          <option value="korean">한국어</option>
        </select>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          style={{ width: '60%', marginRight: '10px', padding: '5px' }}
        />
        <button type="submit" disabled={isAsking} style={{ width: '20%', padding: '5px' }}>
          {isAsking ? 'Thinking...' : 'Ask'}
        </button>
      </form>
    </div>
  );
}

export default App;