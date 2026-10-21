import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ShoppingBag,
  Sparkles,
  Cpu,
  Layers,
  ShieldCheck,
  Database,
  Info,
  CheckCircle2,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import productService from '../services/productService';

export const Footer = () => {
  const { isAuthenticated, isAdmin } = useAuth();
  const [stats, setStats] = useState({ totalProducts: null, totalCategories: null });

  useEffect(() => {
    let isMounted = true;
    const fetchCatalogStats = async () => {
      try {
        const res = await productService.getCategories();
        if (isMounted && res && res.data && Array.isArray(res.data)) {
          const totalProducts = res.data.reduce((acc, cat) => acc + (cat.count || 0), 0);
          const totalCategories = res.data.length;
          setStats({ totalProducts, totalCategories });
        }
      } catch {
        // Fallback: leave null if API unavailable; do NOT fabricate data
      }
    };

    fetchCatalogStats();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <footer
      role="contentinfo"
      aria-label="Site Footer"
      className="mt-20 border-t border-slate-200/80 bg-white text-slate-600 text-xs transition-colors"
    >
      <h2 className="sr-only">Footer Navigation and System Information</h2>

      {/* Main Footer Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 lg:py-16">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-8 lg:gap-8">

          {/* Section 1: Brand & Live Catalog Telemetry */}
          <div className="sm:col-span-2 lg:col-span-3 space-y-4">
            <Link
              to={isAuthenticated ? '/' : '/login'}
              className="inline-flex items-center space-x-2.5 group focus-visible:ring-2 focus-visible:ring-brand-500 rounded-lg focus:outline-none"
              aria-label="NexStore AI Home"
            >
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-teal-400 flex items-center justify-center text-white shadow-md shadow-brand-500/20 group-hover:scale-105 transition-transform flex-shrink-0">
                <ShoppingBag className="w-4 h-4" />
              </div>
              <div className="flex flex-col">
                <span className="text-base font-black tracking-tight text-slate-900 group-hover:text-brand-600 transition-colors">
                  NexStore AI
                </span>
                <span className="text-[10px] font-semibold text-brand-600 tracking-wide uppercase">
                  Personalized E-Commerce Recommendation System
                </span>
              </div>
            </Link>

            <p className="text-xs text-slate-500 leading-relaxed">
              Personalized product discovery powered by hybrid recommendation techniques.
            </p>

            {/* Real Catalog Telemetry (Dynamically fetched from SQLite, never hardcoded) */}
            {stats.totalProducts !== null && (
              <div className="pt-1 flex flex-wrap items-center gap-2.5" aria-label="Catalog Statistics">
                <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200/80 text-[11px] font-medium text-slate-700">
                  <Database className="w-3.5 h-3.5 text-brand-600" aria-hidden="true" />
                  <span>
                    <strong className="text-slate-900 font-bold font-mono">
                      {stats.totalProducts.toLocaleString()}+
                    </strong>{' '}
                    Products
                  </span>
                </div>
                <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200/80 text-[11px] font-medium text-slate-700">
                  <Layers className="w-3.5 h-3.5 text-teal-600" aria-hidden="true" />
                  <span>
                    <strong className="text-slate-900 font-bold font-mono">
                      {stats.totalCategories}
                    </strong>{' '}
                    Categories
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Section 2: Shop & Catalog Navigation */}
          <div className="space-y-3 lg:col-span-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Shop
            </h3>
            <ul className="space-y-2 text-slate-600">
              <li>
                <Link
                  to="/products"
                  className="hover:text-brand-600 transition-colors focus-visible:ring-1 focus-visible:ring-brand-500 rounded focus:outline-none block py-0.5"
                >
                  All Products
                </Link>
              </li>
              <li>
                <Link
                  to="/products"
                  className="hover:text-brand-600 transition-colors focus-visible:ring-1 focus-visible:ring-brand-500 rounded focus:outline-none block py-0.5"
                >
                  Categories
                </Link>
              </li>
              <li>
                <Link
                  to="/recommendations"
                  className="hover:text-brand-600 transition-colors focus-visible:ring-1 focus-visible:ring-brand-500 rounded focus:outline-none block py-0.5"
                >
                  Popular Products
                </Link>
              </li>
              <li>
                <Link
                  to="/recommendations"
                  className="hover:text-brand-600 transition-colors focus-visible:ring-1 focus-visible:ring-brand-500 rounded focus:outline-none block py-0.5"
                >
                  Top Recommendations
                </Link>
              </li>
              <li>
                <Link
                  to="/search"
                  className="hover:text-brand-600 transition-colors focus-visible:ring-1 focus-visible:ring-brand-500 rounded focus:outline-none block py-0.5"
                >
                  Search Catalog
                </Link>
              </li>
            </ul>
          </div>

          {/* Section 3: Account (Conditional on Authentication) */}
          <div className="space-y-3 lg:col-span-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Account
            </h3>
            <ul className="space-y-2 text-slate-600">
              {isAuthenticated ? (
                <>
                  <li>
                    <Link
                      to="/profile"
                      className="hover:text-brand-600 transition-colors focus-visible:ring-1 focus-visible:ring-brand-500 rounded focus:outline-none block py-0.5"
                    >
                      Profile
                    </Link>
                  </li>
                  <li>
                    <Link
                      to="/recommendations"
                      className="hover:text-brand-600 transition-colors focus-visible:ring-1 focus-visible:ring-brand-500 rounded focus:outline-none block py-0.5"
                    >
                      My Recommendations
                    </Link>
                  </li>
                  <li>
                    <Link
                      to="/orders"
                      className="hover:text-brand-600 transition-colors focus-visible:ring-1 focus-visible:ring-brand-500 rounded focus:outline-none block py-0.5"
                    >
                      My Orders
                    </Link>
                  </li>
                  <li>
                    <Link
                      to="/history"
                      className="hover:text-brand-600 transition-colors focus-visible:ring-1 focus-visible:ring-brand-500 rounded focus:outline-none block py-0.5"
                    >
                      Interaction History
                    </Link>
                  </li>
                  <li>
                    <Link
                      to="/profile"
                      className="hover:text-brand-600 transition-colors focus-visible:ring-1 focus-visible:ring-brand-500 rounded focus:outline-none block py-0.5"
                    >
                      Cart
                    </Link>
                  </li>
                  {isAdmin && (
                    <li>
                      <Link
                        to="/admin"
                        className="text-indigo-600 hover:text-indigo-700 font-semibold transition-colors focus-visible:ring-1 focus-visible:ring-indigo-500 rounded focus:outline-none inline-flex items-center space-x-1 py-0.5"
                      >
                        <ShieldCheck className="w-3.5 h-3.5" aria-hidden="true" />
                        <span>Admin Telemetry</span>
                      </Link>
                    </li>
                  )}
                </>
              ) : (
                <>
                  <li>
                    <Link
                      to="/login"
                      className="hover:text-brand-600 transition-colors focus-visible:ring-1 focus-visible:ring-brand-500 rounded focus:outline-none block py-0.5"
                    >
                      Login
                    </Link>
                  </li>
                  <li>
                    <Link
                      to="/register"
                      className="hover:text-brand-600 transition-colors focus-visible:ring-1 focus-visible:ring-brand-500 rounded focus:outline-none block py-0.5"
                    >
                      Register
                    </Link>
                  </li>
                </>
              )}
            </ul>
          </div>

          {/* Section 4: Support / Information (Only verified real routes) */}
          <div className="space-y-3 lg:col-span-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Information
            </h3>
            <ul className="space-y-2 text-slate-600">
              <li>
                <Link
                  to="/about"
                  className="hover:text-brand-600 transition-colors focus-visible:ring-1 focus-visible:ring-brand-500 rounded focus:outline-none block py-0.5"
                >
                  About
                </Link>
              </li>
              <li>
                <Link
                  to="/about#project"
                  className="hover:text-brand-600 transition-colors focus-visible:ring-1 focus-visible:ring-brand-500 rounded focus:outline-none block py-0.5"
                >
                  Project Information
                </Link>
              </li>
              <li>
                <Link
                  to="/about#privacy"
                  className="hover:text-brand-600 transition-colors focus-visible:ring-1 focus-visible:ring-brand-500 rounded focus:outline-none block py-0.5"
                >
                  Privacy
                </Link>
              </li>
              <li>
                <Link
                  to="/about#terms"
                  className="hover:text-brand-600 transition-colors focus-visible:ring-1 focus-visible:ring-brand-500 rounded focus:outline-none block py-0.5"
                >
                  Terms
                </Link>
              </li>
            </ul>
          </div>

          {/* Section 5: Recommendation System Information (Research / Engine) */}
          <div className="space-y-3 lg:col-span-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center space-x-1.5">
              <Cpu className="w-3.5 h-3.5 text-brand-600" aria-hidden="true" />
              <span>Recommendation Engine</span>
            </h3>
            <ul className="space-y-1.5 text-[11px] text-slate-600">
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-brand-500 flex-shrink-0" aria-hidden="true" />
                <span>Hybrid Linear Score Fusion (α=0.25)</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-500 flex-shrink-0" aria-hidden="true" />
                <span>Collaborative Filtering (Truncated SVD)</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0" aria-hidden="true" />
                <span>Content-Based Filtering (TF-IDF 5k)</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 flex-shrink-0" aria-hidden="true" />
                <span>Bayesian Popularity Baseline</span>
              </li>
            </ul>
            <p className="text-[10px] text-slate-400 pt-0.5 leading-normal">
              Real-time inference running on Flask REST backend with SQLite persistence.
            </p>
          </div>
        </div>
      </div>

      {/* Footer Bottom Bar */}
      <div className="border-t border-slate-100 bg-slate-50/70 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-center sm:text-left">
          <p className="text-[11px] text-slate-500">
            © 2026 <strong className="text-slate-700 font-semibold">NexStore AI</strong>. All rights reserved.
          </p>
          <p className="text-[11px] text-slate-400 font-mono flex flex-wrap items-center justify-center sm:justify-end gap-x-2 gap-y-1">
            <span>Powered by React</span>
            <span>•</span>
            <span>Flask</span>
            <span>•</span>
            <span>Machine Learning</span>
            <span>•</span>
            <span>SQLite</span>
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
