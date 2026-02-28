import React, { useState, useEffect } from 'react';
import { Chat, Template } from '../types';
import * as api from '../api';
import { Button } from './ui/Button';

interface ChatMetadataModalProps {
  chat: Chat;
  onSave: (chatId: string, attrs: { name?: string; emoji?: string; template_id?: string; metadata?: Record<string, unknown> }) => void;
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
  const [templateId, setTemplateId] = useState(chat.template_id || 'default');
  const [templates, setTemplates] = useState<Template[]>([]);
  const [jsonText, setJsonText] = useState('');
  const [jsonError, setJsonError] = useState('');

  useEffect(() => {
    api.listTemplates().then(setTemplates).catch(console.error);
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
      setJsonText(JSON.stringify({ name, emoji, template_id: templateId, metadata: chat.metadata || {} }, null, 2));
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
          template_id: parsed.template_id,
          metadata: parsed.metadata,
        });
      } catch {
        setJsonError('Invalid JSON. Please check your syntax.');
        return;
      }
    } else {
      onSave(chat.id, { name, emoji, template_id: templateId });
    }
  };

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
                <label className="block text-xs text-theme-fg-muted mb-1.5 uppercase tracking-wider">Template</label>
                <select
                  value={templateId}
                  onChange={(e) => setTemplateId(e.target.value)}
                  className={selectClass}
                >
                  {templates.map((t) => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </div>
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
