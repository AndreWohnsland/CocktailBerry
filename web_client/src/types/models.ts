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
  enabled: boolean;
  virgin_available: boolean;
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
  | 'COCKTAIL_NOT_FOUND'
  | 'ADDON_ERROR'
  | 'UNDEFINED';

export interface CocktailStatus {
  progress: number;
  completed: boolean;
  message?: string;
  status: PrepareResult;
}

export interface ApiError {
  detail: string;
  status?: PrepareResult;
  bottle?: number;
}

export interface LogData {
  data: { [key: string]: string[] };
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
  UI_LOCKED_TABS: [boolean, boolean, boolean];
  UI_LANGUAGE: string;
  UI_WIDTH: number;
  UI_HEIGHT: number;
  UI_PICTURE_SIZE: number;
  PUMP_CONFIG: PumpConfig[];
  MAKER_NAME: string;
  MAKER_NUMBER_BOTTLES: number;
  MAKER_PREPARE_VOLUME: number[];
  MAKER_SIMULTANEOUSLY_PUMPS: number;
  MAKER_CLEAN_TIME: number;
  MAKER_ALCOHOL_FACTOR: number;
  MAKER_PUMP_REVERSION: boolean;
  MAKER_REVERSION_PIN: number;
  MAKER_SEARCH_UPDATES: boolean;
  MAKER_CHECK_BOTTLE: boolean;
  MAKER_PINS_INVERTED: boolean;
  MAKER_THEME: string;
  MAKER_MAX_HAND_INGREDIENTS: number;
  MAKER_CHECK_INTERNET: boolean;
  MAKER_USE_RECIPE_VOLUME: boolean;
  MAKER_ADD_SINGLE_INGREDIENT: boolean;
  LED_PINS: number[];
  LED_BRIGHTNESS: number;
  LED_COUNT: number;
  LED_NUMBER_RINGS: number;
  LED_DEFAULT_ON: boolean;
  LED_IS_WS: boolean;
  RFID_READER: string;
  MICROSERVICE_ACTIVE: boolean;
  MICROSERVICE_BASE_URL: string;
  TEAMS_ACTIVE: boolean;
  TEAM_BUTTON_NAMES: string[];
  TEAM_API_URL: string;
  CUSTOM_COLOR_PRIMARY: string;
  CUSTOM_COLOR_SECONDARY: string;
  CUSTOM_COLOR_NEUTRAL: string;
  CUSTOM_COLOR_BACKGROUND: string;
  CUSTOM_COLOR_DANGER: string;
  EXP_MAKER_UNIT: string;
  EXP_MAKER_FACTOR: number;
}

export interface CustomColors {
  primary: string;
  secondary: string;
  background: string;
  neutral: string;
  danger: string;
}

export interface PumpConfig {
  pin: number;
  volume_flow: number;
  tube_volume: number;
}

// generic interface for the config data with ui information
export interface ConfigDataWithUiInfo {
  [key: string]: PossibleUiInformation & {
    [additionalKey: string]: PossibleUiInformation | undefined;
  };
}

type PossibleUiInformation = {
  value: PossibleConfigValue;
  description: string;
  prefix?: string;
  suffix?: string;
  immutable?: boolean;
  allowed?: string[];
  check_name?: string;
};

export type PossibleConfigValueTypes = boolean | number | string | boolean[] | number[] | string[];
export type PossibleConfigValue = PossibleConfigValueTypes | { [key: string]: PossibleConfigValueTypes };

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
  file_name: string;
  installed: boolean;
  official: boolean;
}
