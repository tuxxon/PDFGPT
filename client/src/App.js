import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import EmbedAllButton from './components/EmbedAllButton';
import Messages from './components/Messages';
import QuestionForm from './components/QuestionForm';
import UploadedFiles from './components/UploadedFiles';

function App() {
  const [messages, setMessages] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isEmbedding, setIsEmbedding] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [language, setLanguage] = useState('english');

  return (
    <div className="App" style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1>PDFGPT</h1>
      <FileUpload
        setMessages={setMessages}
        setUploadedFiles={setUploadedFiles}
        isUploading={isUploading}
        setIsUploading={setIsUploading}
      />
      <EmbedAllButton
        setMessages={setMessages}
        isEmbedding={isEmbedding}
        setIsEmbedding={setIsEmbedding}
      />
      <UploadedFiles uploadedFiles={uploadedFiles} />
      <Messages messages={messages} />
      <QuestionForm
        setMessages={setMessages}
        language={language}
        setLanguage={setLanguage}
        isAsking={isAsking}
        setIsAsking={setIsAsking}
      />
    </div>
  );
}

export default App;
