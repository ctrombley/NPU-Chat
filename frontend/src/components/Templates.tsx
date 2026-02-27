import React, { useState, useEffect, useCallback } from 'react';
import { Template } from '../types';
import TemplateListItem from './TemplateListItem';
import * as api from '../api';

interface TemplatesProps {
  onBack: () => void;
}

const Templates: React.FC<TemplatesProps> = ({ onBack }) => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoading, setIsLoading] = useState(false);

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

  const handleEdit = useCallback(async (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (!template) return;

    const newName = prompt('Enter new name:', template.name);
    const newPrefix = prompt('Enter new prefix:', template.prefix);
    const newPostfix = prompt('Enter new postfix:', template.postfix);

    if (newName && newPrefix !== null && newPostfix !== null) {
      try {
        await api.updateTemplate(templateId, { name: newName, prefix: newPrefix!, postfix: newPostfix! });
        await loadTemplates();
      } catch (error) {
        console.error('Error updating template:', error);
      }
    }
  }, [templates, loadTemplates]);

  const handleDelete = useCallback(async (templateId: string) => {
    if (!confirm('Delete this template?')) return;

    try {
      await api.deleteTemplate(templateId);
      await loadTemplates();
    } catch (error) {
      console.error('Error deleting template:', error);
    }
  }, [loadTemplates]);

  const handleNew = useCallback(async () => {
    const name = prompt('Enter template name:');
    const prefix = prompt('Enter prefix:');
    const postfix = prompt('Enter postfix:');

    if (name && prefix !== null && postfix !== null) {
      try {
        await api.createTemplate(name, prefix!, postfix!);
        await loadTemplates();
      } catch (error) {
        console.error('Error creating template:', error);
      }
    }
  }, [loadTemplates]);

  return (
    <div className="w-48 h-full bg-sidebar-bg border-r border-gray-600 overflow-y-auto z-10">
      <h3 className="m-2.5 text-white text-base border-b border-gray-600 pb-1.5">
        Templates
      </h3>
      {isLoading && (
        <div className="text-center py-4 text-gray-400">Loading...</div>
      )}
      <ul className="list-none p-0 m-0">
        {templates.map((template) => (
          <TemplateListItem
            key={template.id}
            template={template}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        ))}
      </ul>
      <button
        className="w-full p-2.5 m-2.5 bg-accent text-white border-none rounded cursor-pointer text-sm transition-colors hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed"
        onClick={handleNew}
        disabled={isLoading}
        aria-label="Create new template"
      >
        New Template
      </button>
      <button
        className="w-full p-2.5 m-2.5 bg-gray-600 text-white border-none rounded cursor-pointer text-sm transition-colors hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
        onClick={onBack}
        disabled={isLoading}
        aria-label="Back to chats"
      >
        Back to Chats
      </button>
    </div>
  );
};

export default Templates;
