import type React from 'react';
import { useTranslation } from 'react-i18next';
import Modal from 'react-modal';
import { useConfig } from '../../providers/ConfigProvider';
import TextHeader from '../common/TextHeader';

interface TeamSelectionProps {
  isOpen: boolean;
  amount: number;
  prepareCocktail: (amount: number, teamName: string) => void;
  onClose: () => void;
}

const TeamSelection: React.FC<TeamSelectionProps> = ({ isOpen, amount, prepareCocktail, onClose }) => {
  const { config } = useConfig();
  const { t } = useTranslation();

  const handleTeamSelection = (teamName: string) => {
    prepareCocktail(amount, teamName);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} className='modal slim h-fit' overlayClassName='overlay z-30'>
      <div className='flex flex-col items-center justify-center w-full h-full'>
        <TextHeader text={t('cocktails.selectTeam')} />
        <div className='flex-grow'></div>
        <div className='grid gap-2 sm:grid-cols-2 grid-cols-1 w-full h-full'>
          {config.TEAM_BUTTON_NAMES.map((teamName, index) => {
            const buttonClasses = ['button-primary-filled', 'button-secondary-filled', 'button-neutral-filled'];
            const buttonClass = buttonClasses[index % buttonClasses.length];
            return (
              <button
                type='button'
                key={teamName}
                className={`${buttonClass} p-2 w-full h-full text-xl`}
                onClick={() => handleTeamSelection(teamName)}
              >
                {teamName}
              </button>
            );
          })}
        </div>
        <div className='flex-grow'></div>
      </div>
    </Modal>
  );
};

export default TeamSelection;
