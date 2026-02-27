import React, { useEffect, useRef } from 'react';
import { Message as MessageType } from '../types';
import Message from './Message';

interface ChatMessagesProps {
  messages: MessageType[];
}

const ChatMessages: React.FC<ChatMessagesProps> = ({ messages }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-messages flex-1 overflow-y-auto overflow-x-hidden mb-16 relative" data-testid="chat-messages">
      <div className="absolute inset-0 bg-chat-bg opacity-10 radial-gradient"></div>
      <div className="relative">
        {messages.map((message, index) => (
          <Message key={index} message={message} />
        ))}
        <div ref={messagesEndRef} data-testid="messages-end" />
      </div>
    </div>
  );
};

export default ChatMessages;

