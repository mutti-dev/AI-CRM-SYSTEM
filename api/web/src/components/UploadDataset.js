import React, { useState } from 'react';
import config from '../config/config';
import CheckMark from '../assets/svgs/CheckMark';
import XMark from '../assets/svgs/XMark';

const UploadDataset = () => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [data, setData] = useState('');
  const [message, setMessage] = useState('');
  const [isJsonValid, setIsJsonValid] = useState(true);

  const handleUpload = async () => {
    try {
      JSON.parse(data); // Validate JSON first
      setIsJsonValid(true);

      const response = await fetch(`${config.API_URL}/api/upload-dataset/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          description,
          data: JSON.parse(data),
        }),
      });

      const result = await response.json();
      if (response.ok) {
        setMessage({ type: 'success', text: 'Dataset uploaded successfully!' });
      } else {
        setMessage({ type: 'error', text: `Error: ${result.message}` });
      }
    } catch (error) {
      setIsJsonValid(false);
      setMessage({ type: 'error', text: `Error: ${error.message}` });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-md overflow-hidden p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Upload Fine-Tuned Dataset</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Dataset Name</label>
            <input
              type="text"
              placeholder="Enter dataset name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              placeholder="Enter description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all h-32"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Dataset (JSON format)</label>
            <textarea
              placeholder={`Enter JSON data\nExample: {\n  "key": "value"\n}`}
              value={data}
              onChange={(e) => setData(e.target.value)}
              className={`w-full px-4 py-2 border ${
                isJsonValid ? 'border-gray-300' : 'border-red-500'
              } rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all h-48 font-mono text-sm`}
            />
            {!isJsonValid && (
              <p className="text-red-500 text-sm mt-1">Invalid JSON format</p>
            )}
          </div>

          <button
            onClick={handleUpload}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
          >
            Upload Dataset
          </button>

          {message && (
            <div
              className={`p-4 rounded-lg ${
                message.type === 'success'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              <div className="flex items-center">
                {message.type === 'success' ? (
                  <CheckMark className="w-5 h-5 mr-2" />
                ) : (
                  <XMark className="w-5 h-5 mr-2" />
                )}
                <span>{message.text}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UploadDataset;