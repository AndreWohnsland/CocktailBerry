import { useTranslation } from 'react-i18next';
import { MdNoDrinks } from 'react-icons/md';
import { formatDate } from '../../../dateUtils';
import type { WaiterLogEntry } from '../../../types/models';
import Accordion from '../Accordion';

interface WaiterStatisticsProps {
  logs: WaiterLogEntry[];
}

function groupLogsByDateAndWaiter(logs: WaiterLogEntry[]): Record<string, Record<string, WaiterLogEntry[]>> {
  const grouped: Record<string, Record<string, WaiterLogEntry[]>> = {};
  for (const log of logs) {
    const date = log.timestamp.split(' ')[0];
    if (!grouped[date]) {
      grouped[date] = {};
    }
    if (!grouped[date][log.waiter_name]) {
      grouped[date][log.waiter_name] = [];
    }
    grouped[date][log.waiter_name].push(log);
  }
  return grouped;
}

const WaiterStatistics: React.FC<WaiterStatisticsProps> = ({ logs }) => {
  const { t, i18n } = useTranslation();

  if (logs.length === 0) {
    return <p className='text-neutral text-center mt-4'>{t('waiter.noLogs')}</p>;
  }

  const grouped = groupLogsByDateAndWaiter(logs);

  return (
    <div className='mt-2'>
      {Object.entries(grouped).map(([date, waiterGroups]) => {
        const totalCocktails = Object.values(waiterGroups).flat().length;
        const totalVolume = Object.values(waiterGroups)
          .flat()
          .reduce((sum, log) => sum + log.volume, 0);

        return (
          <Accordion
            key={date}
            title={
              <div className='flex items-center gap-3'>
                <span className='font-bold text-lg'>{formatDate(date, i18n.language)}</span>
                <span className='text-sm text-neutral'>
                  {t('waiter.statsSummary', { count: totalCocktails, volume: totalVolume })}
                </span>
              </div>
            }
          >
            {Object.entries(waiterGroups).map(([waiterName, waiterLogs]) => {
              const waiterVolume = waiterLogs.reduce((sum, log) => sum + log.volume, 0);
              return (
                <Accordion
                  key={waiterName}
                  title={
                    <div className='flex items-center gap-3'>
                      <span className='font-semibold'>{waiterName}</span>
                      <span className='text-sm text-neutral'>
                        {t('waiter.statsSummary', { count: waiterLogs.length, volume: waiterVolume })}
                      </span>
                    </div>
                  }
                >
                  <div className='grid gap-1'>
                    {waiterLogs.map((log) => (
                      <div key={log.id} className='flex items-center justify-between text-sm'>
                        <div className='flex items-center gap-2'>
                          <span className='text-neutral font-mono'>{log.timestamp.split(' ')[1]}</span>
                          <span className='text-primary font-semibold'>{log.recipe_name}</span>
                          {log.is_virgin && <MdNoDrinks className='text-secondary' size={14} />}
                        </div>
                        <span className='text-neutral'>{log.volume} ml</span>
                      </div>
                    ))}
                  </div>
                </Accordion>
              );
            })}
          </Accordion>
        );
      })}
    </div>
  );
};

export default WaiterStatistics;
