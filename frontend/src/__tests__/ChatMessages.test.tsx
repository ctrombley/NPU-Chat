import { render, screen, waitFor, fireEvent } from '../test-utils';
import ChatMessages from '../components/ChatMessages';
import { createMockMessage } from '../test-utils';

const mockMessages = [
  createMockMessage({ type: 'sent', text: 'Hello world', timestamp: 1000 }),
  createMockMessage({ type: 'received', text: 'Hi there!', timestamp: 2000 }),
  createMockMessage({
    type: 'received',
    text: '<md>Hello <strong>world</strong></md>',
    timestamp: 3000
  }),
];

describe('ChatMessages', () => {
  it('renders all messages', () => {
    render(<ChatMessages messages={mockMessages} />);

    expect(screen.getByText('Hello world')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
    expect(screen.getByText('Hello world')).toBeInTheDocument(); // From HTML content
  });

  it('renders sent messages with correct styling', () => {
    render(<ChatMessages messages={[mockMessages[0]]} />);

    const messageDiv = screen.getByText('Hello world').closest('div');
    expect(messageDiv).toHaveClass('bg-theme-bubble-sent');
    expect(messageDiv).toHaveClass('rounded-2xl');
    expect(messageDiv).toHaveClass('rounded-br-sm');
  });

  it('renders received messages with correct styling', () => {
    render(<ChatMessages messages={[mockMessages[1]]} />);

    const messageDiv = screen.getByText('Hi there!').closest('div');
    expect(messageDiv).toHaveClass('bg-theme-bubble-received');
    expect(messageDiv).toHaveClass('rounded-2xl');
    expect(messageDiv).toHaveClass('rounded-bl-sm');
  });

  it('renders md-tagged content as safe plain text', () => {
    render(<ChatMessages messages={[mockMessages[2]]} />);

    // Should strip md tags and render HTML as escaped text, not as DOM elements
    const textContent = screen.getByText(/Hello <strong>world<\/strong>/);
    expect(textContent.tagName).toBe('P');
  });

  it('shows copy button only for received messages', () => {
    render(<ChatMessages messages={mockMessages} />);

    const copyButtons = screen.getAllByRole('button', { name: 'Copy message' });
    expect(copyButtons).toHaveLength(2); // Only for the two received messages
  });

  it('copies message text to clipboard when copy button is clicked', async () => {
    render(<ChatMessages messages={[mockMessages[1]]} />);

    const copyButton = screen.getByRole('button', { name: 'Copy message' });
    fireEvent.click(copyButton);

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Hi there!');
    });
  });

  it('handles empty message list', () => {
    render(<ChatMessages messages={[]} />);

    const chatMessagesDiv = screen.getByTestId('chat-messages');
    expect(chatMessagesDiv).toBeInTheDocument();
    expect(chatMessagesDiv.children).toHaveLength(1); // Relative div with scroll anchor
  });

  it('auto-scrolls to bottom when messages change', () => {
    const { rerender } = render(<ChatMessages messages={[mockMessages[0]]} />);

    const scrollIntoViewMock = jest.fn();
    const messagesEndRef = screen.getByTestId('messages-end');
    messagesEndRef.scrollIntoView = scrollIntoViewMock;

    rerender(<ChatMessages messages={[mockMessages[0], mockMessages[1]]} />);

    expect(scrollIntoViewMock).toHaveBeenCalledWith({ behavior: 'smooth' });
  });
});

