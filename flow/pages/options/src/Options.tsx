import '@src/Options.css';
import { t } from '@extension/i18n';
import { PROJECT_URL_OBJECT, useStorage, withErrorBoundary, withSuspense } from '@extension/shared';
import { extensionConfigStorage } from '@extension/storage';
import { cn, ErrorDisplay, LoadingSpinner, ToggleButton, Input, Label, Switch } from '@extension/ui';

const ProductStrategySection = ({
  title,
  enabled,
  timers,
  onChange,
}: {
  title: string;
  enabled: boolean;
  timers: { min: number; max: number };
  onChange: (updates: { enabled?: boolean; min?: number; max?: number }) => void;
}) => {
  return (
    <div className="space-y-4 rounded-lg bg-white/5 p-4">
      <div className="flex items-center justify-between">
        <Label className="text-lg font-medium">{title}</Label>
        <Switch checked={enabled} onCheckedChange={checked => onChange({ enabled: checked })} />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>Min Delay (s)</Label>
          <Input
            type="number"
            value={timers.min}
            onChange={e => onChange({ min: parseInt(e.target.value) })}
            min={0}
            disabled={!enabled}
          />
        </div>
        <div>
          <Label>Max Delay (s)</Label>
          <Input
            type="number"
            value={timers.max}
            onChange={e => onChange({ max: parseInt(e.target.value) })}
            min={0}
            disabled={!enabled}
          />
        </div>
      </div>
    </div>
  );
};

const Options = () => {
  const config = useStorage(extensionConfigStorage);
  const logo = 'logo_horizontal.svg';

  const updateProductStrategy = (type: 'animals' | 'cancer' | 'people', updates: Record<string, any>) => {
    const configUpdates: Record<string, any> = {};

    if ('enabled' in updates) {
      configUpdates[type] = updates.enabled;
    }
    if ('min' in updates) {
      configUpdates[`${type}TimerMin`] = updates.min;
    }
    if ('max' in updates) {
      configUpdates[`${type}TimerMax`] = updates.max;
    }

    extensionConfigStorage.updateConfig(configUpdates);
  };

  return (
    <div className={cn('App', 'bg-slate-50 text-gray-900')}>
      <div className="mx-auto max-w-2xl space-y-8 p-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Extension Settings</h1>
          <ToggleButton onClick={extensionConfigStorage.toggleEnabled} disabled={!config}>
            {config?.enabled ? 'Enabled' : 'Disabled'}
          </ToggleButton>
        </div>

        <div className="space-y-6">
          <h2 className="text-xl font-semibold">Product Strategies</h2>

          <ProductStrategySection
            title="Animal Insurance"
            enabled={config?.config.animals ?? false}
            timers={{
              min: config?.config.animalTimerMin ?? 10,
              max: config?.config.animalTimerMax ?? 30,
            }}
            onChange={updates => updateProductStrategy('animals', updates)}
          />

          <ProductStrategySection
            title="Cancer Insurance"
            enabled={config?.config.cancer ?? false}
            timers={{
              min: config?.config.cancerTimerMin ?? 15,
              max: config?.config.cancerTimerMax ?? 45,
            }}
            onChange={updates => updateProductStrategy('cancer', updates)}
          />

          <ProductStrategySection
            title="People Insurance"
            enabled={config?.config.people ?? false}
            timers={{
              min: config?.config.peopleTimerMin ?? 20,
              max: config?.config.peopleTimerMax ?? 60,
            }}
            onChange={updates => updateProductStrategy('people', updates)}
          />
        </div>
      </div>
    </div>
  );
};

export default withErrorBoundary(withSuspense(Options, <LoadingSpinner />), ErrorDisplay);
