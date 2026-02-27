import React, { useState, useRef, useEffect } from 'react';

interface MessageInputProps {
  currentChatId: string | null;
  onMessageSent: (text: string) => void;
}

const MessageInput: React.FC<MessageInputProps> = ({ currentChatId, onMessageSent }) => {
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || !currentChatId) return;

    const text = inputText.trim();
    setIsLoading(true);
    setInputText('');

    try {
      await onMessageSent(text);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const autoExpand = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const maxHeight = 15 * (window.innerWidth / 100);
      const newHeight = Math.min(textarea.scrollHeight, maxHeight);
      textarea.style.height = newHeight + 'px';
    }
  };

  return (
    <form onSubmit={handleSubmit} className="fixed bottom-0 left-48 right-0 bg-transparent p-2.5 flex z-20 max-h-48 overflow-hidden">
      <div className="message-input-container flex flex-1">
        <textarea
          ref={textareaRef}
          name="input_text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onInput={autoExpand}
          onKeyDown={handleKeyDown}
          className="flex-1 p-4 box-border border border-purple-800 rounded-3xl resize-none overflow-y-hidden bg-gray-900 text-white text-base mr-2.5 max-h-40"
          placeholder="Chat..."
        />
        <button
          type="submit"
          className="p-3 border border-purple-800 bg-gray-900 text-purple-500 rounded-3xl cursor-pointer text-2xl mr-5 hover:text-white hover:shadow-lg hover:shadow-green-400 transition-colors"
          disabled={isLoading}
        >
          <div className={`send-icon ${isLoading ? 'hidden' : 'block'}`}>⊛</div>
          <div className={`loader ${isLoading ? 'block' : 'hidden'}`}>
            <div className="pupil"></div>
          </div>
        </button>
      </div>
    </form>
  );
};

export default MessageInput;

