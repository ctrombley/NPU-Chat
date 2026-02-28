import React, { useState, useEffect, useCallback } from 'react';
import { Sign } from '../types';
import * as api from '../api';
import { Button } from './ui/Button';

interface EditingState {
  id: string;
  name: string;
  prefix: string;
  postfix: string;
  values: string;
  interests: string;
  default_goal: string;
  aspects: string;
}

interface SignsProps {
  onClose: () => void;
  onNewChatWithSign?: (signId: string) => void;
}

const inputClass = "w-full px-3 py-2 bg-theme-bg text-theme-fg border border-theme-border rounded text-sm focus:outline-none focus:ring-1 focus:ring-theme-active placeholder:text-theme-fg-muted";
const textareaClass = "w-full px-3 py-2 bg-theme-bg text-theme-fg border border-theme-border rounded text-sm resize-y min-h-[80px] focus:outline-none focus:ring-1 focus:ring-theme-active placeholder:text-theme-fg-muted font-mono";

const Signs: React.FC<SignsProps> = ({ onClose, onNewChatWithSign }) => {
  const [signs, setSigns] = useState<Sign[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [editing, setEditing] = useState<EditingState | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newSign, setNewSign] = useState({ name: '', prefix: '', postfix: '', values: '', interests: '', default_goal: '', aspects: '' });
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<string | null>(null);

  useEffect(() => {
    loadSigns();
  }, []);

  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const loadSigns = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await api.listSigns();
      setSigns(data);
    } catch (error) {
      console.error('Error loading signs:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleEdit = useCallback((sign: Sign) => {
    setEditing({
      id: sign.id,
      name: sign.name,
      prefix: sign.prefix,
      postfix: sign.postfix,
      values: typeof sign.values === 'string' ? sign.values : JSON.stringify(sign.values || '', null, 2),
      interests: typeof sign.interests === 'string' ? sign.interests : JSON.stringify(sign.interests || '', null, 2),
      default_goal: sign.default_goal || '',
      aspects: typeof sign.aspects === 'string' ? sign.aspects : JSON.stringify(sign.aspects || '', null, 2),
    });
    setIsCreating(false);
  }, []);

  const handleEditSave = useCallback(async () => {
    if (!editing) return;
    try {
      await api.updateSign(editing.id, {
        name: editing.name,
        prefix: editing.prefix,
        postfix: editing.postfix,
        values: editing.values || undefined,
        interests: editing.interests || undefined,
        default_goal: editing.default_goal || undefined,
        aspects: editing.aspects || undefined,
      });
      setEditing(null);
      await loadSigns();
    } catch (error) {
      console.error('Error updating sign:', error);
    }
  }, [editing, loadSigns]);

  const handleDelete = useCallback(async (signId: string) => {
    if (confirmingDeleteId !== signId) {
      setConfirmingDeleteId(signId);
      return;
    }
    try {
      await api.deleteSign(signId);
      setConfirmingDeleteId(null);
      await loadSigns();
    } catch (error) {
      console.error('Error deleting sign:', error);
    }
  }, [confirmingDeleteId, loadSigns]);

  const handleClone = useCallback(async (signId: string) => {
    try {
      await api.cloneSign(signId);
      await loadSigns();
    } catch (error) {
      console.error('Error cloning sign:', error);
    }
  }, [loadSigns]);

  const handleNewChat = useCallback((signId: string) => {
    if (onNewChatWithSign) {
      onNewChatWithSign(signId);
      onClose();
    }
  }, [onNewChatWithSign, onClose]);

  const handleCreateSave = useCallback(async () => {
    if (!newSign.name) return;
    try {
      await api.createSign(newSign.name, newSign.prefix, newSign.postfix, {
        values: newSign.values || undefined,
        interests: newSign.interests || undefined,
        default_goal: newSign.default_goal || undefined,
        aspects: newSign.aspects || undefined,
      });
      setIsCreating(false);
      setNewSign({ name: '', prefix: '', postfix: '', values: '', interests: '', default_goal: '', aspects: '' });
      await loadSigns();
    } catch (error) {
      console.error('Error creating sign:', error);
    }
  }, [newSign, loadSigns]);

  const renderForm = (
    values: { name: string; prefix: string; postfix: string; values?: string; interests?: string; default_goal?: string; aspects?: string },
    onChange: (field: string, value: string) => void,
    onSave: () => void,
    onCancel: () => void,
    saveLabel: string,
  ) => (
    <div className="space-y-4 p-4 bg-theme-highlight rounded-lg">
      <div>
        <label className="block text-xs text-theme-fg-muted mb-1.5 uppercase tracking-wider">Name</label>
        <input
          type="text"
          value={values.name}
          onChange={(e) => onChange('name', e.target.value)}
          placeholder="Sign name"
          autoFocus
          className={inputClass}
        />
      </div>
      <div>
        <label className="block text-xs text-theme-fg-muted mb-1.5 uppercase tracking-wider">Prefix</label>
        <textarea
          value={values.prefix}
          onChange={(e) => onChange('prefix', e.target.value)}
          placeholder="System prompt prefix..."
          className={textareaClass}
        />
      </div>
      <div>
        <label className="block text-xs text-theme-fg-muted mb-1.5 uppercase tracking-wider">Postfix</label>
        <textarea
          value={values.postfix}
          onChange={(e) => onChange('postfix', e.target.value)}
          placeholder="System prompt postfix..."
          className={textareaClass}
        />
      </div>
      <div>
        <label className="block text-xs text-theme-fg-muted mb-1.5 uppercase tracking-wider">Default Goal</label>
        <input
          type="text"
          value={values.default_goal || ''}
          onChange={(e) => onChange('default_goal', e.target.value)}
          placeholder="Default goal for chats using this sign"
          className={inputClass}
        />
      </div>
      <div>
        <label className="block text-xs text-theme-fg-muted mb-1.5 uppercase tracking-wider">Values (JSON)</label>
        <textarea
          value={values.values || ''}
          onChange={(e) => onChange('values', e.target.value)}
          placeholder='e.g. ["honesty", "curiosity"]'
          className={textareaClass}
        />
      </div>
      <div>
        <label className="block text-xs text-theme-fg-muted mb-1.5 uppercase tracking-wider">Interests (JSON)</label>
        <textarea
          value={values.interests || ''}
          onChange={(e) => onChange('interests', e.target.value)}
          placeholder='e.g. ["science", "philosophy"]'
          className={textareaClass}
        />
      </div>
      <div>
        <label className="block text-xs text-theme-fg-muted mb-1.5 uppercase tracking-wider">Aspects (JSON)</label>
        <textarea
          value={values.aspects || ''}
          onChange={(e) => onChange('aspects', e.target.value)}
          placeholder='e.g. {"trust": {"description": "...", "initial": 0.5, "min": 0, "max": 1}}'
          className={textareaClass}
        />
      </div>
      <div className="flex gap-2 pt-2">
        <Button variant="primary" size="compact" className="px-4 py-1.5" onClick={onSave}>{saveLabel}</Button>
        <Button variant="secondary" size="compact" className="px-4 py-1.5" onClick={onCancel}>Cancel</Button>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-theme-bg border border-theme-border rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-theme-border">
          <h2 className="text-lg font-medium text-theme-fg">Signs</h2>
          <button
            onClick={onClose}
            className="text-theme-fg-muted hover:text-theme-fg text-xl bg-transparent border-none cursor-pointer p-1"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {isLoading && (
            <div className="text-center py-4 text-theme-fg-muted">Loading...</div>
          )}

          {editing && (
            <div>
              <h3 className="text-sm text-theme-fg mb-3">Editing: {editing.name}</h3>
              {renderForm(
                editing,
                (field, value) => setEditing({ ...editing, [field]: value }),
                handleEditSave,
                () => setEditing(null),
                'Save',
              )}
            </div>
          )}

          {!editing && !isCreating && (
            <div className="space-y-2">
              {signs.map((sign) => (
                <div
                  key={sign.id}
                  className="flex items-center justify-between p-3 bg-theme-highlight rounded-lg hover:bg-theme-active-bg transition-colors"
                >
                  <div className="flex-1 min-w-0 mr-4">
                    <div className="text-sm font-medium text-theme-fg">{sign.name}</div>
                    <div className="text-xs text-theme-fg-muted mt-1 truncate">
                      {sign.prefix.substring(0, 80)}{sign.prefix.length > 80 ? '...' : ''}
                    </div>
                  </div>
                  <div className="flex gap-2 flex-shrink-0">
                    {onNewChatWithSign && (
                      <Button
                        variant="primary"
                        size="compact"
                        className="px-3 py-1"
                        onClick={() => handleNewChat(sign.id)}
                      >
                        New Chat
                      </Button>
                    )}
                    <Button
                      variant="secondary"
                      size="compact"
                      className="px-3 py-1"
                      onClick={() => handleEdit(sign)}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="secondary"
                      size="compact"
                      className="px-3 py-1"
                      onClick={() => handleClone(sign.id)}
                    >
                      Clone
                    </Button>
                    <Button
                      variant="secondary"
                      size="compact"
                      className={`px-3 py-1 ${confirmingDeleteId === sign.id ? 'text-red-400' : ''}`}
                      onClick={() => handleDelete(sign.id)}
                    >
                      {confirmingDeleteId === sign.id ? 'Confirm?' : 'Delete'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {isCreating && renderForm(
            newSign,
            (field, value) => setNewSign({ ...newSign, [field]: value }),
            handleCreateSave,
            () => setIsCreating(false),
            'Create',
          )}
        </div>

        <div className="flex gap-2 px-6 py-4 border-t border-theme-border">
          {!isCreating && !editing && (
            <Button
              variant="primary"
              size="compact"
              className="px-4 py-1.5"
              onClick={() => { setIsCreating(true); setNewSign({ name: '', prefix: '', postfix: '', values: '', interests: '', default_goal: '', aspects: '' }); }}
              disabled={isLoading}
            >
              New Sign
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Signs;
