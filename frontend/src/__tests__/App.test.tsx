import { render, screen, fireEvent, waitFor } from '../test-utils';
import App from '../App';

// Mock fetch globally
global.fetch = jest.fn();

// JSON:API helper to wrap a collection
const jsonapiCollection = (type: string, items: { id: string; [key: string]: any }[]) => ({
  data: items.map(({ id, ...attrs }) => ({ type, id, attributes: attrs })),
});

// JSON:API helper to wrap a single resource
const jsonapiResource = (type: string, id: string, attrs: Record<string, any>) => ({
  data: { type, id, attributes: attrs },
});

const defaultMockFetch = (url: string, options?: RequestInit) => {
  if (url === '/api/chats' && (!options || !options.method || options.method === 'GET')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(
        jsonapiCollection('chats', [
          { id: 'chat-1', name: 'Test Chat', emoji: '🤖', is_favorite: false, message_count: 0 },
        ])
      ),
    });
  }
  if (url === '/api/chats/chat-1/messages') {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(jsonapiCollection('messages', [])),
    });
  }
  if (url === '/api/templates') {
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

  it('switches between chats', async () => {
    // Override mock to also handle POST /api/chats for creating a new chat
    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (url === '/api/chats' && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(
            jsonapiResource('chats', 'chat-2', { name: 'New Chat', emoji: '', is_favorite: false, message_count: 0 })
          ),
        });
      }
      return defaultMockFetch(url, options);
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Create new chat' })).toBeInTheDocument();
    });

    // Click New Chat to show inline input
    const newChatButton = screen.getByRole('button', { name: 'Create new chat' });
    fireEvent.click(newChatButton);

    // Type a name in the inline input and submit
    const nameInput = screen.getByPlaceholderText('Chat name...');
    fireEvent.change(nameInput, { target: { value: 'New Chat' } });
    fireEvent.click(screen.getByText('OK'));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/chats', expect.objectContaining({
        method: 'POST',
      }));
    });
  });

  it('sends messages successfully', async () => {
    // Override mock to also handle POST /api/search
    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (url === '/api/search' && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(
            jsonapiResource('search-results', 'chat-1', {
              content: 'Hello from bot',
              session_id: 'chat-1',
            })
          ),
        });
      }
      return defaultMockFetch(url, options);
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByLabelText('Type your message')).toBeInTheDocument();
    });

    const messageInput = screen.getByLabelText('Type your message');
    const sendButton = screen.getByRole('button', { name: 'Send message' });

    fireEvent.change(messageInput, { target: { value: 'Hello bot' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/search', expect.objectContaining({
        method: 'POST',
      }));
    });
  });

  it('handles template management', async () => {
    render(<App />);

    await waitFor(() => {
      const templatesButton = screen.getByRole('button', { name: 'Manage templates' });
      fireEvent.click(templatesButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Templates')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Create new template' })).toBeInTheDocument();
    });
  });

  it('toggles chat favorites', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Add to favorites' })).toBeInTheDocument();
    });

    const favoriteButton = screen.getByRole('button', { name: 'Add to favorites' });
    fireEvent.click(favoriteButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/chats/chat-1', expect.objectContaining({
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
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/chats/chat-1', expect.objectContaining({
        method: 'DELETE',
      }));
    });
  });

  it('handles network errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    // Override mock to reject on POST /api/chats
    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (url === '/api/chats' && options?.method === 'POST') {
        return Promise.reject(new Error('Network error'));
      }
      return defaultMockFetch(url, options);
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Create new chat' })).toBeInTheDocument();
    });

    // Click New Chat to show inline input
    const newChatButton = screen.getByRole('button', { name: 'Create new chat' });
    fireEvent.click(newChatButton);

    // Type name and submit
    const nameInput = screen.getByPlaceholderText('Chat name...');
    fireEvent.change(nameInput, { target: { value: 'Test' } });
    fireEvent.click(screen.getByText('OK'));

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to create chat:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });
});
