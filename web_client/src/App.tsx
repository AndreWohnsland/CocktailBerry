import { useEffect } from 'react';
import Modal from 'react-modal';
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import { useIssues } from './api/options.ts';
import AvailableBottles from './components/bottle/AvailableBottles.tsx';
import BottleList from './components/bottle/BottleList.tsx';
import CocktailList from './components/cocktail/CocktailList.tsx';
import GettingConfiguration from './components/common/GettingConfiguration';
import { MakerPasswordProtected, MasterPasswordProtected } from './components/common/ProtectedRoute.tsx';
import RestrictedModePrompt from './components/common/RestrictedModePrompt.tsx';
import Header from './components/Header.tsx';
import IssuePage from './components/IssuePage.tsx';
import IngredientList from './components/ingredient/IngredientList.tsx';
import AddonManager from './components/options/AddonManager.tsx';
import CalibrationWindow from './components/options/CalibrationWindow.tsx';
import ConfigWindow from './components/options/ConfigWindow.tsx';
import DataWindow from './components/options/DataWindow.tsx';
import EventWindow from './components/options/EventWindow.tsx';
import LogWindow from './components/options/LogWindow.tsx';
import NewsWindow from './components/options/NewsWindow.tsx';
import OptionWindow from './components/options/OptionWindow.tsx';
import SumupManager from './components/options/SumupManager.tsx';
import TimeManager from './components/options/TimeManager.tsx';
import WifiManager from './components/options/WifiManager.tsx';
import RecipeCalculator from './components/recipe/RecipeCalculator.tsx';
import RecipeList from './components/recipe/RecipeList.tsx';
import ResourceWindow from './components/resources/ResourceWindow.tsx';
import { Tabs } from './constants/tabs.ts';
import useAxiosInterceptors from './hooks/useAxiosInterceptors.ts';
import { useConfig } from './providers/ConfigProvider.tsx';
import { useRestrictedMode } from './providers/RestrictedModeProvider.tsx';
import { hastNotIgnoredStartupIssues } from './utils.tsx';

Modal.setAppElement('#root');

function App() {
  const { config } = useConfig();
  const { restrictedModeActive } = useRestrictedMode();
  useAxiosInterceptors();
  const navigate = useNavigate();
  const { data: issues } = useIssues();

  useEffect(() => {
    if (hastNotIgnoredStartupIssues(issues)) {
      navigate('/issues');
    }
  }, [issues, navigate]);

  return (
    <div className='min-h-screen flex w-full h-full'>
      <RestrictedModePrompt />
      <Header />
      <div
        className={`min-h-screen ${
          restrictedModeActive ? 'pt-2' : 'pt-12'
        } flex flex-col w-full justify-center items-center`}
      >
        <ToastContainer position='top-center' />
        {/* do not show routes when config is empty */}
        {Object.keys(config).length === 0 ? (
          <GettingConfiguration />
        ) : (
          <Routes>
            <Route
              path='cocktails'
              element={
                <MakerPasswordProtected tabNumber={Tabs.Maker}>
                  <CocktailList />
                </MakerPasswordProtected>
              }
            />
            <Route
              path='manage/ingredients'
              element={
                <MakerPasswordProtected tabNumber={Tabs.Ingredients}>
                  <IngredientList />
                </MakerPasswordProtected>
              }
            />
            <Route
              path='manage/recipes'
              element={
                <MakerPasswordProtected tabNumber={Tabs.Recipes}>
                  <RecipeList />
                </MakerPasswordProtected>
              }
            />
            <Route
              path='manage/recipes/calculation'
              element={
                <MakerPasswordProtected tabNumber={Tabs.Recipes}>
                  <RecipeCalculator />
                </MakerPasswordProtected>
              }
            />
            <Route
              path='manage/bottles'
              element={
                <MakerPasswordProtected tabNumber={Tabs.Bottles}>
                  <BottleList />
                </MakerPasswordProtected>
              }
            />
            <Route
              path='manage/bottles/available'
              element={
                <MakerPasswordProtected tabNumber={Tabs.Bottles}>
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
              path='options/events'
              element={
                <MasterPasswordProtected>
                  <EventWindow />
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
              path='options/news'
              element={
                <MasterPasswordProtected>
                  <NewsWindow />
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
            <Route
              path='options/resources'
              element={
                <MasterPasswordProtected>
                  <ResourceWindow />
                </MasterPasswordProtected>
              }
            />
            <Route
              path='options/sumup'
              element={
                <MasterPasswordProtected>
                  <SumupManager />
                </MasterPasswordProtected>
              }
            />
            <Route path='issues' element={<IssuePage />} />
            <Route path='/' element={<Navigate to='/cocktails' />} />
          </Routes>
        )}
      </div>
    </div>
  );
}

export default App;
