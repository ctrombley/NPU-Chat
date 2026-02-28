import React, { useState } from 'react';
import { Message as MessageType } from '../types';
import { MessageBubble } from './ui/MessageBubble';

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
      <p className="m-0 p-0">{getCleanText(message.text)}</p>
      {message.type === 'received' && (
        <button
          className={`p-2.5 inline-block bg-tn-bg-highlight text-tn-comment text-lg font-bold font-sans no-underline border border-tn-border rounded shadow-lg transition-all w-10 h-10 leading-5 text-center hover:text-tn-fg ${
            copyFeedback ? 'animate' : ''
          }`}
          onClick={handleCopy}
          aria-label="Copy message"
          title="Copy message"
        >
          ⧈
        </button>
      )}
    </MessageBubble>
  );
};

export default Message;
