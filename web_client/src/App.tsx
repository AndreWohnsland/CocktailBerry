import CocktailList from './components/cocktail/CocktailList.tsx';
import { Route, Routes, Navigate, BrowserRouter } from 'react-router-dom';
import Header from './components/Header.tsx';
import { useTheme } from './ThemeProvider.tsx';
import IngredientList from './components/ingredient/IngredientList.tsx';
import RecipeList from './components/recipe/RecipeList.tsx';
import BottleList from './components/bottle/BottleList.tsx';
import AvailableBottles from './components/bottle/AvailableBottles.tsx';
import AdjustBottles from './components/bottle/AdjustBottles.tsx';

function App() {
  const { theme } = useTheme();

  return (
    <div className={`${theme}`}>
      <BrowserRouter>
        <Header />
        <div className='app-container mt-12'>
          <Routes>
            <Route path='cocktails' element={<CocktailList />} />
            <Route path='ingredients' element={<IngredientList />} />
            <Route path='recipes' element={<RecipeList />} />
            <Route path='bottles' element={<BottleList />} />
            <Route path='bottles/available' element={<AvailableBottles />} />
            <Route path='bottles/adjust' element={<AdjustBottles />} />
            <Route path='/' element={<Navigate to='/cocktails' />} />
          </Routes>
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;
