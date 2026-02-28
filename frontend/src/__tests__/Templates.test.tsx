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

  it('handles edit template flow with inline form', async () => {
    // Override mock to handle PATCH
    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (typeof url === 'string' && url.startsWith('/api/v1/templates/') && options?.method === 'PATCH') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      }
      return defaultMockFetch(url, options);
    });

    render(<Templates onBack={mockOnBack} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Edit template Helpful Assistant' })).toBeInTheDocument();
    });

    // Click edit to show inline form
    const editButton = screen.getByRole('button', { name: 'Edit template Helpful Assistant' });
    fireEvent.click(editButton);

    // The inline form should appear with current values
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

    render(<Templates onBack={mockOnBack} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Delete template Helpful Assistant' })).toBeInTheDocument();
    });

    const deleteButton = screen.getByRole('button', { name: 'Delete template Helpful Assistant' });

    // First click shows "Confirm?" text
    fireEvent.click(deleteButton);
    expect(deleteButton).toHaveTextContent('Confirm?');

    // DELETE should NOT have been called yet
    expect(global.fetch).not.toHaveBeenCalledWith('/api/v1/templates/template-1', expect.objectContaining({ method: 'DELETE' }));

    // Second click actually deletes
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/templates/template-1', expect.objectContaining({
        method: 'DELETE',
      }));
    });
  });

  it('does not delete on first click (two-click required)', async () => {
    render(<Templates onBack={mockOnBack} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Delete template Helpful Assistant' })).toBeInTheDocument();
    });

    const deleteButton = screen.getByRole('button', { name: 'Delete template Helpful Assistant' });
    fireEvent.click(deleteButton);

    // Only first click happened — should not have called DELETE
    expect(global.fetch).not.toHaveBeenCalledWith('/api/v1/templates/template-1', expect.objectContaining({ method: 'DELETE' }));
  });

  it('handles create new template with inline form', async () => {
    // Override mock to handle POST
    (global.fetch as jest.Mock).mockImplementation((url: string, options?: RequestInit) => {
      if (url === '/api/v1/templates' && options?.method === 'POST') {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      }
      return defaultMockFetch(url, options);
    });

    render(<Templates onBack={mockOnBack} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Create new template' })).not.toBeDisabled();
    });

    // Click New Template to show inline form
    const newButton = screen.getByRole('button', { name: 'Create new template' });
    fireEvent.click(newButton);

    // Fill in the form
    const nameInput = screen.getByPlaceholderText('Template name');
    const prefixInput = screen.getByPlaceholderText('Prefix');
    const postfixInput = screen.getByPlaceholderText('Postfix');

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

    render(<Templates onBack={mockOnBack} />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Error loading templates:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  it('disables buttons during loading', async () => {
    render(<Templates onBack={mockOnBack} />);

    // Initially loading — "New Template" button should be disabled
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
