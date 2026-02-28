import { render, screen, fireEvent, waitFor } from '../test-utils';
import Templates from '../components/Templates';
import { createMockTemplate } from '../test-utils';

// Mock fetch globally
global.fetch = jest.fn();

// JSON:API helper to wrap a collection
const jsonapiCollection = (type: string, items: { id: string; [key: string]: unknown }[]) => ({
  data: items.map(({ id, ...attrs }) => ({ type, id, attributes: attrs })),
});

const mockTemplates = [
  createMockTemplate({ id: 'template-1', name: 'Helpful Assistant', prefix: 'You are helpful', postfix: 'Be concise' }),
  createMockTemplate({ id: 'template-2', name: 'Code Expert', prefix: 'You are a coding expert', postfix: 'Use code blocks' }),
];

const mockOnClose = jest.fn();

const defaultMockFetch = (url: string, options?: RequestInit) => {
  if (url === '/api/v1/templates' && (!options || !options.method || options.method === 'GET')) {
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
    render(<Templates onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText('Templates')).toBeInTheDocument();
      expect(screen.getByText('Helpful Assistant')).toBeInTheDocument();
      expect(screen.getByText('Code Expert')).toBeInTheDocument();
    });
  });

  it('shows loading state initially', () => {
    render(<Templates onClose={mockOnClose} />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    render(<Templates onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Close' })).toBeInTheDocument();
    });

    const closeButton = screen.getByRole('button', { name: 'Close' });
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('handles edit template flow', async () => {
    // Override mock to handle PATCH
    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (typeof url === 'string' && url.startsWith('/api/v1/templates/') && options?.method === 'PATCH') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      }
      return defaultMockFetch(url, options);
    });

    render(<Templates onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText('Helpful Assistant')).toBeInTheDocument();
    });

    // Click edit
    const editButtons = screen.getAllByText('Edit');
    fireEvent.click(editButtons[0]);

    // The form should appear with current values
    await waitFor(() => {
      expect(screen.getByDisplayValue('Helpful Assistant')).toBeInTheDocument();
    });

    // Change the name
    const nameInput = screen.getByDisplayValue('Helpful Assistant');
    fireEvent.change(nameInput, { target: { value: 'New Name' } });

    // Click Save
    fireEvent.click(screen.getByText('Save'));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/templates/template-1', expect.objectContaining({
        method: 'PATCH',
      }));
    });
  });

  it('handles delete template with two-click confirmation', async () => {
    // Override mock to handle DELETE
    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (typeof url === 'string' && url.startsWith('/api/v1/templates/') && options?.method === 'DELETE') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      }
      return defaultMockFetch(url, options);
    });

    render(<Templates onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText('Helpful Assistant')).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByText('Delete');

    // First click shows "Confirm?" text
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Confirm?')).toBeInTheDocument();
    });

    // DELETE should NOT have been called yet
    expect(global.fetch).not.toHaveBeenCalledWith('/api/v1/templates/template-1', expect.objectContaining({ method: 'DELETE' }));

    // Second click actually deletes
    fireEvent.click(screen.getByText('Confirm?'));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/templates/template-1', expect.objectContaining({
        method: 'DELETE',
      }));
    });
  });

  it('handles create new template', async () => {
    // Override mock to handle POST
    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (url === '/api/v1/templates' && options?.method === 'POST') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      }
      return defaultMockFetch(url, options);
    });

    render(<Templates onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText('New Template')).toBeInTheDocument();
    });

    // Click New Template
    fireEvent.click(screen.getByText('New Template'));

    // Fill in the form
    const nameInput = screen.getByPlaceholderText('Template name');
    const prefixInput = screen.getByPlaceholderText('System prompt prefix...');
    const postfixInput = screen.getByPlaceholderText('System prompt postfix...');

    fireEvent.change(nameInput, { target: { value: 'New Template' } });
    fireEvent.change(prefixInput, { target: { value: 'New prefix' } });
    fireEvent.change(postfixInput, { target: { value: 'New postfix' } });

    // Click Create
    fireEvent.click(screen.getByText('Create'));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/templates', expect.objectContaining({
        method: 'POST',
      }));
    });
  });

  it('handles fetch errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    (global.fetch as jest.Mock).mockImplementation(() =>
      Promise.reject(new Error('Network error'))
    );

    render(<Templates onClose={mockOnClose} />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Error loading templates:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });
});
