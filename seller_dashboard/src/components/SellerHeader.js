import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import GradientText from "../components/gradient";

const SellerHeader = ({ isDarkMode, toggleDarkMode, user, onLogout }) => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const isOnListings = location.pathname.includes('/listings');
  const isOnConfiguration = location.pathname.includes('/configuration');
  const isOnAuth = location.pathname.includes('/auth');
  const isOnDashboard = location.pathname === '/';

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
              text="🚀 Seller Dashboard"
              startColor="#ff0080"
              endColor="#7928CA"
            />
          </h1>

          {/* Navigation Buttons */}
          <div className="flex flex-wrap items-center gap-1 sm:gap-2 mb-2 sm:mb-0">
            <button
              onClick={() => navigate('/')}
              className={`px-2 sm:px-4 py-2 rounded-lg transition-colors duration-200 text-xs sm:text-sm font-medium ${
                isOnDashboard
                  ? 'bg-indigo-600 text-white' 
                  : `${themeStyles.buttonBg} ${themeStyles.buttonHover} ${themeStyles.text}`
              }`}
            >
              🏠 Dashboard
            </button>
            
            <button
              onClick={() => navigate('/listings')}
              className={`px-2 sm:px-4 py-2 rounded-lg transition-colors duration-200 text-xs sm:text-sm font-medium ${
                isOnListings
                  ? 'bg-indigo-600 text-white' 
                  : `${themeStyles.buttonBg} ${themeStyles.buttonHover} ${themeStyles.text}`
              }`}
            >
              📋 My Listings
            </button>
            
            <button
              onClick={() => navigate('/configuration')}
              className={`px-2 sm:px-4 py-2 rounded-lg transition-colors duration-200 text-xs sm:text-sm font-medium ${
                isOnConfiguration
                  ? 'bg-indigo-600 text-white' 
                  : `${themeStyles.buttonBg} ${themeStyles.buttonHover} ${themeStyles.text}`
              }`}
            >
              ⚙️ Configuration
            </button>
          </div>

          {/* User section */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Dark mode toggle */}
            <button
              onClick={toggleDarkMode}
              className={`p-2 rounded-lg transition-colors duration-200 ${themeStyles.buttonBg} ${themeStyles.buttonHover}`}
              title={isDarkMode ? "Switch to light mode" : "Switch to dark mode"}
            >
              {isDarkMode ? (
                <svg className="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                </svg>
              )}
            </button>

            {user ? (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <img
                      src={user.avatar}
                      alt={user.username || user.display_name || user.global_name || 'User'}
                      className="w-6 h-6 sm:w-8 sm:h-8 rounded-full border-2 border-indigo-500"
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'flex';
                      }}
                    />
                    <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs sm:text-sm border-2 border-indigo-500" style={{ display: 'none' }}>
                      👤
                    </div>
                    <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></div>
                  </div>
                  <span className={`text-xs sm:text-sm font-medium ${themeStyles.text} hidden sm:inline`}>
                    👋 {user.username || user.display_name || user.global_name || 'User'}
                  </span>
                </div>
                <button
                  onClick={onLogout}
                  className={`px-2 sm:px-3 py-1 sm:py-2 rounded-lg transition-colors duration-200 text-xs sm:text-sm font-medium ${themeStyles.buttonBg} ${themeStyles.buttonHover} ${themeStyles.text}`}
                >
                  🚪 Logout
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <div className={`w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-gray-300 animate-pulse`}></div>
                <div className={`w-16 h-4 bg-gray-300 rounded animate-pulse hidden sm:block`}></div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SellerHeader;
