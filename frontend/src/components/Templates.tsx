import React, { useState, useEffect, useCallback } from 'react';
import { Template } from '../types';
import TemplateListItem from './TemplateListItem';
import * as api from '../api';
import { Sidebar } from './ui/Sidebar';
import { Button } from './ui/Button';

interface EditingState {
  id: string;
  name: string;
  prefix: string;
  postfix: string;
}

interface TemplatesProps {
  onBack: () => void;
}

const Templates: React.FC<TemplatesProps> = ({ onBack }) => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [editing, setEditing] = useState<EditingState | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newTemplate, setNewTemplate] = useState({ name: '', prefix: '', postfix: '' });
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<string | null>(null);

  useEffect(() => {
    loadTemplates();
  }, []);

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

  const handleEdit = useCallback((templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (!template) return;
    setEditing({ id: template.id, name: template.name, prefix: template.prefix, postfix: template.postfix });
  }, [templates]);

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

  const handleNew = useCallback(() => {
    setIsCreating(true);
    setNewTemplate({ name: '', prefix: '', postfix: '' });
  }, []);

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

  return (
    <Sidebar title="Templates">
      {isLoading && (
        <div className="text-center py-4 text-gray-400">Loading...</div>
      )}

      {editing && (
        <div className="p-2 mb-2 bg-gray-700 rounded space-y-2">
          <input
            type="text"
            value={editing.name}
            onChange={(e) => setEditing({ ...editing, name: e.target.value })}
            placeholder="Name"
            className="w-full px-2 py-1 bg-gray-600 text-white border border-gray-500 rounded text-sm"
          />
          <input
            type="text"
            value={editing.prefix}
            onChange={(e) => setEditing({ ...editing, prefix: e.target.value })}
            placeholder="Prefix"
            className="w-full px-2 py-1 bg-gray-600 text-white border border-gray-500 rounded text-sm"
          />
          <input
            type="text"
            value={editing.postfix}
            onChange={(e) => setEditing({ ...editing, postfix: e.target.value })}
            placeholder="Postfix"
            className="w-full px-2 py-1 bg-gray-600 text-white border border-gray-500 rounded text-sm"
          />
          <div className="flex gap-2">
            <Button variant="primary" onClick={handleEditSave}>Save</Button>
            <Button variant="secondary" onClick={() => setEditing(null)}>Cancel</Button>
          </div>
        </div>
      )}

      <ul className="list-none p-0 m-0">
        {templates.map((template) => (
          <TemplateListItem
            key={template.id}
            template={template}
            onEdit={handleEdit}
            onDelete={handleDelete}
            isConfirmingDelete={confirmingDeleteId === template.id}
          />
        ))}
      </ul>

      {isCreating ? (
        <div className="p-2 mb-2 bg-gray-700 rounded space-y-2">
          <input
            type="text"
            value={newTemplate.name}
            onChange={(e) => setNewTemplate({ ...newTemplate, name: e.target.value })}
            placeholder="Template name"
            autoFocus
            className="w-full px-2 py-1 bg-gray-600 text-white border border-gray-500 rounded text-sm"
          />
          <input
            type="text"
            value={newTemplate.prefix}
            onChange={(e) => setNewTemplate({ ...newTemplate, prefix: e.target.value })}
            placeholder="Prefix"
            className="w-full px-2 py-1 bg-gray-600 text-white border border-gray-500 rounded text-sm"
          />
          <input
            type="text"
            value={newTemplate.postfix}
            onChange={(e) => setNewTemplate({ ...newTemplate, postfix: e.target.value })}
            placeholder="Postfix"
            className="w-full px-2 py-1 bg-gray-600 text-white border border-gray-500 rounded text-sm"
          />
          <div className="flex gap-2">
            <Button variant="primary" onClick={handleCreateSave}>Create</Button>
            <Button variant="secondary" onClick={() => setIsCreating(false)}>Cancel</Button>
          </div>
        </div>
      ) : (
        <Button
          variant="primary"
          onClick={handleNew}
          disabled={isLoading}
          aria-label="Create new template"
        >
          New Template
        </Button>
      )}
      <Button
        variant="secondary"
        onClick={onBack}
        disabled={isLoading}
        aria-label="Back to chats"
      >
        Back to Chats
      </Button>
    </Sidebar>
  );
};

export default Templates;
