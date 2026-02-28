import React from 'react';
import { Chat } from '../types';
import ChatListItem from './ChatListItem';
import { Sidebar } from './ui/Sidebar';
import { Button } from './ui/Button';

interface ChatListProps {
  chats: Chat[];
  currentChatId: string | null;
  onNewChat: () => void;
  onSwitchChat: (chatId: string) => void;
  onDeleteChat: (chatId: string) => void;
  onToggleFavorite: (chatId: string, isFavorite: boolean) => void;
  onEditChat: (chatId: string) => void;
  onShowTemplates: () => void;
  sidebarWidth?: number;
}

const ChatList: React.FC<ChatListProps> = ({
  chats,
  currentChatId,
  onNewChat,
  onSwitchChat,
  onDeleteChat,
  onToggleFavorite,
  onEditChat,
  onShowTemplates,
  sidebarWidth,
}) => {
  return (
    <Sidebar title="Chats" style={sidebarWidth ? { width: sidebarWidth } : undefined}>
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
        onClick={onShowTemplates}
        aria-label="Manage templates"
      >
        Manage Templates
      </Button>
    </Sidebar>
  );
};

export default ChatList;
