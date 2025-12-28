import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Header from "../components/header";
import Footer from "../components/footer";

const Config = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [config, setConfig] = useState({});
  const [channels, setChannels] = useState({ standalone_channels: [], categories: [] });
  const [roles, setRoles] = useState([]);
  const [configUpdates, setConfigUpdates] = useState({});
  const [saving, setSaving] = useState(false);
  const [draggedItem, setDraggedItem] = useState(null);

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
        const pathParts = location.pathname.split('/').filter(part => part);
        const botName = pathParts[0];
        
        if (botName && botName !== 'dashboard') {
          await Promise.all([
            fetchConfig(botName),
            fetchChannels(botName),
            fetchRoles(botName)
          ]);
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

  const fetchConfig = async (botName) => {
    try {
      const response = await fetch(`https://v2.noemt.dev/api/bot/${botName}/config`, {
        credentials: 'include'
      });
      
      if (response.status === 401) {
        setError("Authentication required. Please login with Discord.");
        setIsAuthenticated(false);
        return;
      }
      
      if (response.status === 403) {
        setError("Access denied. You are not the owner of this bot.");
        return;
      }
      
      if (!response.ok) {
        throw new Error(`Failed to fetch configuration: ${response.status}`);
      }
      
      const data = await response.json();
      if (data.success) {
        setConfig(data.configuration);
      } else {
        setError("Failed to load configuration data");
      }
    } catch (err) {
      console.error("Error fetching config:", err);
      setError(err.message);
    }
  };

  const fetchChannels = async (botName) => {
    try {
      const response = await fetch(`https://v2.noemt.dev/api/bot/${botName}/channels`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setChannels(data.data);
        }
      }
      setLoading(false);
    } catch (err) {
      console.error("Error fetching channels:", err);
      setLoading(false);
    }
  };

  const fetchRoles = async (botName) => {
    try {
      const response = await fetch(`https://v2.noemt.dev/api/bot/${botName}/roles`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setRoles(data.roles);
        }
      }
    } catch (err) {
      console.error("Error fetching roles:", err);
    }
  };

  const saveConfig = async () => {
    try {
      setSaving(true);
      setError(null);
      
      const pathParts = location.pathname.split('/').filter(part => part);
      const botName = pathParts[0];
      
      if (Object.keys(configUpdates).length === 0) {
        setSaving(false);
        return;
      }
      
      const response = await fetch(`https://v2.noemt.dev/api/bot/${botName}/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(configUpdates)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to save configuration: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        // Update local config with saved values
        const updatedConfig = { ...config };
        Object.keys(configUpdates).forEach(key => {
          if (result.results[key]) {
            updatedConfig[key] = {
              ...updatedConfig[key],
              value: result.results[key].value,
              is_set: true
            };
          }
        });
        setConfig(updatedConfig);
        setConfigUpdates({});
        
        // Show success notification
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg z-50 transition-opacity';
        notification.textContent = 'Configuration saved successfully!';
        document.body.appendChild(notification);
        
        setTimeout(() => {
          notification.style.opacity = '0';
          setTimeout(() => document.body.removeChild(notification), 300);
        }, 3000);
      } else {
        setError(result.errors ? result.errors.join(', ') : "Failed to save configuration");
      }
    } catch (err) {
      console.error("Error saving config:", err);
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleConfigUpdate = (key, value, type) => {
    // Ensure Discord IDs and numeric values are always strings
    let processedValue = value;
    if (['TextChannel', 'CategoryChannel', 'Role', 'int', 'float'].includes(type) && value !== null && value !== undefined) {
      processedValue = String(value);
    }
    
    setConfigUpdates(prev => ({
      ...prev,
      [key]: { value: processedValue, type }
    }));
  };

  const handleDragStart = (e, item, itemType) => {
    setDraggedItem({ ...item, itemType });
    e.dataTransfer.effectAllowed = 'copy';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
  };

  const handleDrop = (e, configKey, configType) => {
    e.preventDefault();
    
    if (!draggedItem) return;
    
    // Check if the dragged item type matches the config type
    const isValidDrop = (
      (configType === 'TextChannel' && draggedItem.itemType === 'channel' && draggedItem.type === 'text') ||
      (configType === 'CategoryChannel' && draggedItem.itemType === 'category') ||
      (configType === 'Role' && draggedItem.itemType === 'role')
    );
    
    if (isValidDrop) {
      handleConfigUpdate(configKey, String(draggedItem.id), configType);
    }
    
    setDraggedItem(null);
  };

  const getChannelIcon = (type) => {
    switch (type) {
      case 'text': return '#';
      case 'voice': return '🔊';
      case 'stage': return '🎭';
      case 'forum': return '💬';
      default: return '📄';
    }
  };

  const getConfigIcon = (type) => {
    switch (type) {
      case 'TextChannel': return '#';
      case 'CategoryChannel': return '📁';
      case 'Role': return '👥';
      case 'int': return '🔢';
      case 'float': return '🔢';
      case 'bool': return '☑️';
      case 'str': return '📝';
      default: return '⚙️';
    }
  };

  const getItemDisplayName = (id, type) => {
    if (!id) return null;
    
    // Ensure ID is a string for comparison
    const idStr = String(id);
    
    if (type === 'TextChannel') {
      // Search in standalone channels
      const standAloneChannel = channels.standalone_channels?.find(ch => String(ch.id) === idStr);
      if (standAloneChannel) return standAloneChannel.name;
      
      // Search in category channels
      for (const category of channels.categories || []) {
        const categoryChannel = category.channels?.find(ch => String(ch.id) === idStr);
        if (categoryChannel) return categoryChannel.name;
      }
    } else if (type === 'CategoryChannel') {
      const category = channels.categories?.find(cat => String(cat.id) === idStr);
      if (category) return category.name;
    } else if (type === 'Role') {
      const role = roles.find(r => String(r.id) === idStr);
      if (role) return role.name;
    }
    
    return null;
  };

  const getCurrentValue = (configKey) => {
    if (configUpdates[configKey]) {
      return configUpdates[configKey].value;
    }
    return config[configKey]?.value || '';
  };

  const isConfigModified = (configKey) => {
    return configKey in configUpdates;
  };

  const getDropZoneStyle = (configType, isDragOver) => {
    const baseStyle = `min-h-[40px] border-2 border-dashed rounded-lg p-2 transition-colors ${
      isDarkMode ? 'border-gray-600' : 'border-gray-300'
    }`;
    
    if (isDragOver && draggedItem) {
      const isValidTarget = (
        (configType === 'TextChannel' && draggedItem.itemType === 'channel' && draggedItem.type === 'text') ||
        (configType === 'CategoryChannel' && draggedItem.itemType === 'category') ||
        (configType === 'Role' && draggedItem.itemType === 'role')
      );
      
      if (isValidTarget) {
        return `${baseStyle} border-green-400 bg-green-400 bg-opacity-10`;
      } else {
        return `${baseStyle} border-red-400 bg-red-400 bg-opacity-10`;
      }
    }
    
    return baseStyle;
  };

  // Dynamic styles based on theme
  const themeStyles = {
    background: isDarkMode ? "#070707" : "#f0f2f5",
    cardBg: isDarkMode ? "#101010" : "#ffffff",
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
        <p>Loading configuration...</p>
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
              Please login with Discord to access the configuration
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
                Promise.all([fetchConfig(botName), fetchChannels(botName)]);
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
      
      <main className="flex-grow p-2 sm:p-4">
        <div className="max-w-7xl mx-auto">
          {/* Header Section */}
          <div className="flex flex-row items-center justify-between mb-6">
            <div className="flex items-center">
              <span
                className={`${
                  isDarkMode ? "bg-[#101010]" : "bg-white"
                } p-2 rounded-lg text-xl mr-3`}
              >
                ⚙️
              </span>
              <div>
                <p className={`text-2xl ${themeStyles.primaryText}`}>
                  Bot Configuration
                </p>
                <p className={themeStyles.secondaryText}>
                  Configure your bot settings and channel assignments
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  const pathParts = location.pathname.split('/').filter(part => part);
                  const botName = pathParts[0];
                  navigate(`/${botName}`);
                }}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
              >
                <span>🏠</span>
                Back to Dashboard
              </button>
              <button
                onClick={saveConfig}
                disabled={saving || Object.keys(configUpdates).length === 0}
                className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
              >
                {saving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-t border-b border-white"></div>
                    Saving...
                  </>
                ) : (
                  <>
                    <span>💾</span>
                    Save Changes {Object.keys(configUpdates).length > 0 && `(${Object.keys(configUpdates).length})`}
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Server Layout - Left Side */}
            <div className={`${isDarkMode ? "bg-[#101010]" : "bg-white"} rounded-xl p-5 lg:col-span-1`}>
              <div className="flex items-center gap-2 mb-4">
                <span className="text-blue-400">🏢</span>
                <p className={`text-lg font-medium ${themeStyles.primaryText}`}>
                  Server Layout
                </p>
              </div>
              <p className={`${themeStyles.secondaryText} text-sm mb-4`}>
                Drag channels, categories, and roles to configure your bot
              </p>

              <div className="space-y-3 max-h-[70vh] overflow-y-auto">
                {/* Standalone Channels */}
                {channels.standalone_channels.length > 0 && (
                  <div>
                    <p className={`${themeStyles.secondaryText} text-xs font-medium mb-2 uppercase tracking-wide`}>
                      Channels
                    </p>
                    {channels.standalone_channels.map(channel => (
                      <div
                        key={channel.id}
                        draggable
                        onDragStart={(e) => handleDragStart(e, channel, 'channel')}
                        className={`flex items-center gap-2 p-2 rounded cursor-move transition-colors ${
                          isDarkMode ? 'hover:bg-[#2a2a2a]' : 'hover:bg-gray-100'
                        }`}
                      >
                        <span className="text-gray-400">{getChannelIcon(channel.type)}</span>
                        <span className={`${themeStyles.primaryText} text-sm truncate`}>
                          {channel.name}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Categories */}
                {channels.categories.map(category => (
                  <div key={category.id}>
                    <div
                      draggable
                      onDragStart={(e) => handleDragStart(e, category, 'category')}
                      className={`flex items-center gap-2 p-2 rounded cursor-move transition-colors ${
                        isDarkMode ? 'hover:bg-[#2a2a2a]' : 'hover:bg-gray-100'
                      } mb-1`}
                    >
                      <span className="text-gray-400">📁</span>
                      <span className={`${themeStyles.primaryText} text-sm font-medium truncate`}>
                        {category.name}
                      </span>
                    </div>
                    {category.channels.map(channel => (
                      <div
                        key={channel.id}
                        draggable
                        onDragStart={(e) => handleDragStart(e, channel, 'channel')}
                        className={`flex items-center gap-2 p-1 pl-6 rounded cursor-move transition-colors ${
                          isDarkMode ? 'hover:bg-[#2a2a2a]' : 'hover:bg-gray-100'
                        }`}
                      >
                        <span className="text-gray-400 text-xs">{getChannelIcon(channel.type)}</span>
                        <span className={`${themeStyles.secondaryText} text-xs truncate`}>
                          {channel.name}
                        </span>
                      </div>
                    ))}
                  </div>
                ))}

                {/* Roles */}
                {roles.length > 0 && (
                  <div>
                    <p className={`${themeStyles.secondaryText} text-xs font-medium mb-2 uppercase tracking-wide`}>
                      Roles
                    </p>
                    {roles.map(role => (
                      <div
                        key={role.id}
                        draggable
                        onDragStart={(e) => handleDragStart(e, role, 'role')}
                        className={`flex items-center gap-2 p-2 rounded cursor-move transition-colors ${
                          isDarkMode ? 'hover:bg-[#2a2a2a]' : 'hover:bg-gray-100'
                        }`}
                      >
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: role.color === '#000000' ? '#99aab5' : role.color }}
                        ></div>
                        <span className={`${themeStyles.primaryText} text-sm truncate`}>
                          {role.name}
                        </span>
                        <span className={`${themeStyles.secondaryText} text-xs ml-auto`}>
                          {role.member_count} members
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Configuration Options - Right Side */}
            <div className={`${isDarkMode ? "bg-[#101010]" : "bg-white"} rounded-xl p-5 lg:col-span-2`}>
              <div className="flex items-center gap-2 mb-4">
                <span className="text-purple-400">🔧</span>
                <p className={`text-lg font-medium ${themeStyles.primaryText}`}>
                  Configuration Options
                </p>
              </div>
              <p className={`${themeStyles.secondaryText} text-sm mb-6`}>
                Configure your bot settings by dragging channels/categories/roles or entering values
              </p>

              <div className="space-y-4 max-h-[70vh] overflow-y-auto">
                {Object.entries(config).map(([key, configOption]) => (
                  <div
                    key={key}
                    className={`border rounded-lg p-4 transition-colors ${
                      isConfigModified(key) 
                        ? 'border-blue-400 bg-blue-400 bg-opacity-5' 
                        : isDarkMode ? 'border-gray-700' : 'border-gray-200'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-lg">{getConfigIcon(configOption.type)}</span>
                          <h4 className={`font-medium ${themeStyles.primaryText}`}>
                            {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </h4>
                          {isConfigModified(key) && (
                            <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded">
                              Modified
                            </span>
                          )}
                        </div>
                        <p className={`${themeStyles.secondaryText} text-sm`}>
                          {configOption.description}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs px-2 py-1 rounded ${
                          isDarkMode ? 'bg-gray-700' : 'bg-gray-200'
                        }`}>
                          {configOption.type}
                        </span>
                        <div className={`w-3 h-3 rounded-full ${
                          configOption.is_set || isConfigModified(key) ? 'bg-green-400' : 'bg-gray-400'
                        }`}></div>
                      </div>
                    </div>

                    {/* Input/Drop Zone */}
                    {['TextChannel', 'CategoryChannel', 'Role'].includes(configOption.type) ? (
                      <div
                        onDragOver={handleDragOver}
                        onDrop={(e) => handleDrop(e, key, configOption.type)}
                        className={getDropZoneStyle(configOption.type, false)}
                      >
                        {getCurrentValue(key) ? (
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="text-green-400">{getConfigIcon(configOption.type)}</span>
                              <span className={themeStyles.primaryText}>
                                {getItemDisplayName(getCurrentValue(key), configOption.type) || `ID: ${getCurrentValue(key)}`}
                              </span>
                              {configOption.type === 'Role' && (() => {
                                const role = roles.find(r => String(r.id) === String(getCurrentValue(key)));
                                return role ? (
                                  <div 
                                    className="w-3 h-3 rounded-full ml-1" 
                                    style={{ backgroundColor: role.color === '#000000' ? '#99aab5' : role.color }}
                                  ></div>
                                ) : null;
                              })()}
                            </div>
                            <button
                              onClick={() => handleConfigUpdate(key, null, configOption.type)}
                              className="text-red-400 hover:text-red-300 text-sm"
                            >
                              ✕ Remove
                            </button>
                          </div>
                        ) : (
                          <div className="text-center">
                            <p className={`${themeStyles.secondaryText} text-sm`}>
                              Drop a {configOption.type.replace('Channel', ' Channel').toLowerCase()} here
                            </p>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {configOption.type === 'bool' ? (
                          <div className="flex items-center gap-3">
                            <label className="flex items-center cursor-pointer">
                              <input
                                type="checkbox"
                                checked={getCurrentValue(key) === true || getCurrentValue(key) === 'true'}
                                onChange={(e) => handleConfigUpdate(key, e.target.checked, configOption.type)}
                                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                              />
                              <span className={`ml-2 ${themeStyles.primaryText}`}>
                                {getCurrentValue(key) === true || getCurrentValue(key) === 'true' ? 'Enabled' : 'Disabled'}
                              </span>
                            </label>
                          </div>
                        ) : (
                          <input
                            type={configOption.type === 'int' || configOption.type === 'float' ? 'number' : 'text'}
                            value={getCurrentValue(key)}
                            onChange={(e) => handleConfigUpdate(key, e.target.value, configOption.type)}
                            placeholder={`Enter ${configOption.type} value...`}
                            step={configOption.type === 'float' ? '0.01' : undefined}
                            className={`w-full px-3 py-2 border rounded-lg ${
                              isDarkMode 
                                ? 'bg-[#2a2a2a] border-gray-600 text-white placeholder-gray-400' 
                                : 'bg-white border-gray-300 text-gray-800 placeholder-gray-500'
                            } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                          />
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
      
      <Footer isDarkMode={isDarkMode} />
    </div>
  );
};

export default Config;
