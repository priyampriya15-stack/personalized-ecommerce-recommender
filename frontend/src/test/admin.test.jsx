import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AdminDashboard from '../pages/AdminDashboard';
import * as useAuthModule from '../hooks/useAuth';
import adminService from '../services/adminService';

// Mock adminService
vi.mock('../services/adminService', () => ({
  default: {
    getAnalytics: vi.fn(),
    getModelMetrics: vi.fn(),
    updateRecommendationSettings: vi.fn(),
  },
}));

const mockAnalyticsData = {
  overview: {
    total_users: 5,
    active_users: 3,
    total_products: 8337,
    total_interactions: 27,
    total_recommendation_calls: 21,
    catalog_avg_rating: 4.35,
    interacted_products_count: 24,
    current_hybrid_alpha: 0.25,
  },
  users: {
    total: 5,
    by_role: { admin: 1, user: 4 },
    active_count: 3,
    recent: [
      { id: 1, name: 'System Admin', email: 'admin@ecommerce.com', role: 'admin', created_at: '2026-10-20 17:21:57' },
    ],
  },
  products: {
    total: 8337,
    by_category: { 'All Beauty': 1499, 'Appliances': 1499, 'Digital Music': 5339 },
    avg_rating: 4.35,
    interacted_count: 24,
    top_interacted: [
      { id: 33, title: 'Enjoy VOLUMIZING ELIXIR', category: 'All Beauty', rating: 5.0, price: 21.0, interaction_count: 3 },
    ],
  },
  categories_detailed: [
    { category: 'All Beauty', product_count: 1499, interaction_count: 7, avg_rating: 3.93 },
    { category: 'Appliances', product_count: 1499, interaction_count: 0, avg_rating: 4.14 },
    { category: 'Digital Music', product_count: 5339, interaction_count: 20, avg_rating: 4.53 },
  ],
  category_statistics: { 'All Beauty': 1499, 'Appliances': 1499, 'Digital Music': 5339 },
  interaction_breakdown: { rating: 22, like: 2, view: 1, cart: 1, purchase: 1 },
  interactions_timeline: [{ date: '2026-10-20', count: 7 }],
  recent_interactions: [
    {
      id: 27,
      user_id: 2,
      user_email: 'demo@ecommerce.com',
      product_id: 33,
      product_title: 'Enjoy VOLUMIZING ELIXIR',
      category: 'All Beauty',
      interaction_type: 'like',
      rating: null,
      timestamp: '2026-10-20 18:00:00',
    },
  ],
  algorithm_usage: { content_based: 18, popularity: 3 },
  recent_recommendation_logs: [
    {
      id: 21,
      user_id: 5,
      user_email: 'marcus.vance@example.com',
      product_id: 752,
      product_title: '16 Pieces Parting Comb Set',
      algorithm: 'content_based',
      score: 0.2477,
      created_at: '2026-10-20 18:27:09',
    },
  ],
  system_status: {
    database_connected: true,
    database_engine: 'SQLite',
    database_size_bytes: 5107712,
    models_loaded: { popularity: true, collaborative: true, content_based: true, hybrid: true },
    current_hybrid_alpha: 0.25,
  },
};

const mockModelMetricsData = {
  model_comparison: [
    {
      Model: 'Hybrid (alpha=0.25)',
      K: 10,
      'Precision@K': 0.02156,
      'Recall@K': 0.20995,
      'F1@K': 0.03901,
      'NDCG@K': 0.14199,
      'MAP@K': 0.12038,
      'Coverage@K (%)': 41.63,
      'Diversity@K': 0.5945,
    },
  ],
  k10_models: [
    {
      Model: 'Hybrid',
      K: 10,
      'Precision@K': 0.02156,
      'Recall@K': 0.20995,
      'F1@K': 0.03901,
      'NDCG@K': 0.14199,
      'MAP@K': 0.12038,
      'Coverage@K (%)': 41.63,
      'Diversity@K': 0.5945,
    },
  ],
  alpha_experiments: [
    {
      Model: 'Hybrid (alpha=0.25)',
      K: 10,
      Alpha: 0.25,
      'Precision@K': 0.02156,
      'Recall@K': 0.20995,
      'NDCG@K': 0.14199,
      'Coverage@K (%)': 41.63,
      'Diversity@K': 0.5945,
    },
  ],
  best_metrics_k10: {
    'Recall@K': { model: 'Hybrid (alpha=0.25)', value: 0.20995 },
    'Precision@K': { model: 'Hybrid (alpha=0.25)', value: 0.02156 },
    'NDCG@K': { model: 'Hybrid (alpha=0.25)', value: 0.14199 },
    'Diversity@K': { model: 'Popularity', value: 0.9402 },
  },
};

describe('AdminDashboard Page Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('blocks non-admin users with Admin Access Required banner', () => {
    vi.spyOn(useAuthModule, 'useAuth').mockReturnValue({
      user: { id: 2, name: 'Normal User', role: 'user' },
      isAdmin: false,
      isAuthenticated: true,
    });

    render(
      <BrowserRouter>
        <AdminDashboard />
      </BrowserRouter>
    );

    expect(screen.getByText('Admin Access Required')).toBeInTheDocument();
    expect(
      screen.getByText(/strictly restricted to authenticated platform administrators/)
    ).toBeInTheDocument();
  });

  it('renders telemetry and KPI cards for admin user with real data', async () => {
    vi.spyOn(useAuthModule, 'useAuth').mockReturnValue({
      user: { id: 1, name: 'System Admin', role: 'admin' },
      isAdmin: true,
      isAuthenticated: true,
    });

    adminService.getAnalytics.mockResolvedValue({ data: mockAnalyticsData });
    adminService.getModelMetrics.mockResolvedValue({ data: mockModelMetricsData });

    render(
      <BrowserRouter>
        <AdminDashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Admin Telemetry & Model Control')).toBeInTheDocument();
    });

    // Verify real counts rendered in KPIs
    expect(screen.getByText('8,337')).toBeInTheDocument();
    expect(screen.getByText('3 with interactions')).toBeInTheDocument();
    expect(screen.getByText('24 unique items')).toBeInTheDocument();
    expect(screen.getByText('SQLite Database')).toBeInTheDocument();
  });

  it('allows admin to update hybrid alpha parameter and reloads telemetry', async () => {
    vi.spyOn(useAuthModule, 'useAuth').mockReturnValue({
      user: { id: 1, name: 'System Admin', role: 'admin' },
      isAdmin: true,
      isAuthenticated: true,
    });

    adminService.getAnalytics.mockResolvedValue({ data: mockAnalyticsData });
    adminService.getModelMetrics.mockResolvedValue({ data: mockModelMetricsData });
    adminService.updateRecommendationSettings.mockResolvedValue({
      data: { current_hybrid_alpha: 0.4, collaborative_weight: 0.4, content_weight: 0.6 },
    });

    render(
      <BrowserRouter>
        <AdminDashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Save Live α')).toBeInTheDocument();
    });

    const submitBtn = screen.getByText('Save Live α');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(adminService.updateRecommendationSettings).toHaveBeenCalledWith(0.25);
    });
  });

  it('switches between tabs to show model evaluation and activity tables', async () => {
    vi.spyOn(useAuthModule, 'useAuth').mockReturnValue({
      user: { id: 1, name: 'System Admin', role: 'admin' },
      isAdmin: true,
      isAuthenticated: true,
    });

    adminService.getAnalytics.mockResolvedValue({ data: mockAnalyticsData });
    adminService.getModelMetrics.mockResolvedValue({ data: mockModelMetricsData });

    render(
      <BrowserRouter>
        <AdminDashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Platform Overview')).toBeInTheDocument();
    });

    // Switch to Model Evaluation tab
    const modelTabBtn = screen.getByText('Model Evaluation (Phase 3)');
    fireEvent.click(modelTabBtn);

    expect(screen.getByText(/Offline Model Comparison at K=10/)).toBeInTheDocument();
    expect(screen.getByText('Phase 3 Offline Benchmark Results Matrix')).toBeInTheDocument();

    // Switch to Activity & Catalog Tables tab
    const tablesTabBtn = screen.getByText('Activity & Catalog Tables');
    fireEvent.click(tablesTabBtn);

    expect(screen.getByText('Top Interacted Catalog Products')).toBeInTheDocument();
    expect(screen.getByText('Recent User Interaction Events')).toBeInTheDocument();
  });

  it('renders ErrorMessage when API fails and handles retry', async () => {
    vi.spyOn(useAuthModule, 'useAuth').mockReturnValue({
      user: { id: 1, name: 'System Admin', role: 'admin' },
      isAdmin: true,
      isAuthenticated: true,
    });

    adminService.getAnalytics.mockRejectedValue(new Error('Network error: SQLite locked'));
    adminService.getModelMetrics.mockResolvedValue({ data: mockModelMetricsData });

    render(
      <BrowserRouter>
        <AdminDashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Network error: SQLite locked')).toBeInTheDocument();
    });

    const retryBtn = screen.getByText('Try Again');
    expect(retryBtn).toBeInTheDocument();
  });
});
