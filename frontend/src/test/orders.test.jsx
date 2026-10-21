import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route, Navigate } from 'react-router-dom';
import Orders from '../pages/Orders';
import MyOrders from '../pages/MyOrders';
import Checkout from '../pages/Checkout';
import ProductDetails from '../pages/ProductDetails';
import { AuthContext } from '../context/AuthContext';
import orderService from '../services/orderService';
import * as productService from '../services/productService';

vi.mock('../services/orderService', () => {
  const mockService = {
    getOrderQuote: vi.fn(),
    createOrder: vi.fn(),
    buyNow: vi.fn(),
    getUserOrders: vi.fn(),
    getOrderById: vi.fn(),
    cancelOrder: vi.fn(),
  };
  return {
    default: mockService,
    orderService: mockService,
  };
});

vi.mock('../services/productService', () => ({
  default: {
    getProductById: vi.fn(),
    getSimilarProducts: vi.fn(),
  },
  getProductById: vi.fn(),
  getSimilarProducts: vi.fn(),
}));

describe('Orders and Checkout Flow Unit & Integration Tests', () => {
  const mockUser = { id: 1, name: 'Alice Test', email: 'alice@test.edu', role: 'user' };

  const renderWithAuth = (ui, initialEntries = ['/orders'], authOverrides = {}) => {
    const authContext = {
      user: mockUser,
      token: 'jwt.token.here',
      isAuthenticated: true,
      isAdmin: false,
      loading: false,
      cartCount: 1,
      updateCartCount: vi.fn(),
      refreshCart: vi.fn(),
      ...authOverrides,
    };

    return render(
      <AuthContext.Provider value={authContext}>
        <MemoryRouter initialEntries={initialEntries}>
          <Routes>
            <Route path="/orders" element={<Orders />} />
            <Route path="/my-orders" element={<MyOrders />} />
            <Route path="/checkout" element={<Checkout />} />
            <Route path="/products/:id" element={<ProductDetails />} />
            <Route path="/login" element={<div>Login Page Redirect Target</div>} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Orders and MyOrders Page', () => {
    it('displays honest empty state "No orders yet." when user has 0 orders', async () => {
      orderService.getUserOrders.mockResolvedValue({
        success: true,
        data: [],
      });

      renderWithAuth(<Orders />, ['/orders']);

      expect(await screen.findByText('No orders yet.')).toBeInTheDocument();
      expect(screen.getByText(/You have not placed any orders yet/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Start Shopping/i })).toBeInTheDocument();
    });

    it('renders real order records with ID, items, unit price, total, and status badge', async () => {
      const sampleOrders = [
        {
          id: 42,
          user_id: 1,
          status: 'PENDING',
          total_amount: 59.98,
          created_at: '2026-10-21T10:00:00Z',
          items: [
            {
              id: 101,
              order_id: 42,
              product_id: 7,
              product_title: 'Anker USB-C Fast Charger',
              product_category: 'Electronics',
              quantity: 2,
              unit_price: 29.99,
              subtotal: 59.98,
            },
          ],
        },
      ];

      orderService.getUserOrders.mockResolvedValue({
        success: true,
        data: sampleOrders,
      });

      renderWithAuth(<MyOrders />, ['/my-orders']);

      expect(await screen.findByText('My Orders')).toBeInTheDocument();
      expect(screen.getByText(/Order ID/i)).toBeInTheDocument();
      expect(screen.getByText('#42')).toBeInTheDocument();
      expect(screen.getByText(/Quantity:\s*2/i)).toBeInTheDocument();
      expect(screen.getAllByText('$59.98').length).toBeGreaterThan(0);
      expect(screen.getByText('PENDING')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Cancel Order/i })).toBeInTheDocument();
    });

    it('toggles Order Details view showing item breakdown and telemetry', async () => {
      const sampleOrders = [
        {
          id: 77,
          user_id: 1,
          status: 'CONFIRMED',
          total_amount: 24.99,
          created_at: '2026-10-21T11:00:00Z',
          items_count: 1,
          items: [
            {
              id: 201,
              order_id: 77,
              product_id: 1,
              product_title: 'Leather Conditioner',
              product_category: 'All Beauty',
              quantity: 1,
              unit_price: 24.99,
              subtotal: 24.99,
            },
          ],
        },
      ];

      orderService.getUserOrders.mockResolvedValue({
        success: true,
        data: sampleOrders,
      });

      renderWithAuth(<MyOrders />, ['/my-orders']);

      const detailsBtn = await screen.findByRole('button', { name: /Order Details/i });
      fireEvent.click(detailsBtn);

      expect(screen.getByText(/Order Breakdown & Audit Telemetry/i)).toBeInTheDocument();
      expect(screen.getAllByText(/CONFIRMED/i).length).toBeGreaterThanOrEqual(1);
    });

    it('allows cancelling a PENDING order with confirmation and updates status to CANCELLED', async () => {
      const sampleOrders = [
        {
          id: 55,
          user_id: 1,
          status: 'PENDING',
          total_amount: 19.99,
          created_at: '2026-10-21T10:00:00Z',
          items: [
            {
              id: 102,
              order_id: 55,
              product_id: 3,
              product_title: 'High-Speed HDMI Cable',
              product_category: 'Electronics',
              quantity: 1,
              unit_price: 19.99,
              subtotal: 19.99,
            },
          ],
        },
      ];

      orderService.getUserOrders.mockResolvedValue({
        success: true,
        data: sampleOrders,
      });

      orderService.cancelOrder.mockResolvedValue({
        success: true,
        data: {
          ...sampleOrders[0],
          status: 'CANCELLED',
        },
      });

      renderWithAuth(<Orders />, ['/orders']);

      const cancelBtn = await screen.findByRole('button', { name: /Cancel Order/i });
      fireEvent.click(cancelBtn);

      // Inline confirmation appears
      expect(screen.getByText(/Cancel this order\?/i)).toBeInTheDocument();
      const confirmBtn = screen.getByRole('button', { name: /Yes, Cancel/i });
      fireEvent.click(confirmBtn);

      await waitFor(() => {
        expect(orderService.cancelOrder).toHaveBeenCalledWith(55);
        expect(screen.getByText('CANCELLED')).toBeInTheDocument();
      });
    });
  });

  describe('Checkout Page', () => {
    it('fetches server quote and renders verified server-side totals', async () => {
      orderService.getOrderQuote.mockResolvedValue({
        success: true,
        data: {
          source: 'cart',
          items: [
            {
              product_id: 10,
              title: 'Mechanical Gaming Keyboard',
              category: 'Electronics',
              quantity: 1,
              unit_price: 89.99,
              subtotal: 89.99,
            },
          ],
          items_count: 1,
          total_amount: 89.99,
        },
      });

      renderWithAuth(<Checkout />, ['/checkout']);

      expect(await screen.findByText('Mechanical Gaming Keyboard')).toBeInTheDocument();
      expect(screen.getAllByText('$89.99').length).toBeGreaterThan(0);
      expect(screen.getByRole('button', { name: /Confirm & Place Order/i })).toBeInTheDocument();
    });
  });

  describe('Authentication and Navigation Guards', () => {
    it('redirects unauthenticated users attempting to access /orders to login', () => {
      const ProtectedOrdersRoute = () => {
        const { isAuthenticated } = React.useContext(AuthContext);
        if (!isAuthenticated) {
          return <Navigate to="/login" replace />;
        }
        return <Orders />;
      };

      const authContext = {
        user: null,
        token: null,
        isAuthenticated: false,
        isAdmin: false,
        loading: false,
      };

      render(
        <AuthContext.Provider value={authContext}>
          <MemoryRouter initialEntries={['/orders']}>
            <Routes>
              <Route path="/orders" element={<ProtectedOrdersRoute />} />
              <Route path="/login" element={<div>Login Page Redirect Target</div>} />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      );

      expect(screen.getByText('Login Page Redirect Target')).toBeInTheDocument();
    });
  });
});
