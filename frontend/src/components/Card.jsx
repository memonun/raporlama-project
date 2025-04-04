import React from 'react';

const Card = ({ children, className = '', onClick }) => {
  // onClick prop'u varsa tıklanabilir özellikler ekle
  const isClickable = typeof onClick === 'function';

  return (
    <div 
      className={`bg-white rounded-lg shadow-md p-6 ${isClickable ? 'cursor-pointer hover:shadow-lg transition-shadow duration-200' : ''} ${className}`}
      onClick={onClick}
      role={isClickable ? "button" : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={isClickable ? (e) => { if (e.key === 'Enter' || e.key === 'Space') onClick(); } : undefined}
    >
      {children}
    </div>
  );
};

export default Card; 