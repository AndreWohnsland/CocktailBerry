import React from 'react';
import { ignoreIssues, useIssues } from '../api/options';
import LoadingData from './common/LoadingData';
import ErrorComponent from './common/ErrorComponent';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import { FaRegClock } from 'react-icons/fa';
import { AiOutlineCloseCircle } from 'react-icons/ai';
import { executeAndShow, hasStartupIssues } from '../utils';
import { FaGear } from 'react-icons/fa6';

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
      <h1 className='text-secondary text-2xl font-bold mb-4'>{t('issues.systemIssues')}</h1>
      {hasIssues && (
        <div className='w-full mt-4 border rounded-lg border-neutral items-center justify-center flex flex-col p-2'>
          <p className='text-center text-neutral'>{t('issues.info')}</p>
          <button onClick={applyResetIssue} className='button-danger p-2 mt-2 w-full items-center justify-center flex'>
            <AiOutlineCloseCircle className='mr-3' size={22} />
            {t('issues.reset')}
          </button>
        </div>
      )}

      {issues?.internet.has_issue && (
        <div className='w-full mt-4 border rounded-lg border-neutral items-center justify-center flex flex-col p-2'>
          <h2 className='text-secondary text-center text-xl mb-2'>{t('issues.InternetConnectionIssue')}</h2>
          <p className='text-center'>{t('issues.noInternetConnection')}</p>
          <button onClick={goToTime} className='button-primary-filled p-2 mt-2 w-full items-center justify-center flex'>
            <FaRegClock className='mr-3' size={22} /> {t('issues.adjustTime')}
          </button>
        </div>
      )}
      {issues?.deprecated.has_issue && (
        <div className='w-full mt-4 border rounded-lg border-neutral items-center justify-center flex flex-col p-2'>
          <h2 className='text-secondary text-center text-xl mb-2'>{t('issues.deprecationWaring')}</h2>
          <p className='text-center'>{t('issues.systemPythonDeprecated')}</p>
        </div>
      )}
      {issues?.config.has_issue && (
        <div className='w-full mt-4 border rounded-lg border-neutral items-center justify-center flex flex-col p-2'>
          <h2 className='text-secondary text-center text-xl mb-2'>{t('issues.configIssue')}</h2>
          <p className='text-center'>{t('issues.configSetToDefault')}</p>
          <p className='text-center'>{issues.config.message}</p>
          <button
            onClick={goToConfig}
            className='button-primary-filled p-2 mt-2 w-full items-center justify-center flex'
          >
            <FaGear className='mr-3' size={22} /> {t('issues.goToConfig')}
          </button>
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
