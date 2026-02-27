import React, { useState } from 'react';
import { Message as MessageType } from '../types';
import { MessageBubble } from './ui/MessageBubble';

interface MessageProps {
  message: MessageType;
}

const Message: React.FC<MessageProps> = ({ message }) => {
  const [copyFeedback, setCopyFeedback] = useState(false);

  const handleCopy = async () => {
    const text = message.text.replace(/<md[^>]*>|<\/md>/g, '');
    try {
      await navigator.clipboard.writeText(text);
      setCopyFeedback(true);
      setTimeout(() => setCopyFeedback(false), 1000);
    } catch (error) {
      console.error('Failed to copy text:', error);
    }
  };

  const renderMessageContent = () => {
    if (message.type === 'received' && /<md[^>]*>/.test(message.text)) {
      return <div dangerouslySetInnerHTML={{ __html: message.text }} />;
    }
    return <p className="m-0 p-0">{message.text}</p>;
  };

  return (
    <MessageBubble variant={message.type === 'sent' ? 'sent' : 'received'}>
      {renderMessageContent()}
      {message.type === 'received' && (
        <button
          className={`p-2.5 inline-block bg-gray-600 text-gray-300 text-lg font-bold font-sans no-underline border border-black rounded shadow-lg transition-all w-10 h-10 leading-5 text-center ${
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
