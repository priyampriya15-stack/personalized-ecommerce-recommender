import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProductCard from '../components/ProductCard';
import EmptyState from '../components/EmptyState';
import ErrorMessage from '../components/ErrorMessage';
import Toast from '../components/Toast';
import CategoryFilter from '../components/CategoryFilter';
import SearchBar from '../components/SearchBar';
import RecommendationSection from '../components/RecommendationSection';
import { AuthProvider } from '../context/AuthContext';

// Helper to wrap components in BrowserRouter and AuthProvider
const renderWithProviders = (ui) => {
  return render(
    <AuthProvider>
      <BrowserRouter>{ui}</BrowserRouter>
    </AuthProvider>
  );
};

describe('Frontend Component Tests', () => {
  it('renders ProductCard with correct product details', () => {
    const mockProduct = {
      id: 42,
      title: 'Premium Wireless Headphones',
      category: 'Appliances',
      price: 99.99,
      rating: 4.8,
      algorithm: 'hybrid',
      score: 0.85,
      explanation: 'Matches your preferences in audio equipment',
    };

    renderWithProviders(<ProductCard product={mockProduct} />);

    expect(screen.getByText('Premium Wireless Headphones')).toBeInTheDocument();
    expect(screen.getByText('Appliances')).toBeInTheDocument();
    expect(screen.getByText('$99.99')).toBeInTheDocument();
    expect(screen.getByText('4.8')).toBeInTheDocument();
    expect(screen.getByText(/Matches your preferences/)).toBeInTheDocument();
  });

  it('renders EmptyState with custom title, description, and action button', () => {
    const handleAction = vi.fn();
    renderWithProviders(
      <EmptyState
        title="Custom Empty Title"
        description="Detailed empty description message"
        actionText="Click Me"
        onAction={handleAction}
      />
    );

    expect(screen.getByText('Custom Empty Title')).toBeInTheDocument();
    expect(screen.getByText('Detailed empty description message')).toBeInTheDocument();
    const btn = screen.getByText('Click Me');
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(handleAction).toHaveBeenCalledTimes(1);
  });

  it('renders ErrorMessage with retry action', () => {
    const handleRetry = vi.fn();
    renderWithProviders(
      <ErrorMessage
        title="Connection Timed Out"
        message="Backend server did not respond"
        onRetry={handleRetry}
      />
    );

    expect(screen.getByText('Connection Timed Out')).toBeInTheDocument();
    expect(screen.getByText('Backend server did not respond')).toBeInTheDocument();
    const retryBtn = screen.getByText('Try Again');
    fireEvent.click(retryBtn);
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });

  it('renders Toast and handles close button click', () => {
    const handleClose = vi.fn();
    renderWithProviders(
      <Toast message="Item added to cart!" type="success" onClose={handleClose} />
    );

    expect(screen.getByText('Item added to cart!')).toBeInTheDocument();
    const closeBtn = screen.getByRole('button');
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('renders CategoryFilter and triggers category selection', () => {
    const handleSelect = vi.fn();
    renderWithProviders(
      <CategoryFilter
        categories={['All Beauty', 'Appliances', 'Digital Music']}
        selectedCategory="Appliances"
        onSelectCategory={handleSelect}
      />
    );

    expect(screen.getByText('All Beauty')).toBeInTheDocument();
    expect(screen.getByText('Appliances')).toBeInTheDocument();
    expect(screen.getByText('Digital Music')).toBeInTheDocument();

    fireEvent.click(screen.getByText('All Beauty'));
    expect(handleSelect).toHaveBeenCalledWith('All Beauty');
  });

  it('renders SearchBar and submits query', () => {
    const handleSearch = vi.fn();
    renderWithProviders(<SearchBar onSearch={handleSearch} />);

    const input = screen.getByPlaceholderText(/Search 8,300\+ products/);
    fireEvent.change(input, { target: { value: 'headphones' } });
    expect(input.value).toBe('headphones');

    const searchBtn = screen.getByRole('button', { name: /search/i });
    fireEvent.click(searchBtn);
    expect(handleSearch).toHaveBeenCalledWith('headphones');
  });

  it('renders RecommendationSection with algorithm badge', () => {
    const mockRecs = [
      {
        id: 101,
        title: 'Shampoo Bar Lavender',
        category: 'All Beauty',
        price: 14.5,
        rating: 4.9,
      },
    ];

    renderWithProviders(
      <RecommendationSection
        title="Top Recommendations"
        subtitle="Ranked dynamically"
        algorithm="hybrid"
        recommendations={mockRecs}
      />
    );

    expect(screen.getByText('Top Recommendations')).toBeInTheDocument();
    expect(screen.getByText('Hybrid (CF + CB)')).toBeInTheDocument();
    expect(screen.getByText('Shampoo Bar Lavender')).toBeInTheDocument();
  });

  it('renders Footer component with brand, catalog links, and engine algorithms', async () => {
    const { Footer } = await import('../components/Footer');

    renderWithProviders(<Footer />);

    expect(screen.getAllByText('NexStore AI').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Personalized E-Commerce Recommendation System/i)).toBeInTheDocument();
    expect(screen.getByText(/Personalized product discovery powered by hybrid recommendation techniques/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /All Products/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^Categories$/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Popular Products/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Top Recommendations/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Search Catalog/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^About$/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Project Information/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^Privacy$/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^Terms$/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^Login$/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^Register$/i })).toBeInTheDocument();
    expect(screen.getByText(/Hybrid Linear Score Fusion/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Collaborative Filtering/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Content-Based Filtering/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Bayesian Popularity Baseline/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/© 2026/i)).toBeInTheDocument();
    expect(screen.getByText(/All rights reserved/i)).toBeInTheDocument();
  });
});

