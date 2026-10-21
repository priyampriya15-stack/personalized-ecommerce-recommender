import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShoppingBag,
  Sparkles,
  Database,
  Cpu,
  Layers,
  ShieldCheck,
  Brain,
  Flame,
  ArrowLeft,
  Lock,
  FileText,
  CheckCircle2,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export const About = () => {
  const { isAuthenticated } = useAuth();

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-16 space-y-12">
      {/* Navigation Breadcrumb */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <Link
          to={isAuthenticated ? '/' : '/login'}
          className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-600 hover:text-brand-600 transition-colors focus-visible:ring-2 focus-visible:ring-brand-500 rounded p-1"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>{isAuthenticated ? 'Back to Shop' : 'Back to Login'}</span>
        </Link>
        <span className="text-xs font-medium text-slate-400">
          Project Information & Architecture
        </span>
      </div>

      {/* Hero Header */}
      <header className="space-y-4">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-brand-50 border border-brand-200 text-brand-700 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5 text-brand-500" />
          <span>Production-Grade Architecture</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          NexStore AI
        </h1>
        <p className="text-lg font-medium text-brand-600">
          Personalized E-Commerce Recommendation System
        </p>
        <p className="text-sm sm:text-base text-slate-600 leading-relaxed max-w-3xl">
          Personalized product discovery powered by hybrid recommendation techniques. Combining
          latent collaborative filtering with semantic content analysis over verified Amazon catalog items.
        </p>
      </header>

      {/* Section 1: System Overview */}
      <section id="project" className="space-y-6 pt-4 border-t border-slate-200">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-brand-50 text-brand-600 rounded-lg">
            <Cpu className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">1. System Overview & Technology Stack</h2>
        </div>
        <p className="text-sm text-slate-600 leading-relaxed">
          NexStore AI is a full-stack, data-driven personalized e-commerce recommendation platform.
          The application combines real machine learning algorithms running on a Flask REST API with a modern React single-page frontend and a relational SQLite database.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 mb-1">Frontend</h3>
            <p className="text-xs text-slate-600">React 18, Vite, Tailwind CSS, Axios, Lucide React, Recharts</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 mb-1">Backend</h3>
            <p className="text-xs text-slate-600">Flask REST API, Flask-CORS, PyJWT, Werkzeug Security</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 mb-1">Database</h3>
            <p className="text-xs text-slate-600">SQLite with SQLAlchemy ORM, indexed transactional tables</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 mb-1">ML Engine</h3>
            <p className="text-xs text-slate-600">Scikit-Learn, Truncated SVD, TF-IDF Vectorizer, NumPy, SciPy</p>
          </div>
        </div>
      </section>

      {/* Section 2: Real Dataset */}
      <section id="dataset" className="space-y-6 pt-6 border-t border-slate-200">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-teal-50 text-teal-600 rounded-lg">
            <Database className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">2. Real Dataset & Catalog Specifications</h2>
        </div>
        <p className="text-sm text-slate-600 leading-relaxed">
          The catalog is built from the verified <strong>Amazon Reviews 2023</strong> public research dataset.
          All products, prices, descriptions, and user ratings reflect genuine historical interactions without simulated records or fabricated products.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-teal-50/50 border border-teal-200">
            <div className="text-2xl font-black text-teal-700 font-mono">8,337</div>
            <div className="text-xs font-semibold text-slate-700 mt-1">Verified Products</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Indexed in SQLite database</div>
          </div>
          <div className="p-4 rounded-xl bg-teal-50/50 border border-teal-200">
            <div className="text-2xl font-black text-teal-700 font-mono">3</div>
            <div className="text-xs font-semibold text-slate-700 mt-1">Catalog Categories</div>
            <div className="text-[11px] text-slate-500 mt-0.5">All Beauty, Appliances, Digital Music</div>
          </div>
          <div className="p-4 rounded-xl bg-teal-50/50 border border-teal-200">
            <div className="text-2xl font-black text-teal-700 font-mono">39,000+</div>
            <div className="text-xs font-semibold text-slate-700 mt-1">Training Interactions</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Dense core interaction history</div>
          </div>
        </div>
      </section>

      {/* Section 3: Recommendation Architecture */}
      <section id="architecture" className="space-y-6 pt-6 border-t border-slate-200">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
            <Brain className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">3. Recommendation Engine Architecture</h2>
        </div>
        <p className="text-sm text-slate-600 leading-relaxed">
          The platform operates four specialized recommendation engines serving real-time inferences:
        </p>
        <div className="space-y-3">
          <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm flex items-start space-x-3">
            <div className="w-2 h-2 rounded-full bg-brand-500 mt-2 flex-shrink-0" />
            <div>
              <h3 className="text-xs font-bold text-slate-900">Hybrid Linear Score Fusion (α=0.25)</h3>
              <p className="text-xs text-slate-600 mt-0.5">
                Calculates weighted linear combination: <code className="bg-slate-100 px-1 py-0.5 rounded text-[11px]">Score = α · S_CF + (1 - α) · S_CB</code>.
                Excludes previously interacted items and falls back smoothly for cold-start users.
              </p>
            </div>
          </div>
          <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm flex items-start space-x-3">
            <div className="w-2 h-2 rounded-full bg-teal-500 mt-2 flex-shrink-0" />
            <div>
              <h3 className="text-xs font-bold text-slate-900">Collaborative Filtering (Truncated SVD)</h3>
              <p className="text-xs text-slate-600 mt-0.5">
                Decomposes the user-item interaction matrix into <code className="bg-slate-100 px-1 py-0.5 rounded text-[11px]">k=30</code> latent factors to uncover latent customer affinity patterns.
              </p>
            </div>
          </div>
          <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm flex items-start space-x-3">
            <div className="w-2 h-2 rounded-full bg-amber-500 mt-2 flex-shrink-0" />
            <div>
              <h3 className="text-xs font-bold text-slate-900">Content-Based Filtering (TF-IDF 5,000 Features)</h3>
              <p className="text-xs text-slate-600 mt-0.5">
                Transforms clean product titles, descriptions, and category metadata into sublinear TF-IDF vectors, measuring cosine similarity against user taste profiles.
              </p>
            </div>
          </div>
          <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm flex items-start space-x-3">
            <div className="w-2 h-2 rounded-full bg-indigo-500 mt-2 flex-shrink-0" />
            <div>
              <h3 className="text-xs font-bold text-slate-900">Bayesian Popularity Baseline</h3>
              <p className="text-xs text-slate-600 mt-0.5">
                Computes Bayesian weighted average review scores with smoothing parameters (<code className="bg-slate-100 px-1 py-0.5 rounded text-[11px]">m=5, C=4.22</code>) to ensure fair ranking.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Section 4: Privacy & Data Policy */}
      <section id="privacy" className="space-y-6 pt-6 border-t border-slate-200">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">4. Privacy Policy & Data Handling</h2>
        </div>
        <div className="p-5 rounded-2xl bg-emerald-50/40 border border-emerald-200/80 space-y-3 text-xs text-slate-700 leading-relaxed">
          <div className="flex items-center space-x-2 font-bold text-emerald-800 text-sm">
            <Lock className="w-4 h-4" />
            <span>Local Database Storage & User Privacy</span>
          </div>
          <p>
            NexStore AI stores all application data locally in the application&apos;s SQLite database.
            No personal data is transmitted to external analytics providers, advertising platforms, or third-party trackers.
          </p>
          <ul className="space-y-1.5 list-disc list-inside text-slate-600 pt-1">
            <li>Passwords are securely hashed using Werkzeug PBKDF2 with unique salts.</li>
            <li>Authentication is managed through standard stateless JSON Web Tokens (JWT).</li>
            <li>User orders, cart contents, and interaction histories are isolated strictly per authenticated user.</li>
          </ul>
        </div>
      </section>

      {/* Section 5: Terms of Use */}
      <section id="terms" className="space-y-6 pt-6 border-t border-slate-200">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-slate-100 text-slate-600 rounded-lg">
            <FileText className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">5. Terms of Use</h2>
        </div>
        <p className="text-xs text-slate-600 leading-relaxed">
          This system is developed as an educational, technical demonstration and research platform for personalized recommendation algorithms.
          Product records originate from the Amazon Reviews 2023 dataset. Checkout workflows and order tracking operate on local transactional SQLite tables.
        </p>
        <div className="pt-2 flex flex-wrap gap-4">
          <Link
            to={isAuthenticated ? '/products' : '/login'}
            className="inline-flex items-center space-x-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-500 text-white rounded-xl text-xs font-bold shadow-sm transition-colors"
          >
            <ShoppingBag className="w-4 h-4" />
            <span>{isAuthenticated ? 'Browse Catalog' : 'Sign In to Account'}</span>
          </Link>
        </div>
      </section>
    </div>
  );
};

export default About;
