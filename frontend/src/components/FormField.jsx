import React from 'react';

const FormField = ({ question, value, onChange }) => {
  const { id, text, type, required, options } = question;

  // Her soru tipi için farklı bir bileşen render ediyoruz
  const renderField = () => {
    switch (type) {
      case 'text':
        return (
          <input
            type="text"
            id={id}
            value={value || ''}
            onChange={(e) => onChange(id, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder={`${text}`}
            required={required}
          />
        );
      
      case 'textarea':
        return (
          <textarea
            id={id}
            value={value || ''}
            onChange={(e) => onChange(id, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            rows="4"
            placeholder={`${text}`}
            required={required}
          />
        );
      
      case 'checkbox':
        return (
          <div className="flex items-center space-x-4">
            {options && options.map(option => (
              <label key={option} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  name={id}
                  value={option}
                  checked={value === option}
                  onChange={() => onChange(id, option)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                  required={required}
                />
                <span className="text-gray-700">{option}</span>
              </label>
            ))}
          </div>
        );
      
      case 'select':
        return (
          <select
            id={id}
            value={value || ''}
            onChange={(e) => onChange(id, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            required={required}
          >
            <option value="">Seçiniz...</option>
            {options && options.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        );
      
      case 'file':
        return (
          <div className="mt-1 flex items-center">
            <span className="inline-block h-12 w-12 rounded-md overflow-hidden bg-gray-100">
              <svg className="h-full w-full text-gray-300" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
              </svg>
            </span>
            <label
              htmlFor={`file-upload-${id}`}
              className="ml-5 rounded-md border border-gray-300 bg-white py-2 px-3 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 cursor-pointer"
            >
              Dosya Seç
            </label>
            <input
              id={`file-upload-${id}`}
              name={id}
              type="file"
              className="sr-only"
              onChange={(e) => {
                // Dosya seçildiğinde sadece dosya adını kaydediyoruz
                // Gerçek uygulamada backend'e yüklenecektir
                const fileName = e.target.files[0]?.name || '';
                onChange(id, fileName);
              }}
            />
            {value && <span className="ml-2 text-sm text-gray-500">{value}</span>}
          </div>
        );
      
      default:
        return (
          <input
            type="text"
            id={id}
            value={value || ''}
            onChange={(e) => onChange(id, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder={`${text}`}
            required={required}
          />
        );
    }
  };

  return (
    <div className="mb-6">
      <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-2">
        {text}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {renderField()}
    </div>
  );
};

export default FormField; 