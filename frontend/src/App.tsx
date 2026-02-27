import { useState, useEffect } from 'react';
import ChatList from './components/ChatList';
import ChatMessages from './components/ChatMessages';
import MessageInput from './components/MessageInput';
import Templates from './components/Templates';
import { Message, Chat } from './types';
import * as api from './api';

function App() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [currentMessages, setCurrentMessages] = useState<Message[]>([]);
  const [showTemplates, setShowTemplates] = useState(false);

  useEffect(() => {
    fetchChats();
  }, []);

  const fetchChats = async () => {
    try {
      const chatObjects = await api.listChats();
      setChats(chatObjects);
      if (chatObjects.length > 0) {
        setCurrentChatId(chatObjects[0].id);
        fetchMessages(chatObjects[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch chats:', error);
    }
  };

  const fetchMessages = async (chatId: string) => {
    try {
      const messages = await api.getChatMessages(chatId);
      setCurrentMessages(messages);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  };

  const handleNewChat = async () => {
    const chatName = prompt('Enter chat name:');
    if (!chatName) return;
    try {
      const chatObj = await api.createChat(chatName);
      setChats([...chats, chatObj]);
      setCurrentChatId(chatObj.id);
      setCurrentMessages([]);
    } catch (error) {
      console.error('Failed to create chat:', error);
    }
  };

  const handleSwitchChat = (chatId: string) => {
    setCurrentChatId(chatId);
    fetchMessages(chatId);
  };

  const handleDeleteChat = async (chatId: string) => {
    try {
      await api.deleteChat(chatId);
      setChats(chats.filter(c => c.id !== chatId));
      if (currentChatId === chatId) {
        const remaining = chats.filter(c => c.id !== chatId);
        if (remaining.length > 0) {
          setCurrentChatId(remaining[0].id);
          fetchMessages(remaining[0].id);
        } else {
          setCurrentChatId(null);
          setCurrentMessages([]);
        }
      }
    } catch (error) {
      console.error('Failed to delete chat:', error);
    }
  };

  const handleToggleFavorite = async (chatId: string, isFavorite: boolean) => {
    try {
      await api.updateChat(chatId, { is_favorite: isFavorite });
      setChats(chats.map(c => c.id === chatId ? { ...c, is_favorite: isFavorite } : c));
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    }
  };

  const handleSendMessage = async (messageText: string) => {
    if (!currentChatId) return;
    // Add user message to current messages
    const userMessage: Message = { type: 'sent', text: messageText, timestamp: Date.now() };
    setCurrentMessages(prev => [...prev, userMessage]);

    try {
      const data = await api.sendMessage(messageText, currentChatId);
      const botMessage: Message = { type: 'received', text: data.content, timestamp: Date.now() };
      setCurrentMessages(prev => [...prev, botMessage]);
      // Refresh chat list to pick up auto-naming changes
      const chatObjects = await api.listChats();
      setChats(chatObjects);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white font-bauhaus overflow-hidden">
      {showTemplates ? (
        <Templates onBack={() => setShowTemplates(false)} />
      ) : (
        <ChatList
          chats={chats}
          currentChatId={currentChatId}
          onNewChat={handleNewChat}
          onSwitchChat={handleSwitchChat}
          onDeleteChat={handleDeleteChat}
          onToggleFavorite={handleToggleFavorite}
          onShowTemplates={() => setShowTemplates(true)}
        />
      )}
      <ChatMessages messages={currentMessages} />
      <MessageInput
        currentChatId={currentChatId}
        onMessageSent={handleSendMessage}
      />
    </div>
  );
}

export default App;
