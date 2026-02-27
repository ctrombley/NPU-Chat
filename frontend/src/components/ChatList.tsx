import React from 'react';
import { Chat } from '../types';

interface ChatListProps {
  chats: Chat[];
  currentChatId: string | null;
  onNewChat: () => void;
  onSwitchChat: (chatId: string) => void;
  onDeleteChat: (chatId: string) => void;
  onShowTemplates: () => void;
}

const ChatList: React.FC<ChatListProps> = ({
  chats,
  currentChatId,
  onNewChat,
  onSwitchChat,
  onDeleteChat,
  onShowTemplates,
}) => {
  return (
    <div className="w-48 h-full bg-sidebar-bg border-r border-gray-600 overflow-y-auto z-10">
      <h3 className="m-2.5 text-white text-base border-b border-gray-600 pb-1.5">
        Chats
      </h3>
      <ul className="list-none p-0 m-0">
        {chats.map((chat, index) => (
          <li
            key={chat.id}
            className={`flex justify-between items-center p-2.5 cursor-pointer border-b border-gray-600 transition-colors hover:bg-gray-700 ${
              currentChatId === chat.id ? 'bg-gray-600 border-l-4 border-accent' : ''
            }`}
            onClick={() => onSwitchChat(chat.id)}
          >
            <span className="text-sm">
              {chat.emoji} {chat.name || `Chat ${index + 1}`}
            </span>
            <button
              className="bg-none border-none text-gray-500 text-base cursor-pointer p-0.5 rounded transition-colors hover:text-red-400 hover:bg-gray-600"
              onClick={(e) => {
                e.stopPropagation();
                onDeleteChat(chat.id);
              }}
            >
              ×
            </button>
          </li>
        ))}
      </ul>
      <button
        className="w-full p-2.5 m-2.5 bg-accent text-white border-none rounded cursor-pointer text-sm transition-colors hover:bg-accent-hover"
        onClick={onNewChat}
      >
        New Chat
      </button>
      <button
        className="w-full p-2.5 m-2.5 bg-gray-600 text-white border-none rounded cursor-pointer text-sm transition-colors hover:bg-gray-700"
        onClick={onShowTemplates}
      >
        Manage Templates
      </button>
    </div>
  );
};

export default ChatList;

