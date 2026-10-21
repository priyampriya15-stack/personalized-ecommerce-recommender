import React from 'react';
import { Link } from 'react-router-dom';
import { Compass, ArrowRight } from 'lucide-react';

export const NotFound = () => (
  <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4 py-16">
    <div className="w-16 h-16 rounded-3xl bg-slate-100 flex items-center justify-center text-slate-500 mb-4 border border-slate-200">
      <Compass className="w-8 h-8 animate-spin" style={{ animationDuration: '8s' }} />
    </div>
    <span className="text-4xl font-black text-brand-600 mb-1">404</span>
    <h1 className="text-2xl font-extrabold text-slate-900 mb-2">Page Not Found</h1>
    <p className="text-sm text-slate-500 max-w-sm mb-6">
      The page you were looking for doesn't exist or may have been relocated.
    </p>
    <Link
      to="/"
      className="inline-flex items-center space-x-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
    >
      <span>Return to Home</span>
      <ArrowRight className="w-4 h-4" />
    </Link>
  </div>
);

export default NotFound;
