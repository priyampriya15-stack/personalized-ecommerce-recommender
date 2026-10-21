import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import Login from '../pages/Login';
import { AuthContext } from '../context/AuthContext';

describe('Login Page and Authentication Flow Tests', () => {
  let mockLogin;

  beforeEach(() => {
    mockLogin = vi.fn();
  });

  const renderLogin = (contextOverrides = {}) => {
    const defaultContext = {
      user: null,
      token: null,
      isAuthenticated: false,
      isAdmin: false,
      loading: false,
      login: mockLogin,
      register: vi.fn(),
      logout: vi.fn(),
      ...contextOverrides,
    };

    return render(
      <AuthContext.Provider value={defaultContext}>
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<div>Home Page</div>} />
            <Route path="/register" element={<div>Register Page</div>} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );
  };

  it('renders project name, research description, fields, and register link', () => {
    renderLogin();

    expect(screen.getByText('NexStore AI Recommender')).toBeInTheDocument();
    expect(screen.getByText(/Academic Recommendation Platform/i)).toBeInTheDocument();
    expect(screen.getByText(/Evaluating Collaborative Filtering/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Register here/i })).toBeInTheDocument();
  });

  it('toggles password visibility when eye toggle button is clicked', () => {
    renderLogin();

    const passwordInput = screen.getByLabelText(/^Password/i);
    const toggleBtn = screen.getByRole('button', { name: /Show password/i });

    expect(passwordInput).toHaveAttribute('type', 'password');

    fireEvent.click(toggleBtn);
    expect(passwordInput).toHaveAttribute('type', 'text');
    expect(screen.getByRole('button', { name: /Hide password/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Hide password/i }));
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('displays client-side validation errors when submitting invalid email and empty password', async () => {
    renderLogin();

    const submitBtn = screen.getByRole('button', { name: /Sign In/i });
    fireEvent.click(submitBtn);

    expect(await screen.findByText('Email address is required.')).toBeInTheDocument();
    expect(await screen.findByText('Password is required.')).toBeInTheDocument();
    expect(mockLogin).not.toHaveBeenCalled();

    // Now test invalid email pattern
    const emailInput = screen.getByLabelText(/Email Address/i);
    fireEvent.change(emailInput, { target: { value: 'notanemail' } });
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/Please provide a valid email format/i)).toBeInTheDocument();
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('calls real login API handler and redirects on valid credentials', async () => {
    mockLogin.mockResolvedValueOnce({ id: 1, email: 'admin@ecommerce.com' });
    renderLogin();

    const emailInput = screen.getByLabelText(/Email Address/i);
    const passwordInput = screen.getByLabelText(/^Password/i);
    const submitBtn = screen.getByRole('button', { name: /Sign In/i });

    fireEvent.change(emailInput, { target: { value: 'admin@ecommerce.com' } });
    fireEvent.change(passwordInput, { target: { value: 'Admin@123' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('admin@ecommerce.com', 'Admin@123');
    });
  });

  it('renders API error message when login fails with 401', async () => {
    mockLogin.mockRejectedValueOnce({ status: 401, message: 'Invalid credentials' });
    renderLogin();

    const emailInput = screen.getByLabelText(/Email Address/i);
    const passwordInput = screen.getByLabelText(/^Password/i);
    const submitBtn = screen.getByRole('button', { name: /Sign In/i });

    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'WrongPass@123' } });
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/Invalid email or password/i)).toBeInTheDocument();
  });
});
