import React from 'react';
import { Sign } from '../types';
import { ListItem } from './ui/ListItem';
import { Button, IconButton } from './ui/Button';

interface SignListItemProps {
  sign: Sign;
  onEdit: (signId: string) => void;
  onDelete: (signId: string) => void;
  isConfirmingDelete?: boolean;
}

const SignListItem: React.FC<SignListItemProps> = ({
  sign,
  onEdit,
  onDelete,
  isConfirmingDelete,
}) => {
  return (
    <ListItem>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-theme-fg truncate">{sign.name}</div>
        <div className="text-xs text-theme-fg-muted mt-1">
          <div className="truncate">Prefix: {sign.prefix}</div>
          <div className="truncate">Postfix: {sign.postfix}</div>
        </div>
      </div>
      <div className="flex gap-1 ml-2">
        <Button
          variant="secondary"
          size="compact"
          className="mr-1"
          onClick={() => onEdit(sign.id)}
          aria-label={`Edit sign ${sign.name}`}
        >
          Edit
        </Button>
        <IconButton
          variant="danger"
          className="px-1 py-0.5"
          onClick={() => onDelete(sign.id)}
          aria-label={`Delete sign ${sign.name}`}
        >
          {isConfirmingDelete ? 'Confirm?' : '×'}
        </IconButton>
      </div>
    </ListItem>
  );
};

export default SignListItem;
