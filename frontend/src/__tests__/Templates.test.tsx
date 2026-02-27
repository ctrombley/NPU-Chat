import { render, screen, fireEvent, waitFor } from '../test-utils';
import Templates from '../components/Templates';
import { createMockTemplate } from '../test-utils';

// Mock fetch globally
global.fetch = jest.fn();

// JSON:API helper to wrap a collection
const jsonapiCollection = (type: string, items: { id: string; [key: string]: any }[]) => ({
  data: items.map(({ id, ...attrs }) => ({ type, id, attributes: attrs })),
});

const mockTemplates = [
  createMockTemplate({ id: 'template-1', name: 'Helpful Assistant', prefix: 'You are helpful', postfix: 'Be concise' }),
  createMockTemplate({ id: 'template-2', name: 'Code Expert', prefix: 'You are a coding expert', postfix: 'Use code blocks' }),
];

const mockOnBack = jest.fn();

const defaultMockFetch = (url: string, options?: RequestInit) => {
  if (url === '/api/templates' && (!options || !options.method || options.method === 'GET')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(
        jsonapiCollection('templates', mockTemplates)
      ),
    });
  }
  return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
};

describe('Templates', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockImplementation(defaultMockFetch);
  });

  it('renders templates list', async () => {
    render(<Templates onBack={mockOnBack} />);

    await waitFor(() => {
      expect(screen.getByText('Templates')).toBeInTheDocument();
      expect(screen.getByText('Helpful Assistant')).toBeInTheDocument();
      expect(screen.getByText('Code Expert')).toBeInTheDocument();
    });
  });

  it('shows loading state initially', () => {
    render(<Templates onBack={mockOnBack} />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('displays template details', async () => {
    render(<Templates onBack={mockOnBack} />);

    await waitFor(() => {
      expect(screen.getByText('Prefix: You are helpful')).toBeInTheDocument();
      expect(screen.getByText('Postfix: Be concise')).toBeInTheDocument();
    });
  });

  it('calls onBack when Back button is clicked', async () => {
    render(<Templates onBack={mockOnBack} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Back to chats' })).not.toBeDisabled();
    });

    const backButton = screen.getByRole('button', { name: 'Back to chats' });
    fireEvent.click(backButton);

    expect(mockOnBack).toHaveBeenCalledTimes(1);
  });

  it('handles edit template flow', async () => {
    // Mock window.prompt
    const mockPrompt = jest.spyOn(window, 'prompt').mockImplementation(() => 'New Name');

    // Override mock to handle PATCH
    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (typeof url === 'string' && url.startsWith('/api/templates/') && options?.method === 'PATCH') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      }
      return defaultMockFetch(url, options);
    });

    render(<Templates onBack={mockOnBack} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Edit template Helpful Assistant' })).toBeInTheDocument();
    });

    const editButton = screen.getByRole('button', { name: 'Edit template Helpful Assistant' });
    fireEvent.click(editButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/templates/template-1', expect.objectContaining({
        method: 'PATCH',
      }));
    });

    mockPrompt.mockRestore();
  });

  it('handles delete template with confirmation', async () => {
    // Mock window.confirm
    const mockConfirm = jest.spyOn(window, 'confirm').mockImplementation(() => true);

    // Override mock to handle DELETE
    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (typeof url === 'string' && url.startsWith('/api/templates/') && options?.method === 'DELETE') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      }
      return defaultMockFetch(url, options);
    });

    render(<Templates onBack={mockOnBack} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Delete template Helpful Assistant' })).toBeInTheDocument();
    });

    const deleteButton = screen.getByRole('button', { name: 'Delete template Helpful Assistant' });
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/templates/template-1', expect.objectContaining({
        method: 'DELETE',
      }));
    });

    mockConfirm.mockRestore();
  });

  it('does not delete when confirmation is cancelled', async () => {
    const mockConfirm = jest.spyOn(window, 'confirm').mockImplementation(() => false);

    render(<Templates onBack={mockOnBack} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Delete template Helpful Assistant' })).toBeInTheDocument();
    });

    const deleteButton = screen.getByRole('button', { name: 'Delete template Helpful Assistant' });
    fireEvent.click(deleteButton);

    expect(global.fetch).not.toHaveBeenCalledWith('/api/templates/template-1', expect.objectContaining({ method: 'DELETE' }));

    mockConfirm.mockRestore();
  });

  it('handles create new template', async () => {
    const mockPrompt = jest.spyOn(window, 'prompt');
    mockPrompt.mockImplementationOnce(() => 'New Template');
    mockPrompt.mockImplementationOnce(() => 'New prefix');
    mockPrompt.mockImplementationOnce(() => 'New postfix');

    // Override mock to handle POST
    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (url === '/api/templates' && options?.method === 'POST') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      }
      return defaultMockFetch(url, options);
    });

    render(<Templates onBack={mockOnBack} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Create new template' })).not.toBeDisabled();
    });

    const newButton = screen.getByRole('button', { name: 'Create new template' });
    fireEvent.click(newButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/templates', expect.objectContaining({
        method: 'POST',
      }));
    });

    mockPrompt.mockRestore();
  });

  it('handles fetch errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    (global.fetch as jest.Mock).mockImplementation(() =>
      Promise.reject(new Error('Network error'))
    );

    render(<Templates onBack={mockOnBack} />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Error loading templates:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  it('disables buttons during loading', async () => {
    render(<Templates onBack={mockOnBack} />);

    // Initially loading
    const newButton = screen.getByRole('button', { name: 'Create new template' });
    const backButton = screen.getByRole('button', { name: 'Back to chats' });

    expect(newButton).toBeDisabled();
    expect(backButton).toBeDisabled();

    // After loading
    await waitFor(() => {
      expect(newButton).not.toBeDisabled();
      expect(backButton).not.toBeDisabled();
    });
  });
});
