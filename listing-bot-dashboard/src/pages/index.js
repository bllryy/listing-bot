import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Header from "../components/header";
import GradientText from "../components/gradient";
import Footer from "../components/footer";

const Index = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [botData, setBotData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authorizedUsers, setAuthorizedUsers] = useState(null);
  const [authorizedBots, setAuthorizedBots] = useState(null);
  const [usersInfo, setUsersInfo] = useState(null);
  const [botOwnersInfo, setBotOwnersInfo] = useState(null);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [userSearchQuery, setUserSearchQuery] = useState("");
  const [selectedUser, setSelectedUser] = useState(null);
  const [showUserPopup, setShowUserPopup] = useState(false);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    localStorage.setItem("darkMode", !isDarkMode);
  };

  useEffect(() => {
    const initializeApp = async () => {
      // Check if user is authenticated
      const isAuth = await checkAuth();
      
      if (isAuth) {
        // Extract bot name from URL path - now using /{bot_name} pattern
        const pathParts = location.pathname.split('/').filter(part => part); // Remove empty parts
        
        // Bot name should be the first path segment after the domain
        // e.g., example.com/my-bot-name -> pathParts[0] = 'my-bot-name'
        const botName = pathParts[0];
        
        if (botName && botName !== 'dashboard') {
          await fetchBotData(botName);
        } else {
          setError("Bot name not specified. Please provide a bot name in the URL path (e.g., /your-bot-name).");
          setLoading(false);
        }
      } else {
        setLoading(false);
      }
    };

    initializeApp();
  }, [location.pathname]);

  // Dark mode effect
  useEffect(() => {
    const savedMode = localStorage.getItem("darkMode");
    if (savedMode !== null) {
      setIsDarkMode(savedMode === "true");
    }
  }, []);


  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

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

// Update the handleLogout function
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
    setBotData(null);
  } catch (err) {
    console.error("Logout failed:", err);
  }
};

  // Login with Discord
  const handleLogin = () => {
    const currentUrl = encodeURIComponent(window.location.href);
    window.location.href = `https://v2.noemt.dev/auth/discord/login?redirect_url=${currentUrl}`;
  };


  // Fetch bot data for authenticated user
  const fetchBotData = async (botName) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`https://v2.noemt.dev/dash/${botName}`, {
        credentials: 'include'
      });
      
      if (response.status === 401) {
        setError("Authentication required. Please login with Discord.");
        setIsAuthenticated(false);
        setLoading(false);
        return;
      }
      
      if (response.status === 403) {
        setError("Access denied. You are not the owner of this bot.");
        setLoading(false);
        return;
      }
      
      if (!response.ok) {
        throw new Error(`Failed to fetch bot data: ${response.status}`);
      }
      
      const data = await response.json();
      setBotData(data);
      
      // Also load authorized data when bot data is loaded
      await loadAuthorizedData(botName);
      
      setLoading(false);
    } catch (err) {
      console.error("Error fetching bot data:", err);
      setError(err.message);
      setLoading(false);
    }
  };

  // Fetch authorized bots for the user
  const fetchAuthorizedBots = async (botName) => {
    try {
      const response = await fetch(`https://v2.noemt.dev/api/bot/${botName}/auth/bots`, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch authorized bots: ${response.status}`);
      }
      
      const result = await response.json();
      // Extract client_ids from the API response
      return result.success ? result.data.map(bot => bot.client_id) : [];
    } catch (err) {
      console.error("Error fetching authorized bots:", err);
      return [];
    }
  };

  // Fetch authorized users for the bot
  const fetchAuthorizedUsers = async (botName) => {
    try {
      const response = await fetch(`https://v2.noemt.dev/api/bot/${botName}/auth/users`, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch authorized users: ${response.status}`);
      }
      
      const result = await response.json();
      // Return the data array directly
      return result.success ? result.data : [];
    } catch (err) {
      console.error("Error fetching authorized users:", err);
      return [];
    }
  };

  // Fetch detailed user information
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
        // Convert object format to array format for easier processing
        // Don't filter out users with errors - keep them to show "Unknown User"
        return Object.entries(result.data).map(([userId, userInfo]) => ({
          id: String(userId), // Ensure ID is always a string
          ...userInfo
        }));
      }
      return [];
    } catch (err) {
      console.error("Error fetching users info:", err);
      return [];
    }
  };

  // Get bot statistics (wrapper function)
  const fetchBotStats = async (botName) => {
    try {
      const response = await fetch(`https://v2.noemt.dev/stats/${botName}`, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch bot stats: ${response.status}`);
      }
      
      return await response.json();
    } catch (err) {
      console.error("Error fetching bot stats:", err);
      return null;
    }
  };

  // Load authorized users and bots data
  const loadAuthorizedData = async (botName) => {
    try {
      setLoadingUsers(true);
      
      // Fetch authorized bots and users
      const [botsData, usersData] = await Promise.all([
        fetchAuthorizedBots(botName),
        fetchAuthorizedUsers(botName)
      ]);
      
      setAuthorizedBots(botsData || []);
      setAuthorizedUsers(usersData || []);
      
      // Fetch bot owners info separately
      if (botsData && Array.isArray(botsData) && botsData.length > 0) {
        const botOwnerIds = botsData.map(clientId => String(clientId));
        const botOwnersData = await fetchUsersInfo(botName, botOwnerIds);
        setBotOwnersInfo(botOwnersData || []);
      } else {
        setBotOwnersInfo([]);
      }
      
      // Collect user IDs from authorized users for fetching detailed info
      const userIds = new Set();
      
      // Add user IDs from authorizedUsers (array of objects with user_id property)
      if (usersData && Array.isArray(usersData)) {
        usersData.forEach(user => {
          if (user.user_id) {
            userIds.add(String(user.user_id));
          }
          // Also add bot_id to get bot owner info for the user grouping
          if (user.bot_id) {
            userIds.add(String(user.bot_id));
          }
        });
      }
      
      // Fetch detailed info for authorized users
      if (userIds.size > 0) {
        const userIdsArray = Array.from(userIds);
        const detailedUsersInfo = await fetchUsersInfo(botName, userIdsArray);
        setUsersInfo(detailedUsersInfo || []);
      } else {
        setUsersInfo([]);
      }
      
      setLoadingUsers(false);
    } catch (err) {
      console.error("Error loading authorized data:", err);
      setLoadingUsers(false);
    }
  };

  // Calculate days between dates
  const calculateDaysRemaining = (targetDate) => {
    if (!targetDate) return 0;
    const target = new Date(targetDate);
    const today = new Date();
    const diffTime = target - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? diffDays : 0;
  };

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
              Please login with Discord to access the bot dashboard
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
              window.location.reload();
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
      <main className="flex-grow px-3 sm:px-4 lg:w-4/5 lg:mx-auto">
        {/* Instructions Section */}
        {!botData && (
          <div
            className={`${
              isDarkMode ? "bg-[#101010]" : "bg-white"
            } rounded-xl p-3 sm:p-5 mt-4 sm:mt-6 mb-4 border-l-4 border-indigo-500`}
          >
            <div className="flex items-start gap-3">
              <span className="text-xl sm:text-2xl">ℹ️</span>
              <div>
                <p className={`text-base sm:text-lg font-medium ${themeStyles.primaryText} mb-2`}>
                  How to Access Your Bot Dashboard
                </p>
                <p className={`${themeStyles.secondaryText} text-sm mb-3`}>
                  To view your bot's dashboard, navigate directly to your bot's URL:
                </p>
                <div className={`${isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"} p-3 rounded-lg font-mono text-xs sm:text-sm`}>
                  <p className={themeStyles.primaryText}>
                    {window.location.origin}/
                    <span className="text-indigo-400">your-bot-name</span>
                  </p>
                </div>
                <p className={`${themeStyles.secondaryText} text-xs mt-2`}>
                  You can only access bots that you own on Discord.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* User Profile Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 mt-4 sm:mt-6 gap-3">
          <div className="flex items-center">
            <span
              className={`${
                isDarkMode ? "bg-[#101010]" : "bg-white"
              } p-2 rounded-lg text-lg sm:text-xl mr-3`}
            >
              🤖
            </span>
            <div>
              <p className={`text-xl sm:text-2xl ${themeStyles.primaryText}`}>
                Bot Dashboard
              </p>
              <p className={`${themeStyles.secondaryText} text-sm sm:text-base`}>
                Welcome back, {user?.user_info?.global_name || user?.user_info?.username || 'User'}! 
                View and manage your bot information from this dashboard.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-green-500 text-sm">●</span>
            <span className={`${themeStyles.secondaryText} text-sm`}>
              Authenticated
            </span>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 sm:gap-4 mb-4 sm:mb-6">
          {/* Discord Profile Section */}
          <div
            className={`${
              isDarkMode ? "bg-[#101010]" : "bg-white"
            } rounded-xl p-3 sm:p-5 col-span-1`}
          >
            <div className="flex items-center gap-2 mb-3 sm:mb-4">
              <span className="text-indigo-400 text-lg sm:text-xl">🎮</span>
              <p className={`text-base sm:text-lg font-medium ${themeStyles.primaryText}`}>
                Your Discord Profile
              </p>
            </div>
            <p className={`${themeStyles.secondaryText} text-xs sm:text-sm mb-3 sm:mb-4`}>
              Authenticated Discord account information
            </p>

            <div className="flex flex-col items-center">
              {user?.user_info?.avatar ? (
                <img
                  alt="Discord Profile"
                  className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl transition-transform duration-300 hover:scale-110 mb-3"
                  src={`https://cdn.discordapp.com/avatars/${user.user_info.id}/${user.user_info.avatar}.png?size=128`}
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = "https://via.placeholder.com/80?text=User";
                  }}
                />
              ) : (
                <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-gray-700 flex items-center justify-center mb-3">
                  <span className="text-xl sm:text-2xl">👤</span>
                </div>
              )}
              <p className={`text-base sm:text-lg ${themeStyles.primaryText} font-medium text-center`}>
                {user.display_name || user.user_info.username || "You"}
              </p>
              <p className={`${themeStyles.secondaryText} text-xs sm:text-sm mb-2 text-center`}>
                Discord ID: {user?.discord_id || "N/A"}
              </p>
              {user?.name && user?.discriminator && (
                <p
                  className={`${
                    themeStyles.secondaryText
                  } text-xs mt-1 px-2 py-1 rounded ${
                    isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"
                  } text-center`}
                >
                  {user.user_info.username}#{user.user_info.discriminator}
                </p>
              )}
              {botData?.bot?.name && (
                <p
                  className={`${
                    themeStyles.secondaryText
                  } text-xs mt-1 px-2 py-1 rounded ${
                    isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"
                  } text-center`}
                >
                  Managing: {botData.bot.name}
                </p>
              )}
            </div>
          </div>

          {/* Stats Section */}
          <div className="lg:col-span-2">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
              {/* Listed Items Card */}
              <div
                className={`${
                  isDarkMode ? "bg-[#101010]" : "bg-white"
                } rounded-xl p-3 sm:p-5 flex flex-col justify-between`}
              >
                <div className="mb-2">
                  <span
                    className={`${
                      isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"
                    } p-1 sm:p-2 rounded-full text-teal-400 text-sm sm:text-base`}
                  >
                    🔐
                  </span>
                </div>
                <div>
                  <p className={`${themeStyles.secondaryText} text-xs sm:text-sm`}>
                    Listed Items
                  </p>
                  <p className="text-lg sm:text-xl font-semibold">
                    <GradientText
                      text={botData?.listings?.total || "0"}
                      startColor="#3CEFFF"
                      endColor="#46A3FF"
                    />
                  </p>
                </div>
              </div>

              {/* Tickets Card */}
              <div
                className={`${
                  isDarkMode ? "bg-[#101010]" : "bg-white"
                } rounded-xl p-3 sm:p-5 flex flex-col justify-between`}
              >
                <div className="mb-2">
                  <span
                    className={`${
                      isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"
                    } p-1 sm:p-2 rounded-full text-amber-400 text-sm sm:text-base`}
                  >
                    📜
                  </span>
                </div>
                <div>
                  <p className={`${themeStyles.secondaryText} text-xs sm:text-sm`}>
                    Opened Tickets
                  </p>
                  <p className="text-lg sm:text-xl font-semibold">
                    <GradientText
                      text={botData?.tickets?.total || "0"}
                      startColor="#FFD700"
                      endColor="#FFA500"
                    />
                  </p>
                </div>
              </div>

              {/* AI Credits Card */}
              <div
                className={`${
                  isDarkMode ? "bg-[#101010]" : "bg-white"
                } rounded-xl p-3 sm:p-5 flex flex-col justify-between`}
              >
                <div className="mb-2">
                  <span
                    className={`${
                      isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"
                    } p-1 sm:p-2 rounded-full text-purple-400 text-sm sm:text-base`}
                  >
                    🤖
                  </span>
                </div>
                <div>
                  <p className={`${themeStyles.secondaryText} text-xs sm:text-sm`}>
                    Remaining AI calls
                  </p>
                  <p className="text-lg sm:text-xl font-semibold">
                    <GradientText
                      text={botData?.ai_credits?.total_remaining || "0"}
                      startColor="#C04CFD"
                      endColor="#7B68EE"
                    />
                  </p>
                </div>
              </div>

              {/* Bot Version Card with Changelog Tooltip */}
              <div
                className={`${
                  isDarkMode ? "bg-[#101010]" : "bg-white"
                } rounded-xl p-3 sm:p-5 flex flex-col justify-between relative group`}
              >
                <div className="mb-2">
                  <span
                    className={`${
                      isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"
                    } p-1 sm:p-2 rounded-full text-cyan-400 text-sm sm:text-base`}
                  >
                    📊
                  </span>
                </div>
                <div>
                  <p className={`${themeStyles.secondaryText} text-xs sm:text-sm`}>
                    Bot Version
                  </p>
                  <p className="text-lg sm:text-xl font-semibold">
                    <GradientText
                      text={botData?.bot?.version || "1.0.0"}
                      startColor="#0ED2F7"
                      endColor="#08AEEA"
                    />
                  </p>
                </div>

                {/* Changelog Tooltip */}
                <div
                  className={`absolute left-0 bottom-full mb-2 w-64 p-3 rounded-lg shadow-lg z-10 
                    ${
                      isDarkMode
                        ? "bg-[#1a1a1a] text-white"
                        : "bg-white text-gray-800"
                    } 
                    transform transition-opacity duration-300 opacity-0 group-hover:opacity-100 pointer-events-none`}
                >
                  <h4 className="font-bold border-b mb-2 pb-1 border-gray-600">
                    Latest Changelog
                  </h4>
                  <p className="text-xs font-medium mb-1">
                    Version {botData?.bot?.version || "1.0.0"} (
                    {formatDate(botData?.timestamp?.split("T")[0])})
                  </p>
                  <ul className="text-xs list-disc pl-4 space-y-1">
                    <li>Added AI credit tracking</li>
                    <li>Improved listing management</li>
                    <li>Enhanced ticket system</li>
                    <li>Fixed various bugs</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Server Stats Section */}
            <div
              className={`${
                isDarkMode ? "bg-[#101010]" : "bg-white"
              } rounded-xl p-5 mt-4`}
            >
              <div className="flex items-center gap-2 mb-4">
                <span className="text-indigo-400">📈</span>
                <p className={`text-lg font-medium ${themeStyles.primaryText}`}>
                  Server Statistics
                </p>
              </div>
              <p className={`${themeStyles.secondaryText} text-sm mb-4`}>
                Current server metrics
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div
                  className={`${
                    isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"
                  } p-3 rounded-lg`}
                >
                  <p className={`${themeStyles.secondaryText} text-xs mb-1`}>
                    Total Members
                  </p>
                  <p className={`${themeStyles.primaryText} text-lg`}>
                    {botData?.server?.member_count || "0"}
                  </p>
                </div>
                <div
                  className={`${
                    isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"
                  } p-3 rounded-lg`}
                >
                  <p className={`${themeStyles.secondaryText} text-xs mb-1`}>
                    Human Users
                  </p>
                  <p className={`${themeStyles.primaryText} text-lg`}>
                    {botData?.server?.human_count || "0"}
                  </p>
                </div>
                <div
                  className={`${
                    isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"
                  } p-3 rounded-lg`}
                >
                  <p className={`${themeStyles.secondaryText} text-xs mb-1`}>
                    Bot Count
                  </p>
                  <p className={`${themeStyles.primaryText} text-lg`}>
                    {botData?.server?.bot_count || "0"}
                  </p>
                </div>
                <div
                  className={`${
                    isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"
                  } p-3 rounded-lg`}
                >
                  <p className={`${themeStyles.secondaryText} text-xs mb-1`}>
                    Online Users
                  </p>
                  <p className={`${themeStyles.primaryText} text-lg`}>
                    {botData?.server?.online_count || "0"}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Hosting Information */}
        <div
          className={`${
            isDarkMode ? "bg-[#101010]" : "bg-white"
          } rounded-xl p-5 mb-6`}
        >
          <div className="flex items-center gap-2 mb-4">
            <span className="text-yellow-400">🔑</span>
            <p className={`text-lg font-medium ${themeStyles.primaryText}`}>
              Hosting Information
            </p>
          </div>
          <p className={`${themeStyles.secondaryText} text-sm mb-6`}>
            Your bot hosting status and subscription details
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className={`${themeStyles.secondaryText} mb-2`}>Status</p>
              <div className="flex items-center gap-2 mb-4">
                <div
                  className={`bg-${
                    botData?.payment?.is_paid ? "green" : "red"
                  }-500 h-4 w-4 rounded-full`}
                ></div>
                <p className={themeStyles.primaryText}>
                  {botData?.payment?.is_paid ? "Active" : "Inactive"}
                </p>
              </div>

              <p className={`${themeStyles.secondaryText} mb-2`}>
                Remaining Time
              </p>
              <div className="flex items-center gap-2 mb-4">
                <div
                  className={`${
                    isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"
                  } rounded-lg py-2 px-4 w-full ${themeStyles.primaryText}`}
                >
                  <p className="text-lg font-semibold">
                    <GradientText
                      text={`${
                        botData?.payment?.days_remaining || "0"
                      } days`}
                      startColor="#3CEFFF"
                      endColor="#46A3FF"
                    />
                  </p>
                  <p className={`${themeStyles.secondaryText} text-xs mt-1`}>
                    Expires on {formatDate(botData?.payment?.expires_at)}
                  </p>
                </div>
              </div>
            </div>

            <div>
              <p className={`${themeStyles.secondaryText} mb-2`}>
                Extend Hosting
              </p>
              <div className="flex flex-col gap-3">
                <div
                  className={`${
                    isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"
                  } rounded-lg p-4`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <p className={`${themeStyles.primaryText} font-medium`}>
                      Hosting Extension
                    </p>
                    <p className="text-green-500 font-semibold">$1 ≙ 10 days</p>
                  </div>
                  <p className={`${themeStyles.secondaryText} text-xs mb-4`}>
                    Extend your bot hosting for however long you need. Purchases
                    will be automatically applied. Refunds are not applicable.
                  </p>
                  <a
                    href="https://noemt.dev/product/listing-bot-hosting-payment"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="bg-indigo-600 hover:bg-indigo-700 py-2 px-4 rounded-lg flex items-center justify-center gap-2 text-white w-full"
                  >
                    <span>🛒</span> Purchase Extension
                  </a>
                </div>

                <div
                  className={`${
                    isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"
                  } rounded-lg p-4 mt-2`}
                >
                  <p className={`${themeStyles.secondaryText} text-sm mb-2`}>
                    Recent Transaction
                  </p>
                  <div className="flex justify-between items-center">
                    <p className={`${themeStyles.primaryText} text-sm`}>
                      {botData?.payment?.last_payment_amount
                        ? `${botData.payment.last_payment_amount} Day Extension (${botData.payment.last_payment_amount/3} USD)`
                        : "No recent transactions"}
                    </p>
                    <p className={`${themeStyles.secondaryText} text-xs`}>
                      {botData?.payment?.last_payment
                        ? formatDate(botData.payment.last_payment)
                        : "N/A"}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Additional Management Section */}
        {botData && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
            {/* Quick Actions */}
            <div
              className={`${
                isDarkMode ? "bg-[#101010]" : "bg-white"
              } rounded-xl p-5`}
            >
              <div className="flex items-center gap-2 mb-4">
                <span className="text-green-400">⚡</span>
                <p className={`text-lg font-medium ${themeStyles.primaryText}`}>
                  Quick Actions
                </p>
              </div>
              <p className={`${themeStyles.secondaryText} text-sm mb-4`}>
                Useful management links and actions
              </p>

              <div className="space-y-3">
                <button
                  onClick={() => {
                    const pathParts = location.pathname.split('/').filter(part => part);
                    const botName = pathParts[0];
                    if (botName && botName !== 'dashboard') {
                      navigate(`/${botName}/listings`);
                    }
                  }}
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white p-3 rounded-lg flex items-center gap-2 transition-colors"
                >
                  <span>📋</span>
                  <span>View Listed Items</span>
                </button>
                <button
                  onClick={() => {
                    const pathParts = location.pathname.split('/').filter(part => part);
                    const botName = pathParts[0];
                    if (botName && botName !== 'dashboard') {
                      navigate(`/${botName}/auth`);
                    }
                  }}
                  className="w-full bg-orange-600 hover:bg-orange-700 text-white p-3 rounded-lg flex items-center gap-2 transition-colors"
                >
                  <span>🔐</span>
                  <span>Manage Authentication</span>
                </button>
                <button
                  onClick={() => {
                    const pathParts = location.pathname.split('/').filter(part => part);
                    const botName = pathParts[0];
                    if (botName && botName !== 'dashboard') {
                      navigate(`/${botName}/config`);
                    }
                  }}
                  className="w-full bg-green-600 hover:bg-green-700 text-white p-3 rounded-lg flex items-center gap-2 transition-colors"
                >
                  <span>⚙️</span>
                  <span>Bot Configuration</span>
                </button>
                <button
                  onClick={() => window.open('https://discord.com/developers/applications', '_blank')}
                  className="w-full bg-[#5865F2] hover:bg-[#4752C4] text-white p-3 rounded-lg flex items-center gap-2 transition-colors"
                >
                  <span>🔧</span>
                  <span>Discord Developer Portal</span>
                </button>
                <button
                  onClick={() => {
                    const pathParts = location.pathname.split('/').filter(part => part);
                    const botName = pathParts[0];
                    if (botName && botName !== 'dashboard') {
                      loadAuthorizedData(botName);
                    }
                  }}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-white p-3 rounded-lg flex items-center gap-2 transition-colors"
                >
                  <span>👥</span>
                  <span>Refresh Authorized Data</span>
                </button>
              </div>
            </div>

            {/* Bot Status */}
            <div
              className={`${
                isDarkMode ? "bg-[#101010]" : "bg-white"
              } rounded-xl p-5`}
            >
              <div className="flex items-center gap-2 mb-4">
                <span className="text-blue-400">📊</span>
                <p className={`text-lg font-medium ${themeStyles.primaryText}`}>
                  Bot Status
                </p>
              </div>
              <p className={`${themeStyles.secondaryText} text-sm mb-4`}>
                Current operational status
              </p>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className={themeStyles.secondaryText}>API Status:</span>
                  <div className="flex items-center gap-2">
                    <div className="bg-green-500 h-2 w-2 rounded-full"></div>
                    <span className={`${themeStyles.primaryText} text-sm`}>Online</span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className={themeStyles.secondaryText}>Last Updated:</span>
                  <span className={`${themeStyles.primaryText} text-sm`}>
                    {new Date().toLocaleTimeString()}
                  </span>
                </div>
                {botData?.payment && (
                  <div className="flex justify-between items-center">
                    <span className={themeStyles.secondaryText}>Payment Status:</span>
                    <span className={`text-sm ${botData.payment.is_paid ? 'text-green-500' : 'text-red-500'}`}>
                      {botData.payment.is_paid ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Authorized Users Section */}
        {botData && (
          <div
            className={`${
              isDarkMode ? "bg-[#101010]" : "bg-white"
            } rounded-xl p-5 mb-6`}
          >
            <div className="flex items-center gap-2 mb-4">
              <span className="text-purple-400">👥</span>
              <p className={`text-lg font-medium ${themeStyles.primaryText}`}>
                Authorized Users & Bots
              </p>
              {loadingUsers && (
                <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-purple-500 ml-2"></div>
              )}
            </div>
            <p className={`${themeStyles.secondaryText} text-sm mb-6`}>
              Users and bots authorized to access your bot's features
            </p>

            {/* Authorized Bots */}
            {authorizedBots && Array.isArray(authorizedBots) && (
              <div className="mb-6">
                <h3 className={`text-md font-medium ${themeStyles.primaryText} mb-3`}>
                  Active Auth Bots ({authorizedBots.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {authorizedBots.map((clientId, index) => {
                    // Find detailed info for this bot owner from the separate bot owners data
                    const userInfo = botOwnersInfo?.find(info => String(info.id) === String(clientId)) || { id: clientId };
                    
                    return (
                      <div
                        key={clientId || index}
                        className={`${
                          isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"
                        } p-3 rounded-lg flex items-center gap-3`}
                      >
                        <div className="w-10 h-10 rounded-full overflow-hidden bg-blue-600">
                          {userInfo.avatar && !userInfo.error ? (
                            <img
                              src={userInfo.avatar}
                              alt="Bot Owner Avatar"
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                e.target.onerror = null;
                                e.target.style.display = 'none';
                                e.target.nextSibling.style.display = 'flex';
                              }}
                            />
                          ) : null}
                          <div className="w-full h-full bg-blue-600 flex items-center justify-center text-white text-xs" style={{ display: userInfo.avatar && !userInfo.error ? 'none' : 'flex' }}>
                            🤖
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className={`${themeStyles.primaryText} text-sm font-medium truncate`}>
                            {userInfo.error ? 'Unknown User' : (userInfo.display_name || userInfo.name || 'Bot Owner')}
                          </p>
                          <p className={`${themeStyles.secondaryText} text-xs`}>
                            Client ID: {clientId}
                          </p>
                          {userInfo.name && userInfo.discriminator && !userInfo.error && (
                            <p className={`${themeStyles.secondaryText} text-xs`}>
                              @{userInfo.name}#{userInfo.discriminator}
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
                {authorizedBots.length === 0 && (
                  <p className={`${themeStyles.secondaryText} text-sm italic`}>
                    No authorized bot owners found
                  </p>
                )}
              </div>
            )}

            {/* Authorized Users */}
            {authorizedUsers && Array.isArray(authorizedUsers) && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className={`text-md font-medium ${themeStyles.primaryText}`}>
                    Authorized Users ({authorizedUsers.length})
                  </h3>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      placeholder="Search users..."
                      value={userSearchQuery}
                      onChange={(e) => setUserSearchQuery(e.target.value)}
                      className={`px-3 py-1 text-sm rounded-lg border ${
                        isDarkMode 
                          ? "bg-[#2a2a2a] border-gray-600 text-white placeholder-gray-400" 
                          : "bg-white border-gray-300 text-gray-800 placeholder-gray-500"
                      } focus:outline-none focus:ring-2 focus:ring-purple-500 w-48`}
                    />
                    {userSearchQuery && (
                      <button
                        onClick={() => setUserSearchQuery("")}
                        className="text-gray-400 hover:text-gray-600 text-sm"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                </div>
                
                {/* Group users by bot */}
                {(() => {
                  // Group users by bot_id
                  const usersByBot = authorizedUsers.reduce((acc, user) => {
                    const botId = user.bot_id;
                    if (!acc[botId]) {
                      acc[botId] = [];
                    }
                    acc[botId].push(user);
                    return acc;
                  }, {});

                  // Filter function for search
                  const filterUsers = (users) => {
                    if (!userSearchQuery.trim()) return users;
                    return users.filter(user => {
                      const userInfo = usersInfo?.find(info => String(info.id) === String(user.user_id)) || { id: user.user_id };
                      const searchTerm = userSearchQuery.toLowerCase();
                      return (
                        String(user.user_id).toLowerCase().includes(searchTerm) ||
                        (userInfo.display_name && userInfo.display_name.toLowerCase().includes(searchTerm)) ||
                        (userInfo.name && userInfo.name.toLowerCase().includes(searchTerm)) ||
                        (userInfo.username && userInfo.username.toLowerCase().includes(searchTerm))
                      );
                    });
                  };

                  return Object.keys(usersByBot).map(botId => {
                    const allUsersForBot = usersByBot[botId];
                    const filteredUsersForBot = filterUsers(allUsersForBot);
                    const botOwnerInfo = usersInfo?.find(info => String(info.id) === String(botId)) || { id: botId };
                    
                    // Only show this bot section if it has filtered users or no search query
                    if (filteredUsersForBot.length === 0 && userSearchQuery.trim()) {
                      return null;
                    }
                    
                    return (
                      <div key={botId} className="mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className={`text-sm font-medium ${themeStyles.primaryText} flex items-center gap-2`}>
                            <span className="text-blue-400">🤖</span>
                            Bot: {botOwnerInfo.error ? 'Unknown User' : (botOwnerInfo.display_name || botOwnerInfo.name || `ID: ${botId}`)}
                            <span className={`${themeStyles.secondaryText} text-xs`}>
                              ({filteredUsersForBot.length}{userSearchQuery.trim() ? ` of ${allUsersForBot.length}` : ''} users)
                            </span>
                          </h4>
                          <button
                            onClick={() => {
                              // Toggle users visibility for this bot
                              const element = document.getElementById(`bot-users-${botId}`);
                              if (element) {
                                element.style.display = element.style.display === 'none' ? 'grid' : 'none';
                              }
                            }}
                            className={`text-xs px-2 py-1 rounded ${
                              isDarkMode ? "bg-[#2a2a2a] hover:bg-[#3a3a3a]" : "bg-gray-200 hover:bg-gray-300"
                            } ${themeStyles.primaryText} transition-colors`}
                          >
                            Toggle
                          </button>
                        </div>
                        
                        <div id={`bot-users-${botId}`} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                          {filteredUsersForBot.map((user, index) => {
                            // Find detailed info for this user
                            const userInfo = usersInfo?.find(info => String(info.id) === String(user.user_id)) || { id: user.user_id };
                            const hasError = userInfo.error;
                            
                            return (
                              <div
                                key={user.user_id || index}
                                onClick={() => {
                                  setSelectedUser({ ...user, userInfo });
                                  setShowUserPopup(true);
                                }}
                                className={`${
                                  isDarkMode ? "bg-[#2a2a2a] hover:bg-[#3a3a3a]" : "bg-gray-50 hover:bg-gray-100"
                                } p-3 rounded-lg flex items-center gap-3 border-l-2 border-purple-400 cursor-pointer transition-colors`}
                              >
                                <div className="w-8 h-8 rounded-full overflow-hidden bg-purple-600">
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
                                  <div className="w-full h-full bg-purple-600 flex items-center justify-center text-white text-xs" style={{ display: (!hasError && userInfo.avatar) ? 'none' : 'flex' }}>
                                    👤
                                  </div>
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className={`${themeStyles.primaryText} text-sm font-medium truncate`}>
                                    {hasError ? 'Unknown User' : (userInfo.display_name || userInfo.name || 'Unknown User')}
                                  </p>
                                  <p className={`${themeStyles.secondaryText} text-xs`}>
                                    User ID: {user.user_id}
                                  </p>
                                  {!hasError && userInfo.name && userInfo.discriminator && (
                                    <p className={`${themeStyles.secondaryText} text-xs`}>
                                      @{userInfo.name}#{userInfo.discriminator}
                                    </p>
                                  )}
                                </div>
                                <div className="text-purple-400 text-xs">
                                  👆 Click for details
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  }).filter(Boolean);
                })()}
                
                {authorizedUsers.length === 0 && !loadingUsers && (
                  <p className={`${themeStyles.secondaryText} text-sm italic`}>
                    No authorized users found
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {/* User Details Popup */}
        {showUserPopup && selectedUser && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowUserPopup(false)}>
            <div 
              className={`${isDarkMode ? "bg-[#101010]" : "bg-white"} rounded-xl p-6 max-w-md w-full mx-4 border ${isDarkMode ? "border-gray-700" : "border-gray-200"}`}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className={`text-lg font-medium ${themeStyles.primaryText}`}>User Details</h3>
                <button
                  onClick={() => setShowUserPopup(false)}
                  className={`text-gray-400 hover:text-gray-600 text-xl`}
                >
                  ✕
                </button>
              </div>
              
              <div className="flex items-center gap-4 mb-4">
                <div className="w-16 h-16 rounded-full overflow-hidden bg-purple-600">
                  {!selectedUser.userInfo.error && selectedUser.userInfo.avatar ? (
                    <img
                      src={selectedUser.userInfo.avatar}
                      alt="User Avatar"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full bg-purple-600 flex items-center justify-center text-white text-xl">
                      👤
                    </div>
                  )}
                </div>
                <div>
                  <h4 className={`text-lg font-medium ${themeStyles.primaryText}`}>
                    {selectedUser.userInfo.error ? 'Unknown User' : (selectedUser.userInfo.display_name || selectedUser.userInfo.name || 'Unknown User')}
                  </h4>
                  {!selectedUser.userInfo.error && selectedUser.userInfo.username && (
                    <p className={`${themeStyles.secondaryText} text-sm`}>
                      @{selectedUser.userInfo.username}#{selectedUser.userInfo.discriminator}
                    </p>
                  )}
                </div>
              </div>

              <div className="space-y-3">
                <div className={`${isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"} p-3 rounded-lg`}>
                  <p className={`${themeStyles.secondaryText} text-xs mb-1`}>User ID</p>
                  <p className={`${themeStyles.primaryText} text-sm font-mono`}>
                    {selectedUser.user_id}
                  </p>
                </div>
                
                <div className={`${isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"} p-3 rounded-lg`}>
                  <p className={`${themeStyles.secondaryText} text-xs mb-1`}>Bot ID</p>
                  <p className={`${themeStyles.primaryText} text-sm font-mono`}>
                    {selectedUser.bot_id}
                  </p>
                </div>

                <div className={`${isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"} p-3 rounded-lg`}>
                  <p className={`${themeStyles.secondaryText} text-xs mb-1`}>IP Address</p>
                  <p className={`${themeStyles.primaryText} text-sm font-mono`}>
                    {selectedUser.ip_address || 'Not available'}
                  </p>
                </div>

                {selectedUser.userInfo && !selectedUser.userInfo.error && (
                  <>
                    {selectedUser.userInfo.global_name && (
                      <div className={`${isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"} p-3 rounded-lg`}>
                        <p className={`${themeStyles.secondaryText} text-xs mb-1`}>Global Name</p>
                        <p className={`${themeStyles.primaryText} text-sm`}>
                          {selectedUser.userInfo.global_name}
                        </p>
                      </div>
                    )}
                    
                    {selectedUser.userInfo.banner && (
                      <div className={`${isDarkMode ? "bg-[#1a1a1a]" : "bg-gray-100"} p-3 rounded-lg`}>
                        <p className={`${themeStyles.secondaryText} text-xs mb-1`}>Banner</p>
                        <img
                          src={selectedUser.userInfo.banner}
                          alt="User Banner"
                          className="w-full h-20 object-cover rounded"
                        />
                      </div>
                    )}
                  </>
                )}
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setShowUserPopup(false)}
                  className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
      <Footer isDarkMode={isDarkMode} />
    </div>
  );
};

export default Index;
