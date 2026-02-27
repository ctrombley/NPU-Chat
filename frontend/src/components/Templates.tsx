import React, { useState, useEffect, useCallback } from 'react';
import { Template } from '../types';
import TemplateListItem from './TemplateListItem';
import * as api from '../api';
import { Sidebar } from './ui/Sidebar';
import { Button } from './ui/Button';

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
    <Sidebar title="Templates">
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
      <Button
        variant="primary"
        onClick={handleNew}
        disabled={isLoading}
        aria-label="Create new template"
      >
        New Template
      </Button>
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
