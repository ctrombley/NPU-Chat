import React from 'react';

const TypingIndicator: React.FC = () => (
  <div className="flex items-center gap-1.5 px-1 py-0.5" aria-label="Bot is typing">
    <span className="typing-dot" style={{ animationDelay: '0ms' }} />
    <span className="typing-dot" style={{ animationDelay: '160ms' }} />
    <span className="typing-dot" style={{ animationDelay: '320ms' }} />
  </div>
);

export default TypingIndicator;
