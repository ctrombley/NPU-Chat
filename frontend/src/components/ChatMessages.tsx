import React, { useEffect, useRef } from 'react';
import { Message } from '../types';

interface ChatMessagesProps {
  messages: Message[];
}

const ChatMessages: React.FC<ChatMessagesProps> = ({ messages }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-messages flex-1 overflow-y-auto overflow-x-hidden mb-16 relative">
      <div className="absolute inset-0 bg-chat-bg opacity-10 radial-gradient"></div>
      <div className="relative">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`block m-2.5 p-2.5 text-white bg-transparent rounded-lg ${
              message.type === 'sent'
                ? 'bg-message-sent w-11/12 max-w-11/12 ml-auto mr-0 border-l-2 border-black border-t border-black rounded-tl-3xl rounded-bl-3xl shadow-lg text-left word-wrap break-words pl-5'
                : 'bg-message-received w-4/5 shadow-lg border-r-2 border-black border-t border-black rounded-tr-3xl rounded-br-3xl pt-1.5 pr-20 mr-12 mb-5 word-wrap break-words text-left'
            }`}
          >
            {message.type === 'received' && /<\\w+/.test(message.text) ? (
              <div dangerouslySetInnerHTML={{ __html: message.text }} />
            ) : (
              <p className="m-0 p-0">{message.text}</p>
            )}
            {message.type === 'received' && (
              <button
                className="p-2.5 inline-block bg-gray-600 text-gray-300 text-lg font-bold font-sans no-underline border border-black rounded shadow-lg transition-all w-10 h-10 leading-5 text-center"
                onClick={(e) => {
                  const target = e.target as HTMLElement;
                  const messageDiv = target.parentElement;
                  if (messageDiv) {
                    const mdElement = messageDiv.querySelector('md');
                    const text = mdElement?.textContent || messageDiv.textContent || '';
                    navigator.clipboard.writeText(text);
                    target.classList.add('animate');
                    setTimeout(() => target.classList.remove('animate'), 1000);
                  }
                }}
              >
                ⧈
              </button>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatMessages;

