import React, { useState, useEffect, useCallback } from 'react';
import { Template } from '../types';
import * as api from '../api';
import { Button } from './ui/Button';

interface EditingState {
  id: string;
  name: string;
  prefix: string;
  postfix: string;
}

interface TemplatesProps {
  onClose: () => void;
}

const inputClass = "w-full px-3 py-2 bg-tn-bg-dark text-tn-fg border border-tn-border rounded text-sm focus:outline-none focus:ring-1 focus:ring-tn-blue placeholder:text-tn-comment";
const textareaClass = "w-full px-3 py-2 bg-tn-bg-dark text-tn-fg border border-tn-border rounded text-sm resize-y min-h-[80px] focus:outline-none focus:ring-1 focus:ring-tn-blue placeholder:text-tn-comment font-mono";

const Templates: React.FC<TemplatesProps> = ({ onClose }) => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [editing, setEditing] = useState<EditingState | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newTemplate, setNewTemplate] = useState({ name: '', prefix: '', postfix: '' });
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<string | null>(null);

  useEffect(() => {
    loadTemplates();
  }, []);

  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const loadTemplates = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await api.listTemplates();
      setTemplates(data);
    } catch (error) {
      console.error('Error loading templates:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleEdit = useCallback((template: Template) => {
    setEditing({ id: template.id, name: template.name, prefix: template.prefix, postfix: template.postfix });
    setIsCreating(false);
  }, []);

  const handleEditSave = useCallback(async () => {
    if (!editing) return;
    try {
      await api.updateTemplate(editing.id, { name: editing.name, prefix: editing.prefix, postfix: editing.postfix });
      setEditing(null);
      await loadTemplates();
    } catch (error) {
      console.error('Error updating template:', error);
    }
  }, [editing, loadTemplates]);

  const handleDelete = useCallback(async (templateId: string) => {
    if (confirmingDeleteId !== templateId) {
      setConfirmingDeleteId(templateId);
      return;
    }
    try {
      await api.deleteTemplate(templateId);
      setConfirmingDeleteId(null);
      await loadTemplates();
    } catch (error) {
      console.error('Error deleting template:', error);
    }
  }, [confirmingDeleteId, loadTemplates]);

  const handleCreateSave = useCallback(async () => {
    if (!newTemplate.name) return;
    try {
      await api.createTemplate(newTemplate.name, newTemplate.prefix, newTemplate.postfix);
      setIsCreating(false);
      setNewTemplate({ name: '', prefix: '', postfix: '' });
      await loadTemplates();
    } catch (error) {
      console.error('Error creating template:', error);
    }
  }, [newTemplate, loadTemplates]);

  const renderForm = (
    values: { name: string; prefix: string; postfix: string },
    onChange: (field: string, value: string) => void,
    onSave: () => void,
    onCancel: () => void,
    saveLabel: string,
  ) => (
    <div className="space-y-4 p-4 bg-tn-bg-highlight rounded-lg">
      <div>
        <label className="block text-xs text-tn-comment mb-1.5 uppercase tracking-wider">Name</label>
        <input
          type="text"
          value={values.name}
          onChange={(e) => onChange('name', e.target.value)}
          placeholder="Template name"
          autoFocus
          className={inputClass}
        />
      </div>
      <div>
        <label className="block text-xs text-tn-comment mb-1.5 uppercase tracking-wider">Prefix</label>
        <textarea
          value={values.prefix}
          onChange={(e) => onChange('prefix', e.target.value)}
          placeholder="System prompt prefix..."
          className={textareaClass}
        />
      </div>
      <div>
        <label className="block text-xs text-tn-comment mb-1.5 uppercase tracking-wider">Postfix</label>
        <textarea
          value={values.postfix}
          onChange={(e) => onChange('postfix', e.target.value)}
          placeholder="System prompt postfix..."
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
      <div className="relative bg-tn-bg border border-tn-border rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-tn-border">
          <h2 className="text-lg font-medium text-tn-fg">Templates</h2>
          <button
            onClick={onClose}
            className="text-tn-comment hover:text-tn-fg text-xl bg-transparent border-none cursor-pointer p-1"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {isLoading && (
            <div className="text-center py-4 text-tn-comment">Loading...</div>
          )}

          {editing && (
            <div>
              <h3 className="text-sm text-tn-fg-dark mb-3">Editing: {editing.name}</h3>
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
              {templates.map((template) => (
                <div
                  key={template.id}
                  className="flex items-center justify-between p-3 bg-tn-bg-highlight rounded-lg hover:bg-tn-selection transition-colors"
                >
                  <div className="flex-1 min-w-0 mr-4">
                    <div className="text-sm font-medium text-tn-fg">{template.name}</div>
                    <div className="text-xs text-tn-comment mt-1 truncate">
                      {template.prefix.substring(0, 80)}{template.prefix.length > 80 ? '...' : ''}
                    </div>
                  </div>
                  <div className="flex gap-2 flex-shrink-0">
                    <Button
                      variant="secondary"
                      size="compact"
                      className="px-3 py-1"
                      onClick={() => handleEdit(template)}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="secondary"
                      size="compact"
                      className={`px-3 py-1 ${confirmingDeleteId === template.id ? 'text-tn-red' : ''}`}
                      onClick={() => handleDelete(template.id)}
                    >
                      {confirmingDeleteId === template.id ? 'Confirm?' : 'Delete'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {isCreating && renderForm(
            newTemplate,
            (field, value) => setNewTemplate({ ...newTemplate, [field]: value }),
            handleCreateSave,
            () => setIsCreating(false),
            'Create',
          )}
        </div>

        <div className="flex gap-2 px-6 py-4 border-t border-tn-border">
          {!isCreating && !editing && (
            <Button
              variant="primary"
              size="compact"
              className="px-4 py-1.5"
              onClick={() => { setIsCreating(true); setNewTemplate({ name: '', prefix: '', postfix: '' }); }}
              disabled={isLoading}
            >
              New Template
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Templates;
