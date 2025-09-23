import { useRef, useState } from 'react';
import { Switch } from './Switch';
import { TermsModal } from './TermsModal';

export function Terms({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
  const switchRef = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);

  const handleSwitchClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (value) {
      // Allow un-acceptance without opening modal
      onChange(false);
      return;
    }
    setOpen(true);
  };

  const handleAccepted = () => {
    setOpen(false);
    onChange(true);
    setTimeout(() => switchRef.current?.focus(), 0);
  };

  return (
    <>
      <label className="flex items-center gap-2 cursor-pointer">
        <span>I have read and accept the Terms</span>
        <Switch
          ref={switchRef}
          checked={value}
          onClick={handleSwitchClick}
          onCheckedChange={() => {}}
          className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
        />
      </label>
      {open && <TermsModal onAccept={handleAccepted} onClose={() => setOpen(false)} />}
    </>
  );
}
