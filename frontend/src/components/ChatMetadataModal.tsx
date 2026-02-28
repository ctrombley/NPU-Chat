import React, { useState, useEffect } from 'react';
import { Chat, Sign } from '../types';
import * as api from '../api';
import { Button } from './ui/Button';

interface ChatMetadataModalProps {
  chat: Chat;
  onSave: (chatId: string, attrs: { name?: string; emoji?: string; sign_id?: string; metadata?: Record<string, unknown>; goal?: string }) => void;
  onClose: () => void;
}

type ViewMode = 'form' | 'json';

const inputClass = "w-full px-3 py-2 bg-theme-bg text-theme-fg border border-theme-border rounded text-sm focus:outline-none focus:ring-1 focus:ring-theme-active placeholder:text-theme-fg-muted";
const textareaClass = "w-full px-3 py-2 bg-theme-bg text-theme-fg border border-theme-border rounded text-sm resize-y min-h-[120px] focus:outline-none focus:ring-1 focus:ring-theme-active placeholder:text-theme-fg-muted font-mono";
const selectClass = "w-full px-3 py-2 bg-theme-bg text-theme-fg border border-theme-border rounded text-sm focus:outline-none focus:ring-1 focus:ring-theme-active";

const ChatMetadataModal: React.FC<ChatMetadataModalProps> = ({ chat, onSave, onClose }) => {
  const [viewMode, setViewMode] = useState<ViewMode>('form');
  const [name, setName] = useState(chat.name || '');
  const [emoji, setEmoji] = useState(chat.emoji || '');
  const [signId, setSignId] = useState(chat.sign_id || 'default');
  const [goal, setGoal] = useState(chat.goal || '');
  const [signs, setSigns] = useState<Sign[]>([]);
  const [jsonText, setJsonText] = useState('');
  const [jsonError, setJsonError] = useState('');

  useEffect(() => {
    api.listSigns().then(setSigns).catch(console.error);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Sync JSON text when switching to JSON view
  useEffect(() => {
    if (viewMode === 'json') {
      setJsonText(JSON.stringify({ name, emoji, sign_id: signId, goal, metadata: chat.metadata || {} }, null, 2));
      setJsonError('');
    }
  }, [viewMode]);

  const handleSave = () => {
    if (viewMode === 'json') {
      try {
        const parsed = JSON.parse(jsonText);
        onSave(chat.id, {
          name: parsed.name,
          emoji: parsed.emoji,
          sign_id: parsed.sign_id,
          goal: parsed.goal,
          metadata: parsed.metadata,
        });
      } catch {
        setJsonError('Invalid JSON. Please check your syntax.');
        return;
      }
    } else {
      onSave(chat.id, { name, emoji, sign_id: signId, goal });
    }
  };

  const chart = (chat.metadata?.chart || {}) as Record<string, number>;
  const chartEntries = Object.entries(chart);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-theme-bg border border-theme-border rounded-xl shadow-2xl w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-theme-border">
          <h2 className="text-lg font-medium text-theme-fg">Edit Chat</h2>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setViewMode(viewMode === 'form' ? 'json' : 'form')}
              className="text-xs px-2 py-1 rounded bg-theme-highlight text-theme-fg-muted hover:text-theme-fg border border-theme-border cursor-pointer"
            >
              {viewMode === 'form' ? 'JSON' : 'Form'}
            </button>
            <button
              onClick={onClose}
              className="text-theme-fg-muted hover:text-theme-fg text-xl bg-transparent border-none cursor-pointer p-1"
              aria-label="Close"
            >
              ×
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {viewMode === 'form' ? (
            <>
              <div>
                <label className="block text-xs text-theme-fg-muted mb-1.5 uppercase tracking-wider">Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Chat name"
                  autoFocus
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs text-theme-fg-muted mb-1.5 uppercase tracking-wider">Emoji</label>
                <input
                  type="text"
                  value={emoji}
                  onChange={(e) => setEmoji(e.target.value)}
                  placeholder="e.g. 💬"
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs text-theme-fg-muted mb-1.5 uppercase tracking-wider">Sign</label>
                <select
                  value={signId}
                  onChange={(e) => setSignId(e.target.value)}
                  className={selectClass}
                >
                  {signs.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-theme-fg-muted mb-1.5 uppercase tracking-wider">Goal</label>
                <input
                  type="text"
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  placeholder="Chat goal"
                  className={inputClass}
                />
              </div>
              {chartEntries.length > 0 && (
                <div>
                  <label className="block text-xs text-theme-fg-muted mb-1.5 uppercase tracking-wider">Chart</label>
                  <div className="space-y-2">
                    {chartEntries.map(([aspect, value]) => (
                      <div key={aspect} className="flex items-center gap-3">
                        <span className="text-xs text-theme-fg-muted w-24 truncate capitalize">{aspect}</span>
                        <div className="flex-1 h-2 bg-theme-highlight rounded-full overflow-hidden">
                          <div
                            className="h-full bg-theme-active rounded-full transition-all"
                            style={{ width: `${Math.round(Number(value) * 100)}%` }}
                          />
                        </div>
                        <span className="text-xs text-theme-fg-muted w-10 text-right">{Math.round(Number(value) * 100)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {chat.metadata?.theme && (
                <div>
                  <label className="block text-xs text-theme-fg-muted mb-1.5 uppercase tracking-wider">Theme</label>
                  <p className="text-theme-fg-muted text-sm italic">{String(chat.metadata.theme)}</p>
                </div>
              )}
            </>
          ) : (
            <>
              <textarea
                value={jsonText}
                onChange={(e) => { setJsonText(e.target.value); setJsonError(''); }}
                className={textareaClass}
              />
              {jsonError && (
                <div className="text-sm text-red-400">{jsonError}</div>
              )}
            </>
          )}
        </div>

        <div className="flex gap-2 px-6 py-4 border-t border-theme-border">
          <Button variant="primary" size="compact" className="px-4 py-1.5" onClick={handleSave}>
            Save
          </Button>
          <Button variant="secondary" size="compact" className="px-4 py-1.5" onClick={onClose}>
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatMetadataModal;
