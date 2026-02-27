import type { IconType } from 'react-icons';
import { FaPen, FaPlus, FaTrashAlt } from 'react-icons/fa';
import Button from '../Button';

interface ModalActionsProps {
  onDelete: () => void;
  onSave: () => void;
  isNew: boolean;
  deleteDisabled?: boolean;
  saveDisabled?: boolean;
  deleteLabel?: string;
  saveLabel?: string;
  createLabel?: string;
  deleteIcon?: IconType;
  saveIcon?: IconType;
  createIcon?: IconType;
}

const ModalActions = ({
  onDelete,
  onSave,
  isNew,
  deleteDisabled = false,
  saveDisabled = false,
  deleteLabel = 'delete',
  saveLabel = 'apply',
  createLabel = 'create',
  deleteIcon = FaTrashAlt,
  saveIcon = FaPen,
  createIcon = FaPlus,
}: ModalActionsProps) => {
  return (
    <>
      <Button
        style='danger'
        filled
        icon={deleteIcon}
        label={deleteLabel}
        disabled={deleteDisabled}
        onClick={onDelete}
      />
      <Button
        filled
        icon={isNew ? createIcon : saveIcon}
        label={isNew ? createLabel : saveLabel}
        disabled={saveDisabled}
        onClick={onSave}
      />
    </>
  );
};

export default ModalActions;
