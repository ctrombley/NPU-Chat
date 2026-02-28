import { TextEncoder } from 'util';
import { ReadableStream } from 'stream/web';

// Polyfill for jsdom
if (typeof globalThis.TextEncoder === 'undefined') {
  globalThis.TextEncoder = TextEncoder;
}
if (typeof globalThis.ReadableStream === 'undefined') {
  (globalThis as unknown as Record<string, unknown>).ReadableStream = ReadableStream;
}

import { render, screen, fireEvent, waitFor, act } from '../test-utils';
import App from '../App';

// Mock fetch globally
global.fetch = jest.fn();

// JSON:API helper to wrap a collection
const jsonapiCollection = (type: string, items: { id: string; [key: string]: unknown }[]) => ({
  data: items.map(({ id, ...attrs }) => ({ type, id, attributes: attrs })),
});

// JSON:API helper to wrap a single resource
const jsonapiResource = (type: string, id: string, attrs: Record<string, unknown>) => ({
  data: { type, id, attributes: attrs },
});

const defaultMockFetch = (url: string, options?: RequestInit) => {
  if (url === '/api/v1/chats' && (!options || !options.method || options.method === 'GET')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(
        jsonapiCollection('chats', [
          { id: 'chat-1', name: 'Test Chat', emoji: '🤖', is_favorite: false, message_count: 0 },
        ])
      ),
    });
  }
  if (url === '/api/v1/chats/chat-1/messages') {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(jsonapiCollection('messages', [])),
    });
  }
  if (url === '/api/v1/templates') {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(jsonapiCollection('templates', [])),
    });
  }
  return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
};

describe('App Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockImplementation(defaultMockFetch);
  });

  it('renders the app with initial state', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Chats')).toBeInTheDocument();
      expect(screen.getByText(/Test Chat/)).toBeInTheDocument();
    });
  });

  it('creates a new chat when New Chat is clicked', async () => {
    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (url === '/api/v1/chats' && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(
            jsonapiResource('chats', 'chat-2', { name: 'Chat 1', emoji: '', is_favorite: false, message_count: 0 })
          ),
        });
      }
      return defaultMockFetch(url, options);
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Create new chat' })).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Create new chat' }));
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/chats', expect.objectContaining({
        method: 'POST',
      }));
    });
  });

  it('sends messages successfully via streaming', async () => {
    // Create a mock SSE response body
    const sseData = [
      'data: {"session_id":"chat-1","chunk":"Hello "}\n\n',
      'data: {"session_id":"chat-1","chunk":"from bot"}\n\n',
      'data: {"session_id":"chat-1","done":true}\n\n',
    ].join('');
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(sseData));
        controller.close();
      },
    });

    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (url === '/api/v1/search/stream' && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          body: stream,
        });
      }
      return defaultMockFetch(url, options);
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Test Chat/)).toBeInTheDocument();
    });

    const messageInput = screen.getByLabelText('Type your message');
    const sendButton = screen.getByRole('button', { name: 'Send message' });

    await act(async () => {
      fireEvent.change(messageInput, { target: { value: 'Hello bot' } });
      fireEvent.click(sendButton);
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/search/stream', expect.objectContaining({
        method: 'POST',
      }));
    });
  });

  it('fires shadow review-metadata request concurrently when message is sent', async () => {
    const sseData = [
      'data: {"session_id":"chat-1","chunk":"Hi"}\n\n',
      'data: {"session_id":"chat-1","done":true}\n\n',
    ].join('');
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(sseData));
        controller.close();
      },
    });

    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (url === '/api/v1/search/stream' && options?.method === 'POST') {
        return Promise.resolve({ ok: true, body: stream });
      }
      if (url === '/api/v1/chats/chat-1/review-metadata' && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(
            jsonapiResource('chats', 'chat-1', { name: 'Shadow Name', emoji: '🔮', is_favorite: false, message_count: 0 })
          ),
        });
      }
      return defaultMockFetch(url, options);
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Test Chat/)).toBeInTheDocument();
    });

    const messageInput = screen.getByLabelText('Type your message');
    const sendButton = screen.getByRole('button', { name: 'Send message' });

    await act(async () => {
      fireEvent.change(messageInput, { target: { value: 'Hello shadow' } });
      fireEvent.click(sendButton);
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/chats/chat-1/review-metadata',
        expect.objectContaining({ method: 'POST' }),
      );
    });

    // Both the stream and the shadow request should have fired
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/search/stream',
        expect.objectContaining({ method: 'POST' }),
      );
    });
  });

  it('sends user_message in shadow review-metadata request body', async () => {
    const sseData = 'data: {"session_id":"chat-1","done":true}\n\n';
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(sseData));
        controller.close();
      },
    });

    const shadowCalls: string[] = [];

    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (url === '/api/v1/search/stream' && options?.method === 'POST') {
        return Promise.resolve({ ok: true, body: stream });
      }
      if (url === '/api/v1/chats/chat-1/review-metadata' && options?.method === 'POST') {
        shadowCalls.push(options?.body as string ?? '');
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(
            jsonapiResource('chats', 'chat-1', { name: 'Test Chat', emoji: '', is_favorite: false, message_count: 0 })
          ),
        });
      }
      return defaultMockFetch(url, options);
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Test Chat/)).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.change(screen.getByLabelText('Type your message'), { target: { value: 'My specific question' } });
      fireEvent.click(screen.getByRole('button', { name: 'Send message' }));
    });

    await waitFor(() => {
      expect(shadowCalls.length).toBeGreaterThan(0);
    });

    const parsed = JSON.parse(shadowCalls[0]);
    expect(parsed.user_message).toBe('My specific question');
  });

  it('updates chat list from shadow review-metadata response', async () => {
    const sseData = 'data: {"session_id":"chat-1","done":true}\n\n';
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(sseData));
        controller.close();
      },
    });

    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (url === '/api/v1/search/stream' && options?.method === 'POST') {
        return Promise.resolve({ ok: true, body: stream });
      }
      if (url === '/api/v1/chats/chat-1/review-metadata' && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(
            jsonapiResource('chats', 'chat-1', { name: 'Reviewed Name', emoji: '✨', is_favorite: false, message_count: 0 })
          ),
        });
      }
      return defaultMockFetch(url, options);
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Test Chat/)).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.change(screen.getByLabelText('Type your message'), { target: { value: 'Update my chat name' } });
      fireEvent.click(screen.getByRole('button', { name: 'Send message' }));
    });

    await waitFor(() => {
      expect(screen.getByText(/Reviewed Name/)).toBeInTheDocument();
    });
  });

  it('handles template management modal', async () => {
    render(<App />);

    await waitFor(() => {
      const templatesButton = screen.getByRole('button', { name: 'Manage templates' });
      fireEvent.click(templatesButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Templates')).toBeInTheDocument();
    });
  });

  it('toggles chat favorites', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Add to favorites' })).toBeInTheDocument();
    });

    const favoriteButton = screen.getByRole('button', { name: 'Add to favorites' });

    await act(async () => {
      fireEvent.click(favoriteButton);
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/chats/chat-1', expect.objectContaining({
        method: 'PATCH',
      }));
    });
  });

  it('deletes chats', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Delete chat' })).toBeInTheDocument();
    });

    const deleteButton = screen.getByRole('button', { name: 'Delete chat' });

    await act(async () => {
      fireEvent.click(deleteButton);
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/chats/chat-1', expect.objectContaining({
        method: 'DELETE',
      }));
    });
  });

  it('handles network errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (url === '/api/v1/chats' && options?.method === 'POST') {
        return Promise.reject(new Error('Network error'));
      }
      return defaultMockFetch(url, options);
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Create new chat' })).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Create new chat' }));
    });

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to create chat:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });
});
