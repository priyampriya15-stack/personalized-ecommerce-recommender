import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export const ErrorMessage = ({
  title = 'Something went wrong',
  message = 'We encountered an error while communicating with the server.',
  onRetry,
}) => (
  <div className="rounded-2xl border border-rose-200 bg-rose-50/70 p-6 max-w-lg mx-auto text-center my-8 shadow-sm">
    <div className="w-12 h-12 bg-rose-100 text-rose-600 rounded-xl flex items-center justify-center mx-auto mb-3">
      <AlertTriangle className="w-6 h-6" />
    </div>
    <h3 className="text-lg font-bold text-rose-900 mb-1">{title}</h3>
    <p className="text-sm text-rose-700 mb-4">{message}</p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="inline-flex items-center space-x-2 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-sm font-semibold transition-colors shadow-sm"
      >
        <RefreshCw className="w-4 h-4" />
        <span>Try Again</span>
      </button>
    )}
  </div>
);

export default ErrorMessage;
