import React, { useState, useEffect } from 'react';
import { Template } from '../types';

interface TemplatesProps {
  onBack: () => void;
}

const Templates: React.FC<TemplatesProps> = ({ onBack }) => {
  const [templates, setTemplates] = useState<Template[]>([]);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await fetch('/templates');
      const data = await response.json();
      setTemplates(data);
    } catch (error) {
      console.error('Error loading templates:', error);
    }
  };

  const handleEdit = async (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (!template) return;

    const newName = prompt('Enter new name:', template.name);
    const newPrefix = prompt('Enter new prefix:', template.prefix);
    const newPostfix = prompt('Enter new postfix:', template.postfix);

    if (newName && newPrefix !== null && newPostfix !== null) {
      try {
        await fetch(`/templates/${templateId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: newName, prefix: newPrefix, postfix: newPostfix }),
        });
        loadTemplates();
      } catch (error) {
        console.error('Error updating template:', error);
      }
    }
  };

  const handleDelete = async (templateId: string) => {
    if (confirm('Delete this template?')) {
      try {
        await fetch(`/templates/${templateId}`, { method: 'DELETE' });
        loadTemplates();
      } catch (error) {
        console.error('Error deleting template:', error);
      }
    }
  };

  const handleNew = () => {
    const name = prompt('Enter template name:');
    const prefix = prompt('Enter prefix:');
    const postfix = prompt('Enter postfix:');

    if (name && prefix !== null && postfix !== null) {
      fetch('/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, prefix, postfix }),
      })
        .then(() => loadTemplates())
        .catch(error => console.error('Error creating template:', error));
    }
  };

  return (
    <div className="w-48 h-full bg-sidebar-bg border-r border-gray-600 overflow-y-auto z-10">
      <h3 className="m-2.5 text-white text-base border-b border-gray-600 pb-1.5">
        Templates
      </h3>
      <ul className="list-none p-0 m-0">
        {templates.map((template) => (
          <li
            key={template.id}
            className="flex justify-between items-center p-2.5 cursor-pointer border-b border-gray-600 transition-colors hover:bg-gray-700"
          >
            <span className="text-sm">{template.name}</span>
            <div>
              <button
                className="mr-1 bg-gray-600 text-white border-none rounded px-1 py-0.5 cursor-pointer text-xs"
                onClick={() => handleEdit(template.id)}
              >
                Edit
              </button>
              <button
                className="bg-none border-none text-gray-500 cursor-pointer px-1 py-0.5 rounded transition-colors hover:text-red-400 hover:bg-gray-600"
                onClick={() => handleDelete(template.id)}
              >
                ×
              </button>
            </div>
          </li>
        ))}
      </ul>
      <button
        className="w-full p-2.5 m-2.5 bg-accent text-white border-none rounded cursor-pointer text-sm transition-colors hover:bg-accent-hover"
        onClick={handleNew}
      >
        New Template
      </button>
      <button
        className="w-full p-2.5 m-2.5 bg-gray-600 text-white border-none rounded cursor-pointer text-sm transition-colors hover:bg-gray-700"
        onClick={onBack}
      >
        Back to Chats
      </button>
    </div>
  );
};

export default Templates;

