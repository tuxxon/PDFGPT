import React, { useState } from 'react';
import { embedAllPdfs } from '../services/api';

const EmbedAllButton = ({ setMessages, isEmbedding, setIsEmbedding }) => {
  const [model, setModel] = useState('use'); // 기본 모델 설정

  const handleModelChange = (event) => {
    setModel(event.target.value);
  };

  const handleEmbedAll = async () => {
    setIsEmbedding(true);
    try {
      const message = await embedAllPdfs(model); // 선택된 모델을 서버로 전달
      setMessages(prev => [...prev, { text: message, sender: 'bot' }]);
    } catch (error) {
      setMessages(prev => [...prev, { text: 'Error embedding PDFs.', sender: 'bot' }]);
    }
    setIsEmbedding(false);
  };

  return (
    <div style={{ marginBottom: '20px' }}>
      <select value={model} onChange={handleModelChange} style={{ marginRight: '10px' }}>
        <option value="use">Universal Sentence Encoder</option>
        <option value="ada">OpenAI Ada</option>
      </select>
      <button onClick={handleEmbedAll} disabled={isEmbedding}>
        {isEmbedding ? 'Embedding...' : 'Embed All PDFs'}
      </button>
    </div>
  );
};

export default EmbedAllButton;
