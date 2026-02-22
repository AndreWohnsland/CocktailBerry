import { FaGlassMartiniAlt, FaWineGlassAlt } from 'react-icons/fa';
import { ImMug } from 'react-icons/im';
import { PiPintGlassFill } from 'react-icons/pi';
import { TbGlassChampagne } from 'react-icons/tb';

export const FALLBACK_SERVING_SIZES = [200, 250, 300];

export const servingSizeIcons = [TbGlassChampagne, FaWineGlassAlt, FaGlassMartiniAlt, PiPintGlassFill, ImMug];

/** Pick a centered icon from `servingSizeIcons` for the given button index. */
export const getServingSizeIconIndex = (idx: number, servingSizesCount: number): number => {
  const totalIcons = servingSizeIcons.length;
  const needed = Math.min(servingSizesCount, totalIcons);
  const center = Math.floor(totalIcons / 2);

  // Choose a centered contiguous window; for even sizes bias to the right.
  let start = needed % 2 === 1 ? center - Math.floor(needed / 2) : center - needed / 2 + 1;

  if (start < 0) start = 0;
  if (start + needed > totalIcons) start = totalIcons - needed;

  // If more buttons than icons, clamp to last icon.
  if (idx >= needed) return totalIcons - 1;

  return start + idx;
};
