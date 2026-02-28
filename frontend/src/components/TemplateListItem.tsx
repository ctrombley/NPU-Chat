import React from 'react';
import { Template } from '../types';
import { ListItem } from './ui/ListItem';
import { Button, IconButton } from './ui/Button';

interface TemplateListItemProps {
  template: Template;
  onEdit: (templateId: string) => void;
  onDelete: (templateId: string) => void;
  isConfirmingDelete?: boolean;
}

const TemplateListItem: React.FC<TemplateListItemProps> = ({
  template,
  onEdit,
  onDelete,
  isConfirmingDelete,
}) => {
  return (
    <ListItem>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-tn-fg truncate">{template.name}</div>
        <div className="text-xs text-tn-comment mt-1">
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
          {isConfirmingDelete ? 'Confirm?' : '×'}
        </IconButton>
      </div>
    </ListItem>
  );
};

export default TemplateListItem;
