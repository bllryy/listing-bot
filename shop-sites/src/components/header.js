import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import GradientText from "../components/gradient";

const Header = ({ isDarkMode, toggleDarkMode, user, onLogout }) => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Extract bot name from current path
  const getBotName = () => {
    const pathParts = location.pathname.split('/').filter(part => part);
    return pathParts[0] || '';
  };

  const botName = getBotName();
  const isOnListings = location.pathname.includes('/listings');

  // Dynamic styles based on theme
  const themeStyles = {
    background: isDarkMode ? 'bg-[#101010]' : 'bg-white',
    text: isDarkMode ? 'text-white' : 'text-gray-800',
    border: isDarkMode ? '' : 'border border-gray-200',
    buttonBg: isDarkMode ? 'bg-[#1a1a1a]' : 'bg-gray-100',
    buttonHover: isDarkMode ? 'hover:bg-[#252525]' : 'hover:bg-gray-200',
    secondaryText: isDarkMode ? 'text-gray-400' : 'text-gray-600',
  };

  return (
    <div className="flex flex-col">
      <div className={`flex flex-col ${themeStyles.background} ${themeStyles.border} w-full rounded-b-xl mx-auto`}>
        <div className="flex flex-col sm:flex-row justify-between items-center px-3 sm:px-5 py-3">
          <h1 className="text-lg sm:text-xl mb-2 sm:mb-0">
            <GradientText
              text="noemt.dev"
              startColor="#ff0080"
              endColor="#7928CA"
            />
          </h1>

          {/* Navigation Buttons */}
          {botName && (
            <div className="flex flex-wrap items-center gap-1 sm:gap-2 mb-2 sm:mb-0">
              <button
                onClick={() => navigate(`/${botName}`)}
                className={`px-2 sm:px-4 py-2 rounded-lg transition-colors duration-200 text-xs sm:text-sm font-medium ${
                  !isOnListings
                    ? 'bg-indigo-600 text-white' 
                    : `${themeStyles.buttonBg} ${themeStyles.buttonHover} ${themeStyles.text}`
                }`}
              >
                <span className="sm:hidden">🏠</span>
                <span className="hidden sm:inline">🏠 Home</span>
              </button>
              <button
                onClick={() => navigate(`/${botName}/listings`)}
                className={`px-2 sm:px-4 py-2 rounded-lg transition-colors duration-200 text-xs sm:text-sm font-medium ${
                  isOnListings 
                    ? 'bg-purple-600 text-white' 
                    : `${themeStyles.buttonBg} ${themeStyles.buttonHover} ${themeStyles.text}`
                }`}
              >
                <span className="sm:hidden">📋</span>
                <span className="hidden sm:inline">📋 Listings</span>
              </button>
            </div>
          )}
          
          <div className="flex items-center gap-2 sm:gap-3">
            <button 
              onClick={toggleDarkMode}
              className={`${themeStyles.buttonBg} ${themeStyles.buttonHover} ${themeStyles.text} p-2 rounded-lg transition-colors duration-200 flex items-center`}
              aria-label="Toggle dark mode"
            >
              {isDarkMode ? (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 sm:h-5 sm:w-5 sm:mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  <span className="hidden lg:inline">Light Mode</span>
                </>
              ) : (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 sm:h-5 sm:w-5 sm:mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                  <span className="hidden lg:inline">Dark Mode</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Header;