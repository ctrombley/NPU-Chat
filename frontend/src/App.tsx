import { useState, useEffect } from 'react';
import ChatList from './components/ChatList';
import ChatMessages from './components/ChatMessages';
import MessageInput from './components/MessageInput';
import Templates from './components/Templates';
import { Message } from './types';
import { useChats, useCreateChat, useDeleteChat, useToggleFavorite } from './hooks/useChats';
import { useMessages } from './hooks/useMessages';
import { useSendMessage } from './hooks/useSearch';

function App() {
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [showTemplates, setShowTemplates] = useState(false);
  const [isCreatingChat, setIsCreatingChat] = useState(false);
  const [newChatName, setNewChatName] = useState('');
  const [optimisticMessages, setOptimisticMessages] = useState<Message[]>([]);

  const { data: chats = [] } = useChats();
  const { data: serverMessages = [] } = useMessages(currentChatId);
  const createChatMutation = useCreateChat();
  const deleteChatMutation = useDeleteChat();
  const toggleFavoriteMutation = useToggleFavorite();
  const sendMessageMutation = useSendMessage();

  // Select first chat when chats load and none is selected
  useEffect(() => {
    if (chats.length > 0 && !currentChatId) {
      setCurrentChatId(chats[0].id);
    }
  }, [chats, currentChatId]);

  // Merge server messages with optimistic messages
  const currentMessages = optimisticMessages.length > 0 ? optimisticMessages : serverMessages;

  // Clear optimistic messages when server messages update after a send
  useEffect(() => {
    if (!sendMessageMutation.isPending && optimisticMessages.length > 0) {
      setOptimisticMessages([]);
    }
  }, [sendMessageMutation.isPending, optimisticMessages.length]);

  const handleNewChat = () => {
    setIsCreatingChat(true);
    setNewChatName('');
  };

  const handleCreateChatSubmit = async () => {
    const name = newChatName.trim();
    if (!name) return;
    setIsCreatingChat(false);
    setNewChatName('');
    try {
      const chatObj = await createChatMutation.mutateAsync(name);
      setCurrentChatId(chatObj.id);
      setOptimisticMessages([]);
    } catch (error) {
      console.error('Failed to create chat:', error);
    }
  };

  const handleCreateChatCancel = () => {
    setIsCreatingChat(false);
    setNewChatName('');
  };

  const handleSwitchChat = (chatId: string) => {
    setCurrentChatId(chatId);
    setOptimisticMessages([]);
  };

  const handleDeleteChat = async (chatId: string) => {
    try {
      await deleteChatMutation.mutateAsync(chatId);
      if (currentChatId === chatId) {
        const remaining = chats.filter(c => c.id !== chatId);
        if (remaining.length > 0) {
          setCurrentChatId(remaining[0].id);
        } else {
          setCurrentChatId(null);
          setOptimisticMessages([]);
        }
      }
    } catch (error) {
      console.error('Failed to delete chat:', error);
    }
  };

  const handleToggleFavorite = async (chatId: string, isFavorite: boolean) => {
    try {
      await toggleFavoriteMutation.mutateAsync({ chatId, isFavorite });
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    }
  };

  const handleSendMessage = async (messageText: string) => {
    if (!currentChatId) return;
    const userMessage: Message = { type: 'sent', text: messageText, timestamp: Date.now() };
    setOptimisticMessages([...serverMessages, userMessage]);

    try {
      const data = await sendMessageMutation.mutateAsync({
        inputText: messageText,
        sessionId: currentChatId,
      });
      const botMessage: Message = { type: 'received', text: data.content, timestamp: Date.now() };
      setOptimisticMessages(prev => [...prev, botMessage]);
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
          isCreatingChat={isCreatingChat}
          newChatName={newChatName}
          onNewChatNameChange={setNewChatName}
          onCreateChatSubmit={handleCreateChatSubmit}
          onCreateChatCancel={handleCreateChatCancel}
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
