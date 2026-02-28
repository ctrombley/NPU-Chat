import { useState, useEffect, useCallback, useRef } from 'react';
import ChatList from './components/ChatList';
import ChatMessages from './components/ChatMessages';
import MessageInput from './components/MessageInput';
import Signs from './components/Signs';
import ChatMetadataModal from './components/ChatMetadataModal';
import { Message } from './types';
import { useChats, useCreateChat, useDeleteChat, useToggleFavorite, useUpdateChat } from './hooks/useChats';
import { useMessages } from './hooks/useMessages';
import { sendMessageStream, reviewChatMetadata } from './api';
import { useQueryClient } from '@tanstack/react-query';
import { useTheme } from './hooks/useTheme';

function App() {
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [showSigns, setShowSigns] = useState(false);
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [optimisticMessages, setOptimisticMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(220);
  const isResizing = useRef(false);
  const streamingTextRef = useRef('');
  const queryClient = useQueryClient();
  const [theme, setTheme] = useTheme();

  const { data: chats = [] } = useChats();
  const { data: serverMessages = [] } = useMessages(currentChatId);
  const createChatMutation = useCreateChat();
  const deleteChatMutation = useDeleteChat();
  const toggleFavoriteMutation = useToggleFavorite();
  const updateChatMutation = useUpdateChat();

  // Select first chat when chats load and none is selected
  useEffect(() => {
    if (chats.length > 0 && !currentChatId) {
      setCurrentChatId(chats[0].id);
    }
  }, [chats, currentChatId]);

  // Show optimistic messages while streaming, otherwise show server messages
  const currentMessages = optimisticMessages.length > 0 ? optimisticMessages : serverMessages;

  // Sidebar resize handlers
  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isResizing.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing.current) return;
      const newWidth = Math.max(120, Math.min(480, e.clientX));
      setSidebarWidth(newWidth);
    };

    const handleMouseUp = () => {
      isResizing.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, []);

  const handleNewChat = async () => {
    try {
      const chatObj = await createChatMutation.mutateAsync();
      setCurrentChatId(chatObj.id);
      setOptimisticMessages([]);
    } catch (error) {
      console.error('Failed to create chat:', error);
    }
  };

  const handleNewChatWithSign = async (signId: string) => {
    try {
      const chatObj = await createChatMutation.mutateAsync({ signId });
      setCurrentChatId(chatObj.id);
      setOptimisticMessages([]);
    } catch (error) {
      console.error('Failed to create chat with sign:', error);
    }
  };

  const handleSwitchChat = (chatId: string) => {
    setCurrentChatId(chatId);
    setOptimisticMessages([]);
  };

  const handleDeleteChat = async (chatId: string) => {
    try {
      await deleteChatMutation.mutateAsync(chatId);
      queryClient.removeQueries({ queryKey: ['messages', chatId] });
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

  const handleEditChat = (chatId: string) => {
    setEditingChatId(chatId);
  };

  const handleSaveChat = async (chatId: string, attrs: { name?: string; emoji?: string; sign_id?: string; metadata?: Record<string, unknown>; goal?: string }) => {
    try {
      await updateChatMutation.mutateAsync({ chatId, attrs });
      setEditingChatId(null);
    } catch (error) {
      console.error('Failed to update chat:', error);
    }
  };

  const handleSendMessage = async (messageText: string) => {
    if (!currentChatId) return;

    const userMessage: Message = { type: 'sent', text: messageText, timestamp: Date.now() };
    const botMessage: Message = { type: 'received', text: '', timestamp: Date.now(), isTyping: true };

    // Show the user message + a typing indicator bubble immediately
    const messagesWithUser = [...serverMessages, userMessage, botMessage];
    setOptimisticMessages(messagesWithUser);
    setIsStreaming(true);
    streamingTextRef.current = '';

    // Fire shadow metadata review concurrently — updates name/emoji/theme without blocking streaming
    const shadowChatId = currentChatId;
    reviewChatMetadata(shadowChatId, messageText).then((chatUpdate) => {
      if (chatUpdate) {
        queryClient.setQueryData<typeof chats>(['chats'], (old = []) =>
          old.map(c => c.id === shadowChatId ? { ...c, ...chatUpdate } : c)
        );
      }
    }).catch(() => { /* shadow errors are non-fatal */ });

    try {
      await sendMessageStream(
        messageText,
        currentChatId,
        (chunk) => {
          // Accumulate streamed text, clear typing indicator on first chunk
          streamingTextRef.current += chunk;
          const updatedBot: Message = { ...botMessage, text: streamingTextRef.current, isTyping: false };
          setOptimisticMessages([...serverMessages, userMessage, updatedBot]);
        },
        (sessionId) => {
          // Streaming done — show server messages. Chat metadata (name/emoji) is
          // updated by the concurrent shadow POST /chats/{id}/review-metadata.
          setIsStreaming(false);
          setOptimisticMessages([]);
          streamingTextRef.current = '';
          queryClient.invalidateQueries({ queryKey: ['messages', sessionId] });
        },
      );
    } catch (error) {
      console.error('Failed to send message:', error);
      setIsStreaming(false);
      setOptimisticMessages([]);
      streamingTextRef.current = '';
    }
  };

  return (
    <div
      className={`flex h-screen bg-theme-bg text-theme-fg font-bauhaus overflow-hidden ${theme}`}
      style={{ '--sidebar-width': `${sidebarWidth}px` } as React.CSSProperties}
    >
      <ChatList
        chats={chats}
        currentChatId={currentChatId}
        onNewChat={handleNewChat}
        onSwitchChat={handleSwitchChat}
        onDeleteChat={handleDeleteChat}
        onToggleFavorite={handleToggleFavorite}
        onEditChat={handleEditChat}
        onShowSigns={() => setShowSigns(true)}
        sidebarWidth={sidebarWidth}
        theme={theme}
        onThemeChange={setTheme}
      />
      <div
        className="resize-handle"
        onMouseDown={handleResizeStart}
      />
      <ChatMessages messages={currentMessages} />
      <MessageInput
        currentChatId={currentChatId}
        onMessageSent={handleSendMessage}
        isLoading={isStreaming}
      />
      {showSigns && (
        <Signs onClose={() => setShowSigns(false)} onNewChatWithSign={handleNewChatWithSign} />
      )}
      {editingChatId && (() => {
        const editingChat = chats.find(c => c.id === editingChatId);
        return editingChat ? (
          <ChatMetadataModal
            chat={editingChat}
            onSave={handleSaveChat}
            onClose={() => setEditingChatId(null)}
          />
        ) : null;
      })()}
    </div>
  );
}

export default App;
