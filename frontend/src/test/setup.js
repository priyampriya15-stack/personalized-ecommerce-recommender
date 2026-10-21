import '@testing-library/jest-dom';

// JSDOM mock for ResizeObserver used by Recharts ResponsiveContainer
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
