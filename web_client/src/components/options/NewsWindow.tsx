import type React from 'react';
import { useTranslation } from 'react-i18next';
import { FaCheckCircle } from 'react-icons/fa';
import { useMutation, useQueryClient } from 'react-query';
import { acknowledgeNews, useNews } from '../../api/options';
import { executeAndShow } from '../../utils';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import TextHeader from '../common/TextHeader';

const NewsWindow: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, error } = useNews();
  const queryClient = useQueryClient();

  const acknowledgeMutation = useMutation(acknowledgeNews, {
    onSuccess: () => {
      // Invalidate and refetch news query to update the list
      queryClient.invalidateQueries('news');
    },
  });

  const handleAcknowledge = async (newsKey: string) => {
    await executeAndShow(() => acknowledgeMutation.mutateAsync(newsKey));
  };

  if (isLoading) {
    return <LoadingData />;
  }

  if (error) {
    return <ErrorComponent error={error} />;
  }

  const newsEntries = Object.entries(data || {});
  const hasNews = newsEntries.length > 0;

  return (
    <div className='flex flex-col items-center max-w-5xl w-full p-2 pt-0'>
      <TextHeader text={t('options.news')} space={4} />
      
      {!hasNews && (
        <div className='w-full p-8 text-center text-neutral text-lg'>
          {t('news.noNews')}
        </div>
      )}

      {hasNews && (
        <div className='w-full space-y-4'>
          {newsEntries.map(([key, content]) => (
            <div key={key} className='card p-4 border-2 border-neutral rounded-lg'>
              <p className='text-base mb-4 whitespace-pre-wrap'>{content}</p>
              <button
                type='button'
                onClick={() => handleAcknowledge(key)}
                className='btn-primary w-full flex items-center justify-center gap-2'
                disabled={acknowledgeMutation.isLoading}
              >
                <FaCheckCircle />
                {t('news.acknowledge')}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default NewsWindow;
