import { render, screen, fireEvent } from '../test-utils';
import ChatList from '../components/ChatList';
import { createMockChat } from '../test-utils';

const mockProps = {
  chats: [
    createMockChat({ id: 'chat-1', name: 'First Chat', emoji: '🤖', is_favorite: false }),
    createMockChat({ id: 'chat-2', name: 'Second Chat', emoji: '🚀', is_favorite: true }),
  ],
  currentChatId: 'chat-1',
  onNewChat: jest.fn(),
  onSwitchChat: jest.fn(),
  onDeleteChat: jest.fn(),
  onToggleFavorite: jest.fn(),
  onEditChat: jest.fn(),
  onShowTemplates: jest.fn(),
};

describe('ChatList', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders chat list with all chats', () => {
    render(<ChatList {...mockProps} />);

    expect(screen.getByText('Chats')).toBeInTheDocument();
    expect(screen.getByText('🤖 First Chat')).toBeInTheDocument();
    expect(screen.getByText('🚀 Second Chat')).toBeInTheDocument();
  });

  it('highlights the active chat', () => {
    render(<ChatList {...mockProps} />);

    const activeChatItem = screen.getByText('🤖 First Chat').closest('li');
    expect(activeChatItem).toHaveClass('border-l-4', 'border-l-tn-blue');
  });

  it('calls onNewChat when New Chat button is clicked', () => {
    render(<ChatList {...mockProps} />);

    const newChatButton = screen.getByRole('button', { name: 'Create new chat' });
    fireEvent.click(newChatButton);

    expect(mockProps.onNewChat).toHaveBeenCalledTimes(1);
  });

  it('calls onShowTemplates when Manage Templates button is clicked', () => {
    render(<ChatList {...mockProps} />);

    const templatesButton = screen.getByRole('button', { name: 'Manage templates' });
    fireEvent.click(templatesButton);

    expect(mockProps.onShowTemplates).toHaveBeenCalledTimes(1);
  });

  it('calls onSwitchChat when a chat item is clicked', () => {
    render(<ChatList {...mockProps} />);

    const secondChatItem = screen.getByText('🚀 Second Chat');
    fireEvent.click(secondChatItem);

    expect(mockProps.onSwitchChat).toHaveBeenCalledWith('chat-2');
  });

  it('calls onToggleFavorite when favorite button is clicked', () => {
    render(<ChatList {...mockProps} />);

    const favoriteButtons = screen.getAllByRole('button', { name: /Remove from favorites|Add to favorites/ });
    fireEvent.click(favoriteButtons[0]); // First chat's favorite button

    expect(mockProps.onToggleFavorite).toHaveBeenCalledWith('chat-1', true);
  });

  it('calls onDeleteChat when delete button is clicked', () => {
    render(<ChatList {...mockProps} />);

    const deleteButtons = screen.getAllByRole('button', { name: 'Delete chat' });
    fireEvent.click(deleteButtons[0]); // First chat's delete button

    expect(mockProps.onDeleteChat).toHaveBeenCalledWith('chat-1');
  });

  it('displays default chat names when no custom name is provided', () => {
    const propsWithUnnamedChats = {
      ...mockProps,
      chats: [
        createMockChat({ id: 'chat-1', name: '' }),
        createMockChat({ id: 'chat-2', name: '' }),
      ],
    };

    render(<ChatList {...propsWithUnnamedChats} />);

    expect(screen.getByText('🤖 Chat 1')).toBeInTheDocument();
    expect(screen.getByText('🤖 Chat 2')).toBeInTheDocument();
  });

  it('handles empty chat list', () => {
    const propsWithNoChats = {
      ...mockProps,
      chats: [],
    };

    render(<ChatList {...propsWithNoChats} />);

    expect(screen.getByText('Chats')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create new chat' })).toBeInTheDocument();
  });
});

