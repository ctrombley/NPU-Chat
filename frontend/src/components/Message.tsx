import React, { useState } from 'react';
import { Message as MessageType } from '../types';
import { MessageBubble } from './ui/MessageBubble';
import TypingIndicator from './TypingIndicator';

interface MessageProps {
  message: MessageType;
}

const Message: React.FC<MessageProps> = ({ message }) => {
  const [copyFeedback, setCopyFeedback] = useState(false);

  const getCleanText = (text: string) => text.replace(/<md[^>]*>|<\/md>/g, '');

  const handleCopy = async () => {
    const text = getCleanText(message.text);
    try {
      await navigator.clipboard.writeText(text);
      setCopyFeedback(true);
      setTimeout(() => setCopyFeedback(false), 1000);
    } catch (error) {
      console.error('Failed to copy text:', error);
    }
  };

  return (
    <MessageBubble variant={message.type === 'sent' ? 'sent' : 'received'}>
      {message.isTyping ? (
        <TypingIndicator />
      ) : (
        <p className="m-0 p-0">{getCleanText(message.text)}</p>
      )}
      {message.type === 'received' && !message.isTyping && (
        <button
          className={`absolute top-2 right-2 bg-theme-highlight text-theme-fg-muted text-sm font-bold font-sans no-underline border border-theme-border rounded shadow-lg transition-all w-8 h-8 leading-5 text-center hover:text-theme-fg opacity-0 group-hover:opacity-100 ${
            copyFeedback ? 'opacity-100' : ''
          }`}
          onClick={handleCopy}
          aria-label="Copy message"
          title="Copy message"
        >
          {copyFeedback ? '\u2713' : '\u29C8'}
        </button>
      )}
    </MessageBubble>
  );
};

export default Message;
