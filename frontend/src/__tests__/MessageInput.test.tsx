import { render, screen, fireEvent, waitFor } from '../test-utils';
import MessageInput from '../components/MessageInput';

const mockOnMessageSent = jest.fn();

const defaultProps = {
  currentChatId: 'chat-1',
  onMessageSent: mockOnMessageSent,
  isLoading: false,
};

describe('MessageInput', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders input and send button', () => {
    render(<MessageInput {...defaultProps} />);

    expect(screen.getByLabelText('Type your message')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Send message' })).toBeInTheDocument();
  });

  it('updates input value when typing', () => {
    render(<MessageInput {...defaultProps} />);

    const input = screen.getByLabelText('Type your message');
    fireEvent.change(input, { target: { value: 'Hello world' } });

    expect(input).toHaveValue('Hello world');
  });

  it('calls onMessageSent when form is submitted', async () => {
    mockOnMessageSent.mockResolvedValueOnce(undefined);
    render(<MessageInput {...defaultProps} />);

    const input = screen.getByLabelText('Type your message');
    const form = screen.getByRole('form');

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.submit(form);

    await waitFor(() => {
      expect(mockOnMessageSent).toHaveBeenCalledWith('Test message');
    });
  });

  it('clears input after successful submission', async () => {
    mockOnMessageSent.mockResolvedValueOnce(undefined);
    render(<MessageInput {...defaultProps} />);

    const input = screen.getByLabelText('Type your message');
    const form = screen.getByRole('form');

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.submit(form);

    await waitFor(() => {
      expect(input).toHaveValue('');
    });
  });

  it('submits on Enter key press', async () => {
    mockOnMessageSent.mockResolvedValueOnce(undefined);
    render(<MessageInput {...defaultProps} />);

    const input = screen.getByLabelText('Type your message');

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      expect(mockOnMessageSent).toHaveBeenCalledWith('Test message');
    });
  });

  it('does not submit on Shift+Enter', () => {
    render(<MessageInput {...defaultProps} />);

    const input = screen.getByLabelText('Type your message');

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter', shiftKey: true });

    expect(mockOnMessageSent).not.toHaveBeenCalled();
  });

  it('disables input and button when no current chat', () => {
    render(<MessageInput {...defaultProps} currentChatId={null} />);

    const input = screen.getByLabelText('Type your message');
    const button = screen.getByRole('button', { name: 'Send message' });

    expect(input).toBeDisabled();
    expect(button).toBeDisabled();
  });

  it('disables input and button when loading', () => {
    render(<MessageInput {...defaultProps} isLoading={true} />);

    const input = screen.getByLabelText('Type your message');
    const button = screen.getByRole('button', { name: 'Sending message...' });

    expect(input).toBeDisabled();
    expect(button).toBeDisabled();
  });

  it('disables button when input is empty', () => {
    render(<MessageInput {...defaultProps} />);

    const button = screen.getByRole('button', { name: 'Send message' });
    expect(button).toBeDisabled();

    const input = screen.getByLabelText('Type your message');
    fireEvent.change(input, { target: { value: '   ' } });
    expect(button).toBeDisabled();

    fireEvent.change(input, { target: { value: 'Hello' } });
    expect(button).not.toBeDisabled();
  });

  it('shows loading state on button', () => {
    render(<MessageInput {...defaultProps} isLoading={true} />);

    expect(screen.getByRole('button', { name: 'Sending message...' })).toBeInTheDocument();
  });

  it('shows correct placeholder text', () => {
    const { rerender } = render(<MessageInput {...defaultProps} />);

    expect(screen.getByPlaceholderText('Chat...')).toBeInTheDocument();

    rerender(<MessageInput {...defaultProps} currentChatId={null} />);
    expect(screen.getByPlaceholderText('Select a chat to start messaging')).toBeInTheDocument();
  });
});

