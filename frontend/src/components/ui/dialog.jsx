import React, { Fragment, useState, useEffect, useRef } from 'react';

// Dialog context to manage open/close state
const DialogContext = React.createContext({
  open: false,
  setOpen: () => {},
});

// Main Dialog component
export const Dialog = ({ children, open = false, onOpenChange }) => {
  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onOpenChange(false);
    }
  };

  if (!open) return null;

  return (
    <DialogContext.Provider value={{ open, setOpen: onOpenChange }}>
      <div 
        className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4 overflow-y-auto"
        onClick={handleBackdropClick}
        aria-modal="true"
        role="dialog"
      >
        <div 
          className="relative bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {children}
        </div>
      </div>
    </DialogContext.Provider>
  );
};

// Dialog Header component
export const DialogHeader = ({ children, className = "", ...props }) => {
  return (
    <div className={`px-6 pt-6 pb-3 ${className}`} {...props}>
      {children}
    </div>
  );
};

// Dialog Title component
export const DialogTitle = ({ children, className = "", ...props }) => {
  return (
    <h2 className={`text-xl font-semibold text-gray-900 ${className}`} {...props}>
      {children}
    </h2>
  );
};

// Dialog Description component
export const DialogDescription = ({ children, className = "", ...props }) => {
  return (
    <p className={`text-sm text-gray-500 mt-1 ${className}`} {...props}>
      {children}
    </p>
  );
};

// Dialog Content component
export const DialogContent = ({ children, className = "", ...props }) => {
  return (
    <div className={`px-6 py-4 ${className}`} {...props}>
      {children}
    </div>
  );
};

// Dialog Footer component
export const DialogFooter = ({ children, className = "", ...props }) => {
  return (
    <div className={`px-6 py-4 bg-gray-50 flex justify-end space-x-2 rounded-b-lg ${className}`} {...props}>
      {children}
    </div>
  );
};

export default Dialog; 