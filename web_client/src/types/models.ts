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
}

export interface Ingredient extends CocktailIngredient {
  bottle_volume: number;
  fill_level: number;
  pump_speed: number;
  cost: number;
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
}

export interface LogData {
  data: { [key: string]: string[] };
}

export interface ConfigData {
  [key: string]: PossibleConfigValue;
}

export interface ConfigDataWithUiInfo {
  [key: string]: PossibleUiInformation & {
    [additionalKey: string]: PossibleUiInformation | undefined;
  };
}

type PossibleUiInformation = {
  value: PossibleConfigValue;
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
