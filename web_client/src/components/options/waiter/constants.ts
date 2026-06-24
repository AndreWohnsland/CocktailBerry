import type { OptionTileName, OptionTiles, TabPermission } from '../../../types/models';

export const PERMISSION_KEYS = ['maker', 'ingredients', 'recipes', 'bottles', 'options'] as const;

export const DEFAULT_PERMISSIONS: TabPermission = {
  maker: false,
  ingredients: false,
  recipes: false,
  bottles: false,
  options: false,
};

export const TILE_GROUPS: Record<string, readonly OptionTileName[]> = {
  system: ['reboot', 'shutdown', 'internet_check', 'update_system', 'update_software'],
  configuration: ['configuration', 'addons', 'sumup', 'wifi', 'adjust_time', 'rfid'],
  data: ['data', 'logs', 'system_resource_usage', 'events', 'news', 'about', 'issues'],
  hardware: ['cleaning', 'calibration', 'scale_calibration', 'initialize_bottles'],
  maintenance: ['backup', 'restore', 'waiters', 'recipe_calculation'],
};

export const ALL_TILE_KEYS: OptionTileName[] = Object.values(TILE_GROUPS).flat();

// Reuse the labels rendered in OptionWindow so a tile shown in the role editor matches
// the tile shown to the user 1:1.
export const TILE_TRANSLATION_KEYS: Record<OptionTileName, string> = {
  cleaning: 'options.cleaning',
  configuration: 'options.configuration',
  calibration: 'options.calibration',
  scale_calibration: 'options.scaleCalibration',
  initialize_bottles: 'options.initializeBottles',
  backup: 'options.backup',
  restore: 'options.restore',
  data: 'options.data',
  logs: 'options.logs',
  wifi: 'options.wifi',
  addons: 'options.addons',
  internet_check: 'options.internetCheck',
  update_system: 'options.updateSystem',
  update_software: 'options.updateCocktailBerry',
  system_resource_usage: 'options.systemResourceUsage',
  about: 'options.about',
  news: 'options.news',
  sumup: 'options.sumup',
  waiters: 'options.waiters',
  events: 'options.events',
  reboot: 'options.reboot',
  shutdown: 'options.shutdown',
  rfid: 'options.rfid',
  adjust_time: 'options.adjustTime',
  issues: 'options.issues',
  recipe_calculation: 'recipeCalculation.title',
};

export const buildEmptyTiles = (): OptionTiles =>
  ALL_TILE_KEYS.reduce((acc, key) => {
    acc[key] = false;
    return acc;
  }, {} as OptionTiles);
