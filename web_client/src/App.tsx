import { Navigate, Route, Routes } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import AvailableBottles from './components/bottle/AvailableBottles.tsx';
import BottleList from './components/bottle/BottleList.tsx';
import CocktailList from './components/cocktail/CocktailList.tsx';
import GettingConfiguration from './components/common/GettingConfiguration.tsx';
import { MakerPasswordProtected, MasterPasswordProtected } from './components/common/ProtectedRoute.tsx';
import Header from './components/Header.tsx';
import IngredientList from './components/ingredient/IngredientList.tsx';
import AddonManager from './components/options/AddonManager.tsx';
import CalibrationWindow from './components/options/CalibrationWindow.tsx';
import ConfigWindow from './components/options/ConfigWindow.tsx';
import DataWindow from './components/options/DataWindow.tsx';
import LogWindow from './components/options/LogWindow.tsx';
import OptionWindow from './components/options/OptionWindow.tsx';
import WifiManager from './components/options/WifiManager.tsx';
import RecipeList from './components/recipe/RecipeList.tsx';
import { useConfig } from './ConfigProvider.tsx';
import useAxiosInterceptors from './hooks/useAxiosInterceptors.ts';

function App() {
  const { config } = useConfig();
  useAxiosInterceptors();

  return (
    <div className='min-h-screen'>
      <Header />
      <div className='app-container pt-12'>
        <ToastContainer position='top-center' />
        {/* do not show routes when config is empty */}
        {Object.keys(config).length === 0 ? (
          <GettingConfiguration />
        ) : (
          <Routes>
            <Route path='cocktails' element={<CocktailList />} />
            <Route
              path='manage/ingredients'
              element={
                <MakerPasswordProtected tabNumber={0}>
                  <IngredientList />
                </MakerPasswordProtected>
              }
            />
            <Route
              path='manage/recipes'
              element={
                <MakerPasswordProtected tabNumber={1}>
                  <RecipeList />
                </MakerPasswordProtected>
              }
            />
            <Route
              path='manage/bottles'
              element={
                <MakerPasswordProtected tabNumber={2}>
                  <BottleList />
                </MakerPasswordProtected>
              }
            />
            <Route
              path='manage/bottles/available'
              element={
                <MakerPasswordProtected tabNumber={2}>
                  <AvailableBottles />
                </MakerPasswordProtected>
              }
            />
            <Route
              path='options'
              element={
                <MasterPasswordProtected>
                  <OptionWindow />
                </MasterPasswordProtected>
              }
            />
            <Route
              path='options/configuration'
              element={
                <MasterPasswordProtected>
                  <ConfigWindow />
                </MasterPasswordProtected>
              }
            />
            <Route
              path='options/data'
              element={
                <MasterPasswordProtected>
                  <DataWindow />
                </MasterPasswordProtected>
              }
            />
            <Route
              path='options/logs'
              element={
                <MasterPasswordProtected>
                  <LogWindow />
                </MasterPasswordProtected>
              }
            />
            <Route
              path='options/wifi'
              element={
                <MasterPasswordProtected>
                  <WifiManager />
                </MasterPasswordProtected>
              }
            />
            <Route
              path='options/addons'
              element={
                <MasterPasswordProtected>
                  <AddonManager />
                </MasterPasswordProtected>
              }
            />
            <Route
              path='options/calibration'
              element={
                <MasterPasswordProtected>
                  <CalibrationWindow />
                </MasterPasswordProtected>
              }
            />
            <Route path='/' element={<Navigate to='/cocktails' />} />
          </Routes>
        )}
      </div>
    </div>
  );
}

export default App;
