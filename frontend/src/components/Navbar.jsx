import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  ShoppingBag,
  Sparkles,
  User as UserIcon,
  LogOut,
  History,
  ShieldCheck,
  Menu,
  X,
  Compass,
  Package,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import SearchBar from './SearchBar';

export const Navbar = () => {
  const { user, isAuthenticated, isAdmin, cartCount, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    setUserDropdownOpen(false);
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header className="sticky top-0 z-40 w-full glass-nav">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-2 sm:gap-4">
          {/* Logo */}
          <Link to={isAuthenticated ? '/' : '/login'} className="flex items-center space-x-2 sm:space-x-2.5 flex-shrink-0 group">
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-teal-400 flex items-center justify-center text-white shadow-md shadow-brand-500/25 group-hover:scale-105 transition-transform">
              <ShoppingBag className="w-4 h-4 sm:w-5 sm:h-5" />
            </div>
            <div>
              <span className="text-base sm:text-lg font-black tracking-tight text-slate-900 group-hover:text-brand-600 transition-colors">
                NexStore
              </span>
              <span className="hidden sm:inline-block ml-1 text-[10px] font-bold uppercase tracking-widest text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded-full border border-brand-200">
                Hybrid AI
              </span>
            </div>
          </Link>

          {/* Desktop Search (Only when authenticated) */}
          {isAuthenticated && (
            <div className="hidden md:flex flex-1 max-w-md mx-4">
              <SearchBar />
            </div>
          )}

          {/* Desktop Navigation Links (Only when authenticated) */}
          {isAuthenticated && (
            <nav className="hidden lg:flex items-center space-x-1">
              <Link
                to="/products"
                className={`px-3 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center space-x-1.5 ${
                  isActive('/products')
                    ? 'bg-brand-50 text-brand-700'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Compass className="w-3.5 h-3.5" />
                <span>Catalog</span>
              </Link>

              <Link
                to="/recommendations"
                className={`px-3 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center space-x-1.5 ${
                  isActive('/recommendations')
                    ? 'bg-brand-50 text-brand-700'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5 text-brand-500" />
                <span>Recommendations</span>
              </Link>

              <Link
                to="/orders"
                className={`px-3 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center space-x-1.5 ${
                  isActive('/orders')
                    ? 'bg-brand-50 text-brand-700'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Package className="w-3.5 h-3.5 text-brand-500" />
                <span>My Orders</span>
              </Link>

              {isAdmin && (
                <Link
                  to="/admin"
                  className={`px-3 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center space-x-1.5 ${
                    isActive('/admin')
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-indigo-600 hover:bg-indigo-50'
                  }`}
                >
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Admin</span>
                </Link>
              )}
            </nav>
          )}

          {/* Right Action Icons: Cart & Auth */}
          <div className="flex items-center space-x-3">
            {/* Cart Icon / Link (Only when authenticated) */}
            {isAuthenticated && (
              <Link
                to="/profile"
                className="relative p-2.5 rounded-xl text-slate-700 hover:text-brand-600 hover:bg-slate-100 transition-colors"
                title="Cart & Profile"
              >
                <ShoppingBag className="w-5 h-5" />
                {cartCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-brand-600 text-white text-[11px] font-bold flex items-center justify-center shadow-sm">
                    {cartCount > 9 ? '9+' : cartCount}
                  </span>
                )}
              </Link>
            )}

            {/* Authenticated User Menu */}
            {isAuthenticated ? (
              <div className="relative">
                <button
                  onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                  className="flex items-center space-x-1.5 sm:space-x-2 p-1 sm:p-1.5 pl-2 sm:pl-3 bg-slate-100 hover:bg-slate-200/80 rounded-xl transition-all border border-slate-200/60"
                >
                  <span className="text-xs font-semibold text-slate-800 max-w-[60px] sm:max-w-[100px] truncate">
                    {user?.name || user?.email?.split('@')[0]}
                  </span>
                  <div className="w-7 h-7 rounded-lg bg-brand-600 text-white flex items-center justify-center text-xs font-bold shadow-sm flex-shrink-0">
                    {user?.name?.[0]?.toUpperCase() || 'U'}
                  </div>
                </button>

                {/* Dropdown Menu */}
                {userDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-2xl border border-slate-200/80 py-2 z-50 animate-fade-in divide-y divide-slate-100">
                    <div className="px-4 py-2">
                      <p className="text-xs text-slate-400">Signed in as</p>
                      <p className="text-xs font-bold text-slate-900 truncate">{user?.email}</p>
                      <span className="inline-block mt-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                        {user?.role || 'user'}
                      </span>
                    </div>

                    <div className="py-1">
                      <Link
                        to="/profile"
                        onClick={() => setUserDropdownOpen(false)}
                        className="flex items-center space-x-2.5 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 hover:text-brand-600"
                      >
                        <UserIcon className="w-4 h-4" />
                        <span>My Profile & Cart</span>
                      </Link>

                      <Link
                        to="/history"
                        onClick={() => setUserDropdownOpen(false)}
                        className="flex items-center space-x-2.5 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 hover:text-brand-600"
                      >
                        <History className="w-4 h-4" />
                        <span>Interaction History</span>
                      </Link>

                      <Link
                        to="/recommendations"
                        onClick={() => setUserDropdownOpen(false)}
                        className="flex items-center space-x-2.5 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 hover:text-brand-600"
                      >
                        <Sparkles className="w-4 h-4 text-brand-500" />
                        <span>My Recommendations</span>
                      </Link>

                      <Link
                        to="/orders"
                        onClick={() => setUserDropdownOpen(false)}
                        className="flex items-center space-x-2.5 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 hover:text-brand-600"
                      >
                        <Package className="w-4 h-4 text-brand-500" />
                        <span>My Orders</span>
                      </Link>

                      {isAdmin && (
                        <Link
                          to="/admin"
                          onClick={() => setUserDropdownOpen(false)}
                          className="flex items-center space-x-2.5 px-4 py-2 text-xs font-semibold text-indigo-700 hover:bg-indigo-50"
                        >
                          <ShieldCheck className="w-4 h-4 text-indigo-600" />
                          <span>Admin Dashboard</span>
                        </Link>
                      )}
                    </div>

                    <div className="py-1">
                      <button
                        onClick={handleLogout}
                        className="w-full text-left flex items-center space-x-2.5 px-4 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50"
                      >
                        <LogOut className="w-4 h-4" />
                        <span>Log Out</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center space-x-1.5 sm:space-x-2">
                <Link
                  to="/login"
                  className="px-2.5 sm:px-3.5 py-1.5 sm:py-2 rounded-xl text-[11px] sm:text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-100 transition-colors whitespace-nowrap"
                >
                  Log In
                </Link>
                <Link
                  to="/register"
                  className="px-2.5 sm:px-4 py-1.5 sm:py-2 rounded-xl text-[11px] sm:text-xs font-semibold bg-brand-600 hover:bg-brand-700 active:scale-95 text-white shadow-sm shadow-brand-500/25 transition-all whitespace-nowrap"
                >
                  Create Account
                </Link>
              </div>
            )}

            {/* Mobile Hamburger Button (Only when authenticated) */}
            {isAuthenticated && (
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-2 text-slate-600 hover:text-slate-900 rounded-lg hover:bg-slate-100"
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            )}
          </div>
        </div>

        {/* Mobile Search Input (Only when authenticated) */}
        {isAuthenticated && (
          <div className="md:hidden py-2 pb-3">
            <SearchBar />
          </div>
        )}
      </div>

      {/* Mobile Drawer Menu (Authenticated) */}
      {isAuthenticated && mobileMenuOpen && (
        <div className="lg:hidden border-t border-slate-200 bg-white px-4 py-4 space-y-2 shadow-xl animate-fade-in">
          <Link
            to="/products"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-xl text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            Catalog
          </Link>
          <Link
            to="/recommendations"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-xl text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            My Recommendations
          </Link>
          <Link
            to="/orders"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-xl text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            My Orders
          </Link>
          {isAdmin && (
            <Link
              to="/admin"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-xl text-sm font-semibold text-indigo-700 bg-indigo-50"
            >
              Admin Dashboard
            </Link>
          )}

          <div className="pt-3 border-t border-slate-100 space-y-1">
            <Link
              to="/profile"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 text-sm text-slate-700"
            >
              Profile & Cart
            </Link>
            <Link
              to="/history"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 text-sm text-slate-700"
            >
              History
            </Link>
            <button
              onClick={() => {
                handleLogout();
                setMobileMenuOpen(false);
              }}
              className="w-full text-left px-3 py-2 text-sm text-rose-600"
            >
              Log Out
            </button>
          </div>
        </div>
      )}
    </header>
  );
};

export default Navbar;
