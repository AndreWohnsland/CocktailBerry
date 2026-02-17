import type React from 'react';
import { useEffect, useState } from 'react';
import { useEvents } from '../../api/options';
import DropDown from '../common/DropDown';
import ErrorComponent from '../common/ErrorComponent';
import { JumpToTopButton } from '../common/JumpToTopButton';
import LoadingData from '../common/LoadingData';

const ALL_EVENT_TYPES = 'ALL';

const EventWindow: React.FC = () => {
  const { data, isLoading, error } = useEvents();
  const [selectedEventType, setSelectedEventType] = useState<string>(ALL_EVENT_TYPES);

  const handleEventTypeChange = (value: string) => {
    setSelectedEventType(value);
  };

  useEffect(() => {
    setSelectedEventType(ALL_EVENT_TYPES);
  }, []);

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  const eventData = data?.data;
  const eventTypeOptions = [ALL_EVENT_TYPES, ...(eventData?.event_keys ?? [])];

  const filteredEvents =
    selectedEventType === ALL_EVENT_TYPES
      ? (eventData?.events ?? [])
      : (eventData?.events ?? []).filter((event) => event.event_type === selectedEventType);

  const eventToString = (event: { timestamp: string; event_type: string; additional_info: string | null }): string => {
    const additionalInfo = event.additional_info ? ` | ${event.additional_info}` : '';
    return `${event.timestamp} | ${event.event_type}${additionalInfo}`;
  };

  return (
    <div className='flex flex-col w-full max-w-xl'>
      <div className='flex flex-col items-center justify-center flex-shrink-0 mb-2'>
        <div className='flex flex-row items-center w-full max-w-lg px-2'>
          <p className='text-2xl font-bold text-secondary mr-4'>Events:</p>
          <DropDown
            value={selectedEventType}
            allowedValues={eventTypeOptions}
            handleInputChange={handleEventTypeChange}
            className='mt-2 p-2'
          />
        </div>
      </div>
      <div className='flex-grow p-2'>
        {filteredEvents.map((event, index) => (
          // biome-ignore lint/suspicious/noArrayIndexKey: ordered from backend
          <div key={index} className='px-1 break-all'>
            {eventToString(event)}
          </div>
        ))}
      </div>
      <JumpToTopButton />
    </div>
  );
};

export default EventWindow;
