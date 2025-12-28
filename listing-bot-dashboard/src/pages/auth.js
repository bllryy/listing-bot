import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Header from "../components/header";
import Footer from "../components/footer";

const Auth = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [authActions, setAuthActions] = useState([]);
  const [usersInfo, setUsersInfo] = useState({});
  const [loadingActions, setLoadingActions] = useState(false);
  const [filterType, setFilterType] = useState("all"); // all, captcha, manual
  const [showResolved, setShowResolved] = useState(false);
  const [verifyingUsers, setVerifyingUsers] = useState(new Set());

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    localStorage.setItem("darkMode", !isDarkMode);
  };

  // Dark mode effect
  useEffect(() => {
    const savedMode = localStorage.getItem("darkMode");
    if (savedMode !== null) {
      setIsDarkMode(savedMode === "true");
    }
  }, []);

  // Main effect to handle authentication and data fetching
  useEffect(() => {
    const initializeApp = async () => {
      const isAuth = await checkAuth();
      
      if (isAuth) {
        // Extract bot name from URL path - using /{bot_name}/auth pattern
        const pathParts = location.pathname.split('/').filter(part => part);
        const botName = pathParts[0];
        
        if (botName && botName !== 'dashboard') {
          await fetchAuthActions(botName);
        } else {
          setError("Bot name not specified. Please provide a bot name in the URL path.");
          setLoading(false);
        }
      } else {
        setLoading(false);
      }
    };

    initializeApp();
  }, [location.pathname]);

  const checkAuth = async () => {
    try {
      const response = await fetch('https://v2.noemt.dev/auth/me', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setIsAuthenticated(true);
        return true;
      } else {
        setIsAuthenticated(false);
        return false;
      }
    } catch (err) {
      console.error("Auth check failed:", err);
      setIsAuthenticated(false);
      return false;
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('https://v2.noemt.dev/auth/logout', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      setUser(null);
      setIsAuthenticated(false);
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  const handleLogin = () => {
    const currentUrl = encodeURIComponent(window.location.href);
    window.location.href = `https://v2.noemt.dev/auth/discord/login?redirect_url=${currentUrl}`;
  };

  const fetchAuthActions = async (botName) => {
    try {
      setLoadingActions(true);
      setError(null);
      
      const response = await fetch(`https://v2.noemt.dev/api/bot/${botName}/auth/actions`, {
        credentials: 'include'
      });
      
      if (response.status === 401) {
        setError("Authentication required. Please login with Discord.");
        setIsAuthenticated(false);
        setLoadingActions(false);
        return;
      }
      
      if (response.status === 403) {
        setError("Access denied. You are not the owner of this bot.");
        setLoadingActions(false);
        return;
      }
      
      if (!response.ok) {
        throw new Error(`Failed to fetch auth actions: ${response.status}`);
      }
      
      const data = await response.json();
      setAuthActions(data.data || []);
      
      // Fetch user info for all unique user IDs
      const userIds = [...new Set(data.data?.map(action => action.user_id) || [])];
      if (userIds.length > 0) {
        await fetchUsersInfo(botName, userIds);
      }
      
      setLoading(false);
      setLoadingActions(false);
    } catch (err) {
      console.error("Error fetching auth actions:", err);
      setError(err.message);
      setLoading(false);
      setLoadingActions(false);
    }
  };

  const fetchUsersInfo = async (botName, userIds) => {
    try {
      const response = await fetch(`https://v2.noemt.dev/api/bot/${botName}/users/info`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(userIds)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch users info: ${response.status}`);
      }
      
      const result = await response.json();
      if (result.success && result.data) {
        setUsersInfo(result.data);
      }
    } catch (err) {
      console.error("Error fetching users info:", err);
    }
  };

  const verifyUser = async (actionId) => {
    try {
      setVerifyingUsers(prev => new Set(prev).add(actionId));
      
      // Extract bot name from current path
      const pathParts = location.pathname.split('/').filter(part => part);
      const botName = pathParts[0];
      
      const response = await fetch(`https://v2.noemt.dev/api/bot/${botName}/verify/user`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ action_id: actionId })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to verify user: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        // Refresh auth actions to see updated state
        await fetchAuthActions(botName);
      } else {
        setError(result.error || "Failed to verify user");
      }
    } catch (err) {
      console.error("Error verifying user:", err);
      setError(err.message);
    } finally {
      setVerifyingUsers(prev => {
        const newSet = new Set(prev);
        newSet.delete(actionId);
        return newSet;
      });
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getActionTypeDisplay = (actionType) => {
    switch (actionType) {
      case "captcha":
        return { emoji: "🧩", label: "Troll Captcha (manual verify required)", color: "text-orange-400" };
      case "manual":
        return { emoji: "👤", label: "No troll captcha (manual verify still required)", color: "text-blue-400" };
      case "verify":
        return { emoji: "✅", label: "User Verified", color: "text-green-400" };
      case "ban":
        return { emoji: "🚫", label: "User Banned", color: "text-red-400" };
      default:
        return { emoji: "❓", label: actionType, color: "text-gray-400" };
    }
  };

  // Filter actions based on criteria
  const filteredActions = authActions.filter(action => {
    // Hide resolved actions unless showResolved is true
    if (action.resolved && !showResolved) return false;
    
    // Filter by action type
    if (filterType !== "all" && action.action_type !== filterType) return false;
    
    return true;
  });

  // Dynamic styles based on theme
  const themeStyles = {
    background: isDarkMode ? "#070707" : "#f0f2f5",
    cardBg: isDarkMode ? "#101010" : "#ffffff",
    cardHover: isDarkMode ? "#202020" : "#f5f5f5",
    settingsBg: isDarkMode ? "#1a1a1a" : "#e9ecef",
    primaryText: isDarkMode ? "text-white" : "text-gray-800",
    secondaryText: isDarkMode ? "text-[#aaa]" : "text-gray-600",
  };

  // Display loading state
  if (loading) {
    return (
      <div
        className={`flex flex-col min-h-screen items-center justify-center ${
          isDarkMode ? "bg-[#070707] text-white" : "bg-[#f0f2f5] text-gray-800"
        }`}
      >
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // Display authentication required state
  if (!isAuthenticated) {
    return (
      <div
        className={`flex flex-col min-h-screen items-center justify-center ${
          isDarkMode ? "bg-[#070707] text-white" : "bg-[#f0f2f5] text-gray-800"
        }`}
      >
        <div className="text-center">
          <div className="mb-6">
            <span className="text-6xl mb-4 block">🔐</span>
            <h1 className="text-3xl font-bold mb-2">Authentication Required</h1>
            <p className={`${isDarkMode ? "text-gray-400" : "text-gray-600"} mb-6`}>
              Please login with Discord to access the auth management
            </p>
          </div>
          <button
            onClick={handleLogin}
            className="bg-[#5865F2] hover:bg-[#4752C4] text-white px-6 py-3 rounded-lg flex items-center gap-2 mx-auto transition-colors"
          >
            <span>🎮</span>
            Login with Discord
          </button>
        </div>
      </div>
    );
  }

  // Display error state
  if (error) {
    return (
      <div
        className={`flex flex-col min-h-screen items-center justify-center ${
          isDarkMode ? "bg-[#070707] text-white" : "bg-[#f0f2f5] text-gray-800"
        }`}
      >
        <div className="bg-red-500 text-white p-4 rounded-lg mb-4 max-w-md text-center">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => {
              setError(null);
              const pathParts = location.pathname.split('/').filter(part => part);
              const botName = pathParts[0];
              if (botName) {
                fetchAuthActions(botName);
              }
            }}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg"
          >
            Try Again
          </button>
          <button
            onClick={handleLogout}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
          >
            Logout
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`flex flex-col min-h-screen ${
        isDarkMode ? "bg-[#070707]" : "bg-[#f0f2f5]"
      }`}
    >
      <Header 
        isDarkMode={isDarkMode} 
        toggleDarkMode={toggleDarkMode}
        user={user}
        onLogout={handleLogout}
      />
      <main className="flex-grow w-4/5 mx-auto">
        {/* Header Section */}
        <div className="flex flex-row items-center justify-between mb-6 mt-6">
          <div className="flex items-center">
            <span
              className={`${
                isDarkMode ? "bg-[#101010]" : "bg-white"
              } p-2 rounded-lg text-xl mr-3`}
            >
              🔐
            </span>
            <div>
              <p className={`text-2xl ${themeStyles.primaryText}`}>
                Authentication Management
              </p>
              <p className={themeStyles.secondaryText}>
                Review and approve user verification requests for {location.pathname.split('/').filter(part => part)[0] || 'your bot'}
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              const pathParts = location.pathname.split('/').filter(part => part);
              const botName = pathParts[0];
              navigate(`/${botName}`);
            }}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
          >
            <span>🏠</span>
            Back to Dashboard
          </button>
        </div>

        {/* Filters Section */}
        <div
          className={`${
            isDarkMode ? "bg-[#101010]" : "bg-white"
          } rounded-xl p-5 mb-6`}
        >
          <div className="flex items-center gap-2 mb-4">
            <span className="text-purple-400">🔍</span>
            <p className={`text-lg font-medium ${themeStyles.primaryText}`}>
              Filters & Actions
            </p>
          </div>
          
          <div className="flex flex-wrap items-center gap-4">
            {/* Action Type Filter */}
            <div className="flex items-center gap-2">
              <label className={`${themeStyles.secondaryText} text-sm`}>
                Action Type:
              </label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className={`px-3 py-1 text-sm rounded-lg border ${
                  isDarkMode 
                    ? "bg-[#2a2a2a] border-gray-600 text-white" 
                    : "bg-white border-gray-300 text-gray-800"
                } focus:outline-none focus:ring-2 focus:ring-purple-500`}
              >
                <option value="all">All Types</option>
                <option value="captcha">🧩 Troll Captcha</option>
                <option value="manual">👤 Manual Verify</option>
              </select>
            </div>

            {/* Show Resolved Toggle */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showResolved}
                onChange={(e) => setShowResolved(e.target.checked)}
                className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <span className={`${themeStyles.secondaryText} text-sm`}>
                Show resolved actions
              </span>
            </label>

            {/* Refresh Button */}
            <button
              onClick={() => {
                const pathParts = location.pathname.split('/').filter(part => part);
                const botName = pathParts[0];
                if (botName) {
                  fetchAuthActions(botName);
                }
              }}
              disabled={loadingActions}
              className="bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white px-3 py-1 rounded-lg text-sm transition-colors flex items-center gap-1"
            >
              {loadingActions ? (
                <div className="animate-spin rounded-full h-3 w-3 border-t border-b border-white"></div>
              ) : (
                <span>🔄</span>
              )}
              Refresh
            </button>
          </div>

          <div className="mt-3 text-sm">
            <span className={themeStyles.secondaryText}>
              Showing {filteredActions.length} of {authActions.length} actions
            </span>
          </div>
        </div>

        {/* Auth Actions List */}
        <div
          className={`${
            isDarkMode ? "bg-[#101010]" : "bg-white"
          } rounded-xl p-5 mb-6`}
        >
          <div className="flex items-center gap-2 mb-4">
            <span className="text-orange-400">📋</span>
            <p className={`text-lg font-medium ${themeStyles.primaryText}`}>
              Pending Verifications
            </p>
          </div>

          {loadingActions ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500 mr-3"></div>
              <span className={themeStyles.secondaryText}>Loading auth actions...</span>
            </div>
          ) : filteredActions.length === 0 ? (
            <div className="text-center py-8">
              <span className="text-4xl mb-2 block">✅</span>
              <p className={`${themeStyles.primaryText} text-lg font-medium mb-2`}>
                No pending verifications
              </p>
              <p className={themeStyles.secondaryText}>
                {showResolved 
                  ? "No authentication actions found with current filters."
                  : "All verification requests have been resolved. Toggle 'Show resolved actions' to see completed ones."
                }
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredActions.map((action) => {
                const userInfo = usersInfo[action.user_id] || { id: action.user_id };
                const hasError = userInfo.error;
                const actionTypeInfo = getActionTypeDisplay(action.action_type);
                const isVerifying = verifyingUsers.has(action.action_id);

                return (
                  <div
                    key={action.action_id}
                    className={`${
                      isDarkMode ? "bg-[#1a1a1a] hover:bg-[#2a2a2a]" : "bg-gray-50 hover:bg-gray-100"
                    } p-4 rounded-lg border-l-4 ${
                      action.resolved 
                        ? "border-green-400" 
                        : action.action_type === "captcha" 
                          ? "border-orange-400" 
                          : "border-blue-400"
                    } transition-colors`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4 flex-1">
                        {/* User Avatar */}
                        <div className="w-12 h-12 rounded-full overflow-hidden bg-purple-600 flex-shrink-0">
                          {!hasError && userInfo.avatar ? (
                            <img
                              src={userInfo.avatar}
                              alt="User Avatar"
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                e.target.onerror = null;
                                e.target.style.display = 'none';
                                e.target.nextSibling.style.display = 'flex';
                              }}
                            />
                          ) : null}
                          <div className="w-full h-full bg-purple-600 flex items-center justify-center text-white text-lg" style={{ display: (!hasError && userInfo.avatar) ? 'none' : 'flex' }}>
                            👤
                          </div>
                        </div>

                        {/* User Info */}
                        <div className="flex-1">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h3 className={`${themeStyles.primaryText} text-lg font-medium`}>
                                {hasError ? 'Unknown User' : (userInfo.display_name || userInfo.global_name || userInfo.username || 'Unknown User')}
                              </h3>
                              {!hasError && userInfo.username && (
                                <p className={`${themeStyles.secondaryText} text-sm`}>
                                  @{userInfo.username}
                                  {userInfo.discriminator && userInfo.discriminator !== "0" && `#${userInfo.discriminator}`}
                                </p>
                              )}
                              <p className={`${themeStyles.secondaryText} text-xs font-mono`}>
                                ID: {action.user_id}
                              </p>
                            </div>
                            <div className="text-right">
                              <div className={`flex items-center gap-2 ${actionTypeInfo.color} text-sm font-medium mb-1`}>
                                <span>{actionTypeInfo.emoji}</span>
                                <span>{actionTypeInfo.label}</span>
                              </div>
                              <p className={`${themeStyles.secondaryText} text-xs`}>
                                {formatDate(action.timestamp)}
                              </p>
                            </div>
                          </div>

                          {/* Status and Actions */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs ${
                                action.resolved 
                                  ? "bg-green-100 text-green-700" 
                                  : "bg-yellow-100 text-yellow-700"
                              }`}>
                                <span>{action.resolved ? "✅" : "⏳"}</span>
                                <span>{action.resolved ? "Resolved" : "Pending"}</span>
                              </div>
                              
                              {!hasError && userInfo.username && (
                                <a
                                  href={`https://sky.shiiyu.moe/stats/${userInfo.username}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-400 hover:text-blue-300 text-xs flex items-center gap-1 transition-colors"
                                >
                                  <span>📊</span>
                                  View Stats
                                </a>
                              )}
                            </div>

                            {!action.resolved && (
                              <button
                                onClick={() => verifyUser(action.action_id)}
                                disabled={isVerifying}
                                className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-lg text-sm transition-colors flex items-center gap-2"
                              >
                                {isVerifying ? (
                                  <>
                                    <div className="animate-spin rounded-full h-3 w-3 border-t border-b border-white"></div>
                                    Verifying...
                                  </>
                                ) : (
                                  <>
                                    <span>✅</span>
                                    Verify User
                                  </>
                                )}
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
      <Footer isDarkMode={isDarkMode} />
    </div>
  );
};

export default Auth;
