import { useEffect } from 'react';
import Modal from 'react-modal';
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import { useIssues } from './api/options.ts';
import AvailableBottles from './components/bottle/AvailableBottles.tsx';
import BottleList from './components/bottle/BottleList.tsx';
import CocktailList from './components/cocktail/CocktailList.tsx';
import GettingConfiguration from './components/common/GettingConfiguration.tsx';
import { MakerPasswordProtected, MasterPasswordProtected } from './components/common/ProtectedRoute.tsx';
import Header from './components/Header.tsx';
import IngredientList from './components/ingredient/IngredientList.tsx';
import IssuePage from './components/IssuePage.tsx';
import AddonManager from './components/options/AddonManager.tsx';
import CalibrationWindow from './components/options/CalibrationWindow.tsx';
import ConfigWindow from './components/options/ConfigWindow.tsx';
import DataWindow from './components/options/DataWindow.tsx';
import LogWindow from './components/options/LogWindow.tsx';
import OptionWindow from './components/options/OptionWindow.tsx';
import TimeManager from './components/options/TimeManager.tsx';
import WifiManager from './components/options/WifiManager.tsx';
import RecipeList from './components/recipe/RecipeList.tsx';
import { useConfig } from './ConfigProvider.tsx';
import useAxiosInterceptors from './hooks/useAxiosInterceptors.ts';
import { hastNotIgnoredStartupIssues } from './utils.tsx';

Modal.setAppElement('#root');

function App() {
  const { config } = useConfig();
  useAxiosInterceptors();
  const navigate = useNavigate();
  const { data: issues, isSuccess } = useIssues();

  useEffect(() => {
    if (hastNotIgnoredStartupIssues(issues)) {
      navigate('/issues');
    }
  }, [isSuccess, issues, navigate]);

  return (
    <div className='min-h-screen flex w-full h-full'>
      <Header />
      <div className='min-h-screen pt-12 flex flex-col w-full justify-center items-center'>
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
            <Route
              path='options/time'
              element={
                <MasterPasswordProtected>
                  <TimeManager />
                </MasterPasswordProtected>
              }
            />
            <Route path='/issues' element={<IssuePage />} />
            <Route path='/' element={<Navigate to='/cocktails' />} />
          </Routes>
        )}
      </div>
    </div>
  );
}

export default App;
