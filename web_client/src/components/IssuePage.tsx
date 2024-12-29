import React from 'react';
import { resetIssue, useIssues } from '../api/options';
import LoadingData from './common/LoadingData';
import ErrorComponent from './common/ErrorComponent';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import { FaRegClock } from 'react-icons/fa';
import { AiOutlineCloseCircle } from 'react-icons/ai';

const IssuePage: React.FC = () => {
  const { data: issues, error, isLoading, refetch } = useIssues();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const applyResetIssue = async () => {
    await resetIssue();
    await refetch();
  };

  const goToTime = async () => {
    await applyResetIssue();
    navigate('/options/time');
  };

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  const hasIssues = issues?.deprecated || issues?.internet;

  return (
    <div className='w-full h-full flex flex-col items-center justify-center max-w-lg p-2'>
      <h1 className='text-secondary text-2xl font-bold mb-4'>{t('issues.systemIssues')}</h1>
      {hasIssues && (
        <div className='mt-4 border rounded-lg border-neutral items-center justify-center flex flex-col p-2'>
          <p className='text-center text-neutral'>{t('issues.info')}</p>
          <button onClick={applyResetIssue} className='button-danger p-2 mt-2 w-full items-center justify-center flex'>
            <AiOutlineCloseCircle className='mr-3' size={22} />
            {t('issues.reset')}
          </button>
        </div>
      )}

      {issues?.internet && (
        <div className='mt-4 border rounded-lg border-neutral items-center justify-center flex flex-col p-2'>
          <h2 className='text-secondary text-center text-xl mb-2'>{t('issues.InternetConnectionIssue')}</h2>
          <p className='text-center'>{t('issues.noInternetConnection')}</p>
          <button onClick={goToTime} className='button-primary-filled p-2 mt-2 w-full items-center justify-center flex'>
            <FaRegClock className='mr-3' size={22} /> {t('issues.adjustTime')}
          </button>
        </div>
      )}
      {issues?.deprecated && (
        <div className='mt-4 border rounded-lg border-neutral items-center justify-center flex flex-col p-2'>
          <h2 className='text-secondary text-center text-xl mb-2'>{t('issues.deprecationWaring')}</h2>
          <p className='text-center'>{t('issues.systemPythonDeprecated')}</p>
        </div>
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
