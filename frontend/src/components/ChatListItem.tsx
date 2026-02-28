import React from 'react';
import { Chat } from '../types';
import { ListItem } from './ui/ListItem';
import { IconButton } from './ui/Button';

interface ChatListItemProps {
  chat: Chat;
  index: number;
  isActive: boolean;
  onSwitchChat: (chatId: string) => void;
  onToggleFavorite: (chatId: string, isFavorite: boolean) => void;
  onDeleteChat: (chatId: string) => void;
  onEditChat: (chatId: string) => void;
}

const ChatListItem: React.FC<ChatListItemProps> = ({
  chat,
  index,
  isActive,
  onSwitchChat,
  onToggleFavorite,
  onDeleteChat,
  onEditChat,
}) => {
  const handleToggleFavorite = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggleFavorite(chat.id, !chat.is_favorite);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDeleteChat(chat.id);
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    onEditChat(chat.id);
  };

  return (
    <ListItem
      active={isActive}
      onClick={() => onSwitchChat(chat.id)}
    >
      <span className="text-sm flex items-center">
        <IconButton
          variant="favorite"
          onClick={handleToggleFavorite}
          aria-label={chat.is_favorite ? 'Remove from favorites' : 'Add to favorites'}
        >
          {chat.is_favorite ? '⭐' : '☆'}
        </IconButton>
        {chat.emoji} {chat.name || `Chat ${index + 1}`}
      </span>
      <span className="flex items-center gap-0.5">
        <IconButton
          onClick={handleEdit}
          aria-label="Edit chat"
        >
          ⚙
        </IconButton>
        <IconButton
          variant="danger"
          onClick={handleDelete}
          aria-label="Delete chat"
        >
          ×
        </IconButton>
      </span>
    </ListItem>
  );
};

export default ChatListItem;
