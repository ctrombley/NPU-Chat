import React, { ReactElement } from 'react';
import { render, RenderOptions, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Custom render function that includes providers and common setup
const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <>
      {children}
    </>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options });

// Mock data factories
export const createMockChat = (overrides = {}) => ({
  id: 'chat-1',
  name: 'Test Chat',
  emoji: '🤖',
  is_favorite: false,
  messages: [],
  ...overrides,
});

export const createMockMessage = (overrides = {}) => ({
  type: 'sent' as const,
  text: 'Hello world',
  timestamp: Date.now(),
  ...overrides,
});

export const createMockTemplate = (overrides = {}) => ({
  id: 'template-1',
  name: 'Test Template',
  prefix: 'You are a helpful assistant.',
  postfix: 'Please be concise.',
  ...overrides,
});

// Custom user event setup
export const setupUserEvent = () => userEvent.setup();

export * from '@testing-library/react';
export { customRender as render, fireEvent };

