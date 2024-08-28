import axios from 'axios';

export const uploadPdf = async (file, model) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('model', model);

  const response = await axios.post('http://localhost:8000/upload_pdf', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
  return response.data;
};

export const uploadPdfUrl = async (url, model) => {
  const response = await axios.post('http://localhost:8000/upload_pdf_url', null, {
    params: { url, model }
  });
  return response.data;
};

export const embedAllPdfs = async (model) => {
    const response = await axios.post('http://localhost:8000/embed_all_pdfs', null, {
      params: { model }
    });
    return response.data.message;
  };

export const askQuestion = async (question, language) => {
  const response = await axios.post('http://localhost:8000/ask_question', 
    { question },
    { params: { language } }
  );
  return response.data.answer;
};
