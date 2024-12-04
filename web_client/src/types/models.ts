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
