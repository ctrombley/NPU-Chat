import React from 'react';
import { Template } from '../types';
import { ListItem } from './ui/ListItem';
import { Button, IconButton } from './ui/Button';

interface TemplateListItemProps {
  template: Template;
  onEdit: (templateId: string) => void;
  onDelete: (templateId: string) => void;
}

const TemplateListItem: React.FC<TemplateListItemProps> = ({
  template,
  onEdit,
  onDelete,
}) => {
  return (
    <ListItem>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-white truncate">{template.name}</div>
        <div className="text-xs text-gray-400 mt-1">
          <div className="truncate">Prefix: {template.prefix}</div>
          <div className="truncate">Postfix: {template.postfix}</div>
        </div>
      </div>
      <div className="flex gap-1 ml-2">
        <Button
          variant="secondary"
          size="compact"
          className="mr-1"
          onClick={() => onEdit(template.id)}
          aria-label={`Edit template ${template.name}`}
        >
          Edit
        </Button>
        <IconButton
          variant="danger"
          className="px-1 py-0.5"
          onClick={() => onDelete(template.id)}
          aria-label={`Delete template ${template.name}`}
        >
          ×
        </IconButton>
      </div>
    </ListItem>
  );
};

export default TemplateListItem;
