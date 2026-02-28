import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from './ui/Button';

interface MessageInputProps {
  currentChatId: string | null;
  onMessageSent: (text: string) => void;
  isLoading?: boolean;
}

const MessageInput: React.FC<MessageInputProps> = ({
  currentChatId,
  onMessageSent,
  isLoading = false
}) => {
  const [inputText, setInputText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || !currentChatId || isLoading) return;

    const text = inputText.trim();
    setInputText('');
    await onMessageSent(text);
  }, [inputText, currentChatId, isLoading, onMessageSent]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }, [handleSubmit]);

  const autoExpand = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const maxHeight = 15 * (window.innerWidth / 100);
      const newHeight = Math.min(textarea.scrollHeight, maxHeight);
      textarea.style.height = newHeight + 'px';
    }
  }, []);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
    autoExpand();
  }, [autoExpand]);

  const isDisabled = !currentChatId || isLoading;

  return (
    <form onSubmit={handleSubmit} aria-label="Message form" className="fixed bottom-0 right-0 bg-theme-bg/80 backdrop-blur-sm p-2.5 flex z-20 max-h-48 overflow-hidden" style={{ left: 'var(--sidebar-width, 192px)' }}>
      <div className="message-input-container flex flex-1">
        <label htmlFor="message-input" className="sr-only">
          Type your message
        </label>
        <textarea
          id="message-input"
          ref={textareaRef}
          name="input_text"
          value={inputText}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          className="flex-1 p-4 box-border border border-theme-border rounded-3xl resize-none overflow-y-hidden bg-theme-bg text-theme-fg text-base mr-2.5 max-h-40 focus:outline-none focus:ring-2 focus:ring-theme-active focus:border-theme-active placeholder:text-theme-fg-muted"
          placeholder={currentChatId ? "Chat..." : "Select a chat to start messaging"}
          disabled={isDisabled}
          aria-disabled={isDisabled}
        />
        <Button
          type="submit"
          variant="send"
          size="icon"
          className="mr-5"
          disabled={isDisabled || !inputText.trim()}
          aria-label={isLoading ? "Sending message..." : "Send message"}
        >
          {isLoading ? (
            <div className="loader"></div>
          ) : (
            <div className="send-icon">⊛</div>
          )}
        </Button>
      </div>
    </form>
  );
};

export default MessageInput;
