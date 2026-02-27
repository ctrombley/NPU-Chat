import { useState, useEffect } from 'react';
import ChatList from './components/ChatList';
import ChatMessages from './components/ChatMessages';
import MessageInput from './components/MessageInput';
import Templates from './components/Templates';
import { Message, Chat } from './types';

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
      const response = await fetch('/chats');
      if (response.ok) {
        const chatList: any[] = await response.json();
        const chatObjects: Chat[] = chatList.map(c => ({
          id: c.id,
          name: c.name,
          emoji: c.emoji,
          messages: [] // messages will be fetched separately
        }));
        setChats(chatObjects);
        if (chatObjects.length > 0) {
          setCurrentChatId(chatObjects[0].id);
          fetchMessages(chatObjects[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to fetch chats:', error);
    }
  };

  const fetchMessages = async (chatId: string) => {
    try {
      const response = await fetch(`/chats/${chatId}/messages`);
      if (response.ok) {
        const messages: Message[] = await response.json().then(data => data.messages.map((m: string) => {
          // Assuming messages are strings like "User: ..." or "Assistant: ..."
          const isUser = m.startsWith('User: ');
          const text = isUser ? m.substring(6) : m.startsWith('Assistant: ') ? m.substring(11) : m;
          return { type: isUser ? 'sent' : 'received', text, timestamp: Date.now() };
        }));
        setCurrentMessages(messages);
      }
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  };

  const handleNewChat = async () => {
    const chatName = prompt('Enter chat name:');
    if (!chatName) return;
    try {
      const response = await fetch('/chats', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: chatName })
      });
      if (response.ok) {
        const newChat: any = await response.json();
        const chatObj: Chat = { id: newChat.chat_id, name: newChat.name, emoji: '', messages: [] };
        setChats([...chats, chatObj]);
        setCurrentChatId(chatObj.id);
        setCurrentMessages([]);
      }
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
      const response = await fetch(`/chats/${chatId}`, { method: 'DELETE' });
      if (response.ok) {
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
      }
    } catch (error) {
      console.error('Failed to delete chat:', error);
    }
  };

  const handleSendMessage = async (messageText: string) => {
    if (!currentChatId) return;
    // Add user message to current messages
    const userMessage: Message = { type: 'sent', text: messageText, timestamp: Date.now() };
    setCurrentMessages(prev => [...prev, userMessage]);

    try {
      const formData = new FormData();
      formData.append('input_text', messageText);
      const response = await fetch(`/search?session_id=${currentChatId}`, {
        method: 'POST',
        body: formData
      });
      if (response.ok) {
        const data: any = await response.json();
        const botMessage: Message = { type: 'received', text: data.content.replace(/<md[^>]*>|<\/md>/g, ''), timestamp: Date.now() };
        setCurrentMessages(prev => [...prev, botMessage]);
        // Refresh chats to update metadata if needed
        fetchChats();
      }
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

