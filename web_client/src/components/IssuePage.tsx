import React from 'react';
import { useTranslation } from 'react-i18next';
import { AiFillCloseCircle } from 'react-icons/ai';
import { FaRegClock } from 'react-icons/fa';
import { FaGear } from 'react-icons/fa6';
import { useNavigate } from 'react-router';
import { ignoreIssues, useIssues } from '../api/options';
import { executeAndShow, hasStartupIssues } from '../utils';
import ActionCard from './common/ActionCard';
import ErrorComponent from './common/ErrorComponent';
import LoadingData from './common/LoadingData';
import TextHeader from './common/TextHeader';

const IssuePage: React.FC = () => {
  const { data: issues, error, isLoading, refetch } = useIssues();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const applyResetIssue = async () => {
    await executeAndShow(ignoreIssues);
    await refetch();
  };

  const goToTime = async () => {
    await ignoreIssues();
    await refetch();
    navigate('/options/time');
  };

  const goToConfig = async () => {
    await ignoreIssues();
    await refetch();
    navigate('/options/configuration');
  };

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  const hasIssues = hasStartupIssues(issues);

  return (
    <div className='w-full h-full flex flex-col items-center justify-center max-w-lg p-2'>
      <TextHeader text={t('issues.systemIssues')} />
      {hasIssues && (
        <ActionCard
          header={t('issues.infoHeader')}
          sections={[t('issues.info')]}
          actionText={t('issues.reset')}
          onActionClick={applyResetIssue}
          actionIcon={AiFillCloseCircle}
          actionStyle='danger'
        />
      )}

      {issues?.internet.has_issue && (
        <ActionCard
          header={t('issues.InternetConnectionIssue')}
          sections={[t('issues.noInternetConnection')]}
          actionText={t('issues.adjustTime')}
          onActionClick={goToTime}
          actionIcon={FaRegClock}
        />
      )}
      {issues?.deprecated.has_issue && (
        <ActionCard header={t('issues.deprecationWaring')} sections={[t('issues.systemPythonDeprecated')]} />
      )}
      {issues?.config.has_issue && (
        <ActionCard
          header={t('issues.configIssue')}
          sections={[t('issues.configSetToDefault'), issues.config.message]}
          actionText={t('issues.goToConfig')}
          onActionClick={goToConfig}
          actionIcon={FaGear}
        />
      )}
      {!hasIssues && (
        <div className='items-center justify-center  flex flex-col'>
          <p className='text-center'>{t('issues.noIssues')}</p>
        </div>
      )}
    </div>
  );
};

export default IssuePage;
