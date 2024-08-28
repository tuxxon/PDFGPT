import React, { useState } from 'react';
import { askQuestion } from '../services/api';

const QuestionForm = ({ setMessages, language, setLanguage, isAsking, setIsAsking }) => {
  const [input, setInput] = useState('');

  const handleLanguageChange = (event) => {
    setLanguage(event.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    setMessages(prev => [...prev, { text: input, sender: 'user' }]);
    setInput('');
    setIsAsking(true);

    try {
      const answer = await askQuestion(input, language);
      setMessages(prev => [...prev, { text: answer, sender: 'bot' }]);
    } catch (error) {
      setMessages(prev => [...prev, { text: 'Error getting answer.', sender: 'bot' }]);
    }
    setIsAsking(false);
  };

  return (
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
  );
};

export default QuestionForm;
