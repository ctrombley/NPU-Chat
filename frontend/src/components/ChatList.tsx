import React from 'react';
import { Chat } from '../types';
import ChatListItem from './ChatListItem';
import { Sidebar } from './ui/Sidebar';
import { Button } from './ui/Button';
import ThemeToggle from './ThemeToggle';
import { Theme } from '../hooks/useTheme';

interface ChatListProps {
  chats: Chat[];
  currentChatId: string | null;
  onNewChat: () => void;
  onSwitchChat: (chatId: string) => void;
  onDeleteChat: (chatId: string) => void;
  onToggleFavorite: (chatId: string, isFavorite: boolean) => void;
  onEditChat: (chatId: string) => void;
  onShowSigns: () => void;
  sidebarWidth?: number;
  theme: Theme;
  onThemeChange: (theme: Theme) => void;
}

const ChatList: React.FC<ChatListProps> = ({
  chats,
  currentChatId,
  onNewChat,
  onSwitchChat,
  onDeleteChat,
  onToggleFavorite,
  onEditChat,
  onShowSigns,
  sidebarWidth,
  theme,
  onThemeChange,
}) => {
  return (
    <Sidebar
      title="Chats"
      style={sidebarWidth ? { width: sidebarWidth } : undefined}
      footer={<ThemeToggle theme={theme} onThemeChange={onThemeChange} />}
    >
      <ul className="list-none p-0 m-0">
        {chats.map((chat, index) => (
          <ChatListItem
            key={chat.id}
            chat={chat}
            index={index}
            isActive={currentChatId === chat.id}
            onSwitchChat={onSwitchChat}
            onToggleFavorite={onToggleFavorite}
            onDeleteChat={onDeleteChat}
            onEditChat={onEditChat}
          />
        ))}
      </ul>
      <Button
        variant="primary"
        onClick={onNewChat}
        aria-label="Create new chat"
      >
        New Chat
      </Button>
      <Button
        variant="secondary"
        onClick={onShowSigns}
        aria-label="Manage signs"
      >
        Signs
      </Button>
    </Sidebar>
  );
};

export default ChatList;
