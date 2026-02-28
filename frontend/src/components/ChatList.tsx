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
  onShowTemplates: () => void;
  isCreatingChat?: boolean;
  newChatName?: string;
  onNewChatNameChange?: (name: string) => void;
  onCreateChatSubmit?: () => void;
  onCreateChatCancel?: () => void;
}

const ChatList: React.FC<ChatListProps> = ({
  chats,
  currentChatId,
  onNewChat,
  onSwitchChat,
  onDeleteChat,
  onToggleFavorite,
  onShowTemplates,
  isCreatingChat,
  newChatName,
  onNewChatNameChange,
  onCreateChatSubmit,
  onCreateChatCancel,
}) => {
  return (
    <Sidebar title="Chats">
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
          />
        ))}
      </ul>
      {isCreatingChat ? (
        <div className="flex gap-2 px-2">
          <input
            type="text"
            value={newChatName || ''}
            onChange={(e) => onNewChatNameChange?.(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') onCreateChatSubmit?.();
              if (e.key === 'Escape') onCreateChatCancel?.();
            }}
            placeholder="Chat name..."
            autoFocus
            className="flex-1 px-2 py-1 bg-gray-700 text-white border border-gray-600 rounded text-sm focus:outline-none focus:border-blue-500"
          />
          <Button variant="primary" onClick={onCreateChatSubmit}>
            OK
          </Button>
          <Button variant="secondary" onClick={onCreateChatCancel}>
            Cancel
          </Button>
        </div>
      ) : (
        <Button
          variant="primary"
          onClick={onNewChat}
          aria-label="Create new chat"
        >
          New Chat
        </Button>
      )}
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
