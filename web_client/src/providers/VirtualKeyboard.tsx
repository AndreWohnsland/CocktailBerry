import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import Keyboard from 'react-simple-keyboard';
import 'react-simple-keyboard/build/css/index.css';
import './virtual-keyboard.css';

type LayoutName = 'default' | 'shift' | 'numeric';

const LAYOUTS: Record<LayoutName, string[]> = {
  default: [
    '1 2 3 4 5 6 7 8 9 0 {bksp}',
    'q w e r t y u i o p',
    'a s d f g h j k l',
    '{shift} z x c v b n m , . -',
    '{space} {close}',
  ],
  shift: [
    '! " § $ % & / ( ) = {bksp}',
    'Q W E R T Y U I O P',
    'A S D F G H J K L',
    '{shift} Z X C V B N M ; : _',
    '{space} {close}',
  ],
  numeric: ['1 2 3', '4 5 6', '7 8 9', ', 0 {bksp}', '{close}'],
};

const DISPLAY = {
  '{bksp}': '⌫',
  '{shift}': '⇧',
  '{space}': '␣',
  '{close}': '✕',
};

const isEditable = (el: Element | null): el is HTMLInputElement | HTMLTextAreaElement => {
  if (!el) return false;
  if (el instanceof HTMLTextAreaElement) return true;
  if (!(el instanceof HTMLInputElement)) return false;
  const skip = [
    'checkbox',
    'radio',
    'file',
    'range',
    'color',
    'date',
    'time',
    'datetime-local',
    'month',
    'week',
    'hidden',
    'submit',
    'reset',
    'button',
    'image',
  ];
  return !skip.includes(el.type);
};

const layoutFor = (el: HTMLInputElement | HTMLTextAreaElement): LayoutName => {
  if (el instanceof HTMLInputElement) {
    if (el.type === 'number' || el.inputMode === 'numeric' || el.inputMode === 'decimal') return 'numeric';
  }
  return 'default';
};

// Sets the value via the native setter so React's synthetic event system picks it up
// (controlled inputs would otherwise overwrite a plain assignment on the next render).
const setNativeValue = (el: HTMLInputElement | HTMLTextAreaElement, value: string) => {
  const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
  setter?.call(el, value);
  el.dispatchEvent(new Event('input', { bubbles: true }));
};

const deriveHint = (el: HTMLInputElement | HTMLTextAreaElement): string => {
  if (el.placeholder) return el.placeholder;
  const ariaLabel = el.getAttribute('aria-label');
  if (ariaLabel) return ariaLabel;
  const labelledBy = el.getAttribute('aria-labelledby');
  if (labelledBy) {
    const labelEl = document.getElementById(labelledBy);
    if (labelEl?.textContent) return labelEl.textContent.trim();
  }
  return '';
};

const VirtualKeyboard = () => {
  const [target, setTarget] = useState<HTMLInputElement | HTMLTextAreaElement | null>(null);
  const [layoutName, setLayoutName] = useState<LayoutName>('default');
  const [mirrorValue, setMirrorValue] = useState('');
  const [mirrorHint, setMirrorHint] = useState('');
  const keyboardRef = useRef<unknown>(null);
  const dismissedUntil = useRef<number>(0);
  const openedAt = useRef<number>(0);
  const targetRef = useRef<HTMLInputElement | HTMLTextAreaElement | null>(null);
  const mirrorValueElRef = useRef<HTMLSpanElement | null>(null);

  // Keep a ref in sync so document-level listeners see the latest target without re-registering.
  useEffect(() => {
    targetRef.current = target;
  }, [target]);

  // Mirror the current target's value live so the user can see what they're typing
  // even when the keyboard overlaps the input. Listens to the target's input events so
  // both virtual-keyboard and external value changes stay in sync.
  useEffect(() => {
    if (!target) {
      setMirrorValue('');
      setMirrorHint('');
      return;
    }
    setMirrorValue(target.value ?? '');
    setMirrorHint(deriveHint(target));
    // Defer one frame so controlled components have committed their normalized value
    // (e.g. number inputs stripping leading zeros) before we mirror it.
    const onInput = () => {
      requestAnimationFrame(() => setMirrorValue(target.value ?? ''));
    };
    target.addEventListener('input', onInput);
    return () => target.removeEventListener('input', onInput);
  }, [target]);

  // Keep the right edge (where the caret is) visible when the value overflows.
  // biome-ignore lint/correctness/useExhaustiveDependencies: mirrorValue is used as a re-run trigger, not read inside.
  useEffect(() => {
    const el = mirrorValueElRef.current;
    if (el) el.scrollLeft = el.scrollWidth;
  }, [mirrorValue]);

  const isPassword = target instanceof HTMLInputElement && target.type === 'password';
  const displayValue = isPassword ? '•'.repeat(mirrorValue.length) : mirrorValue;

  useEffect(() => {
    const onFocus = (e: FocusEvent) => {
      const el = e.target as Element | null;
      if (!isEditable(el)) return;
      if (Date.now() < dismissedUntil.current) return;
      setTarget(el);
      setLayoutName(layoutFor(el));
      openedAt.current = Date.now();
      requestAnimationFrame(() => el.scrollIntoView({ block: 'center' }));
    };
    const onFocusOut = (e: FocusEvent) => {
      if (Date.now() - openedAt.current < 300) return;
      const related = e.relatedTarget as Element | null;
      // No relatedTarget = transient blur (touch settle, focus-trap shuffle). Ignore.
      if (!related) return;
      // Focus moved into the keyboard itself — keep it open.
      if (related.closest('.virtual-keyboard-root')) return;
      // Focus moved to another editable element — onFocus will pick the new target up.
      if (isEditable(related)) return;
      // Focus moved to a real non-editable element — user is done typing.
      setTarget(null);
    };
    const onPointerDown = (e: PointerEvent) => {
      const t = targetRef.current;
      if (!t) return;
      if (Date.now() - openedAt.current < 300) return;
      const tgt = e.target as Element | null;
      if (!tgt) return;
      // Tap inside keyboard or on something that will (re)focus an input — leave it open.
      if (tgt.closest('.virtual-keyboard-root')) return;
      if (tgt.closest('input, textarea, label')) return;
      // User tapped a non-input area — close the keyboard regardless of where browser focus stays.
      setTarget(null);
      t.blur();
    };
    document.addEventListener('focusin', onFocus);
    document.addEventListener('focusout', onFocusOut);
    document.addEventListener('pointerdown', onPointerDown);
    return () => {
      document.removeEventListener('focusin', onFocus);
      document.removeEventListener('focusout', onFocusOut);
      document.removeEventListener('pointerdown', onPointerDown);
    };
  }, []);

  const onKeyPress = useCallback(
    (button: string) => {
      const t = targetRef.current;
      if (!t) return;
      if (button === '{shift}') {
        setLayoutName((current) => (current === 'shift' ? 'default' : 'shift'));
        // Refocus so any modal focus trap stays happy.
        t.focus({ preventScroll: true });
        return;
      }
      if (button === '{close}') {
        dismissedUntil.current = Date.now() + 500;
        setTarget(null);
        t.blur();
        return;
      }
      const current = t.value ?? '';
      let next = current;
      if (button === '{bksp}') next = current.slice(0, -1);
      else if (button === '{space}') next = `${current} `;
      else next = `${current}${button}`;
      setNativeValue(t, next);
      if (layoutName === 'shift') setLayoutName('default');
      // Belt-and-suspenders: restore focus in case the tap on the key transferred it.
      t.focus({ preventScroll: true });
    },
    [layoutName],
  );

  const containerStyle = useMemo<React.CSSProperties>(
    () => ({
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      zIndex: 9999,
      padding: '8px 2px',
      boxShadow: '0 -2px 12px rgba(0, 0, 0, 0.5)',
      display: target ? 'block' : 'none',
    }),
    [target],
  );

  // Render into document.body so the keyboard sits outside #root — sibling of any
  // react-modal portal, so modals' aria-hidden and focus-trap don't reach it.
  return createPortal(
    <div className='virtual-keyboard-root' style={containerStyle}>
      <div className='virtual-keyboard-mirror'>
        {mirrorHint && <span className='virtual-keyboard-mirror-hint'>{mirrorHint}</span>}
        <span className='virtual-keyboard-mirror-value' ref={mirrorValueElRef}>
          {displayValue}
          <span className='virtual-keyboard-mirror-caret' />
        </span>
      </div>
      <Keyboard
        keyboardRef={(r) => {
          keyboardRef.current = r;
        }}
        layoutName={layoutName}
        layout={LAYOUTS}
        display={DISPLAY}
        onKeyPress={onKeyPress}
        physicalKeyboardHighlight={false}
        preventMouseDownDefault
      />
    </div>,
    document.body,
  );
};

export default VirtualKeyboard;
