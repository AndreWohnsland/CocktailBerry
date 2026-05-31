export interface CocktailIngredient {
  id: number;
  name: string;
  alcohol: number;
  hand: boolean;
  amount: number;
  recipe_order: number;
  unit: string;
}

export interface Cocktail {
  id: number;
  name: string;
  alcohol: number;
  amount: number;
  price_per_100_ml: number;
  is_allowed: boolean;
  enabled: boolean;
  virgin_available: boolean;
  only_virgin: boolean;
  ingredients: CocktailIngredient[];
  image: string;
  default_image: string;
}

export interface Ingredient extends CocktailIngredient {
  bottle_volume: number;
  fill_level: number;
  pump_speed: number;
  cost: number;
  bottle?: number;
  disallow_pump_back: boolean;
}

export interface IngredientInput {
  id?: number;
  name: string;
  alcohol: number;
  bottle_volume: number;
  fill_level: number;
  cost: number;
  pump_speed: number;
  hand: boolean;
  unit: string;
  disallow_pump_back: boolean;
}

export interface CocktailIngredientInput {
  id: number;
  amount: number;
  recipe_order: number;
}

export interface CocktailInput {
  id?: number;
  name: string;
  enabled: boolean;
  virgin_available: boolean;
  price_per_100_ml: number;
  ingredients: CocktailIngredientInput[];
  image: string;
  default_image: string;
}

export interface Bottle {
  number: number;
  ingredient?: Ingredient;
}

export type PrepareResult =
  | 'VALIDATION_OK'
  | 'IN_PROGRESS'
  | 'FINISHED'
  | 'CANCELED'
  | 'NOT_ENOUGH_INGREDIENTS'
  | 'ADDON_ERROR'
  | 'WAITING_FOR_PAYMENT'
  | 'NO_WAITER_LOGGED_IN'
  | 'NO_GLASS_DETECTED'
  | 'UNDEFINED';

export interface UserAuth {
  uid: string | null;
  balance: number | null;
  can_get_alcohol: boolean;
  is_authenticated: boolean;
}

export interface CocktailStatus {
  progress: number;
  message?: string;
  status: PrepareResult;
  hand_adds?: HandAddAssistItem[];
}

export interface HandAddAssistItem {
  item_id: string;
  name: string;
  display_amount: number;
  display_unit: string;
  measurable: boolean;
  target_weight_grams?: number | null;
}

export interface ApiError {
  detail: string;
  status?: PrepareResult;
  bottle?: number;
}

export interface LogData {
  data: { [key: string]: string[] };
}

export interface EventEntry {
  timestamp: string;
  event_type: string;
  additional_info: string | null;
}

export interface EventData {
  data: {
    events: EventEntry[];
    event_keys: string[];
  };
}

export interface SumupReader {
  id: string;
  name: string;
}

export interface SumupReaderCreate {
  name: string;
  pairing_code: string;
}

// generic interface for the config data
export interface ConfigData {
  [key: string]: PossibleConfigValue;
}

// explicit interface for the config data returned to the frontend for UI setup
// this alters slightly from the "real" config, since it for example abstracts password into bool (is it set or not)
export interface DefinedConfigData {
  UI_DEVENVIRONMENT: boolean;
  UI_MASTERPASSWORD: boolean;
  UI_MAKER_PASSWORD: boolean;
  UI_LOCKED_TABS: [boolean, boolean, boolean, boolean];
  UI_LANGUAGE: string;
  UI_WIDTH: number;
  UI_HEIGHT: number;
  UI_PICTURE_SIZE: number;
  UI_ONLY_MAKER_TAB: boolean;
  UI_VIRTUAL_KEYBOARD?: boolean;
  PUMP_CONFIG: PumpConfig[];
  MAKER_PINS_INVERTED: boolean;
  I2C_CONFIG: I2CConfig[];
  MAKER_NAME: string;
  MAKER_NUMBER_BOTTLES: number;
  MAKER_PREPARE_VOLUME: number[];
  MAKER_SIMULTANEOUSLY_PUMPS: number;
  MAKER_CLEAN_TIME: number;
  MAKER_ALCOHOL_FACTOR: number;
  MAKER_PUMP_REVERSION_CONFIG: ReversionConfig;
  MAKER_SEARCH_UPDATES: boolean;
  MAKER_CHECK_BOTTLE: boolean;
  MAKER_THEME: string;
  MAKER_MAX_HAND_INGREDIENTS: number;
  MAKER_CHECK_INTERNET: boolean;
  MAKER_USE_RECIPE_VOLUME: boolean;
  MAKER_ADD_SINGLE_INGREDIENT: boolean;
  MAKER_RANDOM_COCKTAIL: boolean;
  MAKER_HANDADD_SCALE_ASSIST: boolean;
  LED_CONFIG: LedConfig[];
  RFID_CONFIG: RfidConfig;
  MICROSERVICE_ACTIVE: boolean;
  MICROSERVICE_BASE_URL: string;
  TEAMS_ACTIVE: boolean;
  TEAM_BUTTON_NAMES: string[];
  TEAM_API_URL: string;
  PAYMENT_TYPE: 'Disabled' | 'CocktailBerry' | 'SumUp';
  PAYMENT_PRICE_ROUNDING: number;
  PAYMENT_VIRGIN_MULTIPLIER: number;
  PAYMENT_SHOW_NOT_POSSIBLE: boolean;
  PAYMENT_LOCK_SCREEN_NO_USER: boolean;
  PAYMENT_SERVICE_URL: string;
  PAYMENT_SECRET_KEY: string;
  PAYMENT_SUMUP_API_KEY: string;
  PAYMENT_SUMUP_MERCHANT_CODE: string;
  PAYMENT_SUMUP_TERMINAL_ID: string;
  PAYMENT_TIMEOUT_S: number;
  PAYMENT_AUTO_LOGOUT_TIME_S: number;
  PAYMENT_LOGOUT_AFTER_PREPARATION: boolean;
  WAITER_MODE: boolean;
  WAITER_LOGOUT_AFTER_COCKTAIL: boolean;
  WAITER_AUTO_LOGOUT_S: number;
  CUSTOM_COLOR_PRIMARY: string;
  CUSTOM_COLOR_SECONDARY: string;
  CUSTOM_COLOR_NEUTRAL: string;
  CUSTOM_COLOR_BACKGROUND: string;
  CUSTOM_COLOR_DANGER: string;
  EXP_MAKER_UNIT: string;
  EXP_MAKER_FACTOR: number;
  EXP_DEMO_MODE: boolean;
  SCALE_CONFIG: ScaleConfig;
  CARRIAGE_CONFIG: CarriageConfig;
}

export interface ScaleConfig {
  scale_type: string;
  enabled: boolean;
  calibration_factor: number;
  zero_raw_offset: number;
}

export interface CarriageConfig {
  carriage_type: string;
  enabled: boolean;
  home_position: number;
  speed_pct_per_s: number;
  move_during_cleaning: boolean;
  wait_after_dispense: number;
}

interface BaseDCPumpConfig {
  pin: number;
  volume_flow: number;
  tube_volume: number;
  consumption_estimation: 'time' | 'weight';
  carriage_position: number;
}

export interface DCGPIOPumpConfig extends BaseDCPumpConfig {
  pump_type: 'DC over GPIO';
}

export interface DCI2CPumpConfig extends BaseDCPumpConfig {
  pump_type: 'DC over I2C';
  pin_type: string;
  board_number: number;
}

export type DCPumpConfig = DCGPIOPumpConfig | DCI2CPumpConfig;

export interface StepperPumpConfig {
  pump_type: 'Stepper';
  pin: number;
  dir_pin: number;
  driver_type: string;
  step_type: string;
  volume_flow: number;
  tube_volume: number;
  consumption_estimation: 'time' | 'weight';
  carriage_position: number;
}

export type PumpConfig = DCPumpConfig | StepperPumpConfig;

export interface CustomColors {
  primary: string;
  secondary: string;
  background: string;
  neutral: string;
  danger: string;
}

export interface BaseReversionConfig {
  reversion_type: 'Global over GPIO' | 'Global over I2C' | 'Dispenser Controlled';
  enabled: boolean;
}

interface BaseGlobalReversionConfig extends BaseReversionConfig {
  pin: number;
  inverted: boolean;
}

export interface GlobalGPIOReversionConfig extends BaseGlobalReversionConfig {
  reversion_type: 'Global over GPIO';
}

export interface GlobalI2CReversionConfig extends BaseGlobalReversionConfig {
  reversion_type: 'Global over I2C';
  pin_type: string;
  board_number: number;
}

export type GlobalReversionConfig = GlobalGPIOReversionConfig | GlobalI2CReversionConfig;

export interface DispenserControlledReversionConfig extends BaseReversionConfig {
  reversion_type: 'Dispenser Controlled';
}

export type ReversionConfig = GlobalReversionConfig | DispenserControlledReversionConfig;

export interface I2CConfig {
  device_type: string;
  enabled: boolean;
  address: string;
  inverted: boolean;
  board_number: number;
}

export interface BaseLedConfig {
  led_type: string;
  default_on: boolean;
  preparation_state: 'Effect' | 'On' | 'Off';
}

interface BaseNormalLedConfig extends BaseLedConfig {
  pin: number;
}

export interface NormalGPIOLedConfig extends BaseNormalLedConfig {
  led_type: 'Normal over GPIO';
}

export interface NormalI2CLedConfig extends BaseNormalLedConfig {
  led_type: 'Normal over I2C';
  pin_type: string;
  board_number: number;
}

export type NormalLedConfig = NormalGPIOLedConfig | NormalI2CLedConfig;

export interface WS281xLedConfig extends BaseLedConfig {
  led_type: 'WSLED';
  pin: number;
  brightness: number;
  count: number;
  number_rings: number;
}

export type LedConfig = NormalLedConfig | WS281xLedConfig;

export interface RfidConfig {
  rfid_type: string;
  enabled: boolean;
}

// generic interface for the config data with ui information
// The structure contains:
// - Main key (e.g., "PUMP_CONFIG"): the root config item with ui metadata (value, description, prefix, suffix, etc.)
// - Additional nested keys (e.g., "pin", "volume_flow"): UI metadata for nested dict/list item properties
// These nested properties are flattened at the same level as the root config item.
// Example structure for PUMP_CONFIG:
// {
//   "PUMP_CONFIG": {
//     "value": [...],
//     "description": "...",
//     "immutable": false,
//     "pin": { prefix: "GPIO " },
//     "volume_flow": { suffix: "ml/s" }
// }
export interface ConfigDataWithUiInfo {
  [key: string]: PossibleUiInformation & {
    [additionalKeyForNestedAttributes: string]: PossibleUiInformation | undefined;
  };
}

type PossibleUiInformation = {
  value: PossibleConfigValue;
  default: PossibleConfigValue;
  description: string;
  readable_name: string;
  prefix?: string;
  suffix?: string;
  immutable?: boolean;
  allowed?: string[];
  check_name?: string;
  discriminator?: string;
  variants?: { [variantName: string]: { [fieldKey: string]: PossibleUiInformation } };
};

export type PossibleConfigValueTypes = boolean | number | string | boolean[] | number[] | string[];
export type PossibleConfigValue =
  | PossibleConfigValueTypes
  | { [key: string]: PossibleConfigValueTypes }
  | PumpConfig
  | PumpConfig[]
  | I2CConfig
  | I2CConfig[]
  | LedConfig
  | LedConfig[]
  | RfidConfig
  | ReversionConfig
  | ScaleConfig
  | CarriageConfig;

export interface ConsumeData {
  data: {
    'AT RESET': SingleConsumeData;
    ALL: SingleConsumeData;
    [key: string]: SingleConsumeData;
  };
}

interface SingleConsumeData {
  recipes: { [key: string]: number };
  ingredients: { [key: string]: number };
  cost?: { [key: string]: number };
}

export interface WifiData {
  ssid: string;
  password: string;
}

export interface AddonData {
  name: string;
  description: string;
  url: string;
  disabled_since: string;
  is_installable: boolean;
  disabled: boolean;
  satisfy_min_version: boolean;
  minimal_version: string;
  version: string;
  local_version?: string;
  file_name: string;
  installed: boolean;
  official: boolean;
  can_update: boolean;
}

export interface StartupIssue {
  has_issue: boolean;
  ignored: boolean;
  message: string;
}

export interface IssueData {
  deprecated: StartupIssue;
  internet: StartupIssue;
  config: StartupIssue;
  payment: StartupIssue;
}

export interface ResourceInfo {
  session_id: number;
  start_time: string;
}

export interface ResourceStats {
  min_cpu: number;
  max_cpu: number;
  mean_cpu: number;
  min_ram: number;
  max_ram: number;
  mean_ram: number;
  samples: number;
  raw_cpu: number[];
  raw_ram: number[];
}

export interface PaymentUserData {
  nfc_id: string | null;
  balance: number | null;
  is_adult: boolean | null;
}

export type UserLookupResult = 'USER_FOUND' | 'USER_NOT_FOUND' | 'SERVICE_UNAVAILABLE' | 'USER_REMOVED';

export interface PaymentUserUpdate {
  user: PaymentUserData | null;
  cocktails: Cocktail[];
  changeReason: UserLookupResult;
}

export interface AboutInfo {
  python_version: string;
  platform: string;
  project_name: string;
  version: string;
}

export interface UpdateVersion {
  version: string;
  release_notes: string;
  is_major: boolean;
}

export interface UpdateAvailability {
  status: string;
  message: string;
  versions: UpdateVersion[];
}

export interface TabPermission {
  maker: boolean;
  ingredients: boolean;
  recipes: boolean;
  bottles: boolean;
  options: boolean;
}

export interface Role {
  id: number;
  name: string;
  permissions: TabPermission;
  tile_permissions: OptionTiles;
}

export interface RoleCreate {
  name: string;
  permissions: TabPermission;
  tile_permissions: OptionTiles;
}

export interface RoleUpdate {
  name?: string;
  permissions?: TabPermission;
  tile_permissions?: OptionTiles;
}

export interface Waiter {
  nfc_id: string;
  name: string;
  role_id: number;
  role: Role;
  permissions: TabPermission;
  tile_permissions: OptionTiles;
}

export interface WaiterCreate {
  nfc_id: string;
  name: string;
  role_id: number;
}

export interface WaiterUpdate {
  name?: string;
  role_id?: number;
}

export interface WaiterLogEntry {
  id: number;
  timestamp: string;
  waiter_name: string;
  recipe_name: string;
  volume: number;
  is_virgin: boolean;
}

export interface CurrentWaiterState {
  nfc_id: string | null;
  waiter: Waiter | null;
}

/**
 * Mirror of the backend `OptionTiles` Pydantic model. Each field corresponds
 * to one option-tile in the Options screen; `true` means the producer has
 * blacklisted that tile and the UI must hide it.
 */
export interface OptionTiles {
  cleaning: boolean;
  configuration: boolean;
  calibration: boolean;
  scale_calibration: boolean;
  backup: boolean;
  restore: boolean;
  data: boolean;
  logs: boolean;
  wifi: boolean;
  addons: boolean;
  internet_check: boolean;
  update_system: boolean;
  update_software: boolean;
  system_resource_usage: boolean;
  about: boolean;
  news: boolean;
  sumup: boolean;
  waiters: boolean;
  events: boolean;
  reboot: boolean;
  shutdown: boolean;
  rfid: boolean;
  adjust_time: boolean;
  issues: boolean;
  recipe_calculation: boolean;
}

export type OptionTileName = keyof OptionTiles;

export interface Blacklist {
  configs: string[];
  options: OptionTiles;
}
