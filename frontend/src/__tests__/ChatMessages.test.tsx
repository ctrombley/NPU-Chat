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
    expect(messageDiv).toHaveClass('bg-message-sent');
    expect(messageDiv).toHaveClass('rounded-tl-3xl');
    expect(messageDiv).toHaveClass('rounded-bl-3xl');
  });

  it('renders received messages with correct styling', () => {
    render(<ChatMessages messages={[mockMessages[1]]} />);

    const messageDiv = screen.getByText('Hi there!').closest('div');
    expect(messageDiv).toHaveClass('bg-message-received');
    expect(messageDiv).toHaveClass('rounded-tr-3xl');
    expect(messageDiv).toHaveClass('rounded-br-3xl');
  });

  it('renders HTML content for received messages with md tags', () => {
    render(<ChatMessages messages={[mockMessages[2]]} />);

    // Should render the HTML content
    const strongElement = screen.getByText('world');
    expect(strongElement.tagName).toBe('STRONG');
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
    expect(chatMessagesDiv.children).toHaveLength(2); // Background div and relative div
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

