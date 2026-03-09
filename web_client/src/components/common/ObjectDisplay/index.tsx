import { useEffect, useMemo, useRef, useState } from 'react';

interface ObjectDisplayProps {
  children: React.ReactNode[];
}

/** Determine the best number of columns so rows are evenly filled.
 *  maxPerRow is the upper bound (based on screen width), itemCount the total items.
 *  Returns a value <= maxPerRow where itemCount % cols === 0, or the best fit. */
const evenColumns = (itemCount: number, maxPerRow: number): number => {
  if (itemCount <= maxPerRow) return itemCount;
  // prefer a divisor of itemCount that is <= maxPerRow for perfectly even rows
  for (let cols = maxPerRow; cols >= 2; cols--) {
    if (itemCount % cols === 0) return cols;
  }
  // fallback: pick cols that minimizes the difference between row sizes
  let best = maxPerRow;
  let bestDiff = maxPerRow;
  for (let cols = maxPerRow; cols >= 2; cols--) {
    const rows = Math.ceil(itemCount / cols);
    const lastRow = itemCount - cols * (rows - 1);
    const diff = cols - lastRow;
    if (diff < bestDiff) {
      bestDiff = diff;
      best = cols;
    }
  }
  return best;
};

const ObjectDisplay = ({ children }: ObjectDisplayProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(0);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerWidth(entry.contentRect.width);
      }
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Max items that fit per row based on the container's own width
  const maxItemsPerRow = useMemo(() => {
    if (containerWidth < 480) return 4;
    if (containerWidth < 768) return 5;
    return 6;
  }, [containerWidth]);

  const cols = evenColumns(children.length, maxItemsPerRow);
  const remainder = children.length % cols;
  const gridChildren = remainder === 0 ? children : children.slice(0, -remainder);
  const lastRowChildren = remainder === 0 ? [] : children.slice(-remainder);

  return (
    <div ref={containerRef} className='w-full flex flex-col gap-y-1'>
      {gridChildren.length > 0 && (
        <div className='grid w-full' style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}>
          {gridChildren.map((child, index) => (
            // biome-ignore lint/suspicious/noArrayIndexKey: items are always ordered here
            <div key={index} className='flex items-center w-full'>
              {child}
            </div>
          ))}
        </div>
      )}
      {lastRowChildren.length > 0 && (
        <div className='flex w-full'>
          {lastRowChildren.map((child, index) => (
            // biome-ignore lint/suspicious/noArrayIndexKey: items are always ordered here
            <div key={index} className='flex items-center flex-1'>
              {child}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ObjectDisplay;
