import React, { useState, useEffect, useCallback } from "react";
import { useLocation } from "react-router-dom";
import Header from "../components/header";
import Footer from "../components/footer";

const Listings = () => {
  const location = useLocation();
  const [listings, setListings] = useState({ accounts: [], alts: [], profiles: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [filters, setFilters] = useState({
    catacombs_level: 0,
    coins: 0,
    networth: 0,
    skill_average: 0,
    zombie_slayer: 0,
    spider_slayer: 0,
    wolf_slayer: 0,
    enderman_slayer: 0,
    blaze_slayer: 0,
    vampire_slayer: 0,
    maxPrice: 10000,
    minPrice: 0,
    type: "all" // all, account, alt, profile
  });
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [filteredItems, setFilteredItems] = useState([]);
  const [unlistingItems, setUnlistingItems] = useState(new Set());

  // Dark mode effect
  useEffect(() => {
    const savedMode = localStorage.getItem("darkMode");
    if (savedMode !== null) {
      setIsDarkMode(savedMode === "true");
    }
  }, []);

  // Check authentication
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

  // Fetch listings data
  const fetchListings = async (botName) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(`https://v2.noemt.dev/api/bot/${botName}/listed/items`, {
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
        throw new Error(`Failed to fetch listings: ${response.status}`);
      }
      
      const data = await response.json();
      if (data.success) {
        setListings(data.data);
      } else {
        setError("Failed to load listings data");
      }
    } catch (err) {
      console.error("Error fetching listings:", err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Initialize app
  useEffect(() => {
    const initializeApp = async () => {
      const isAuth = await checkAuth();
      
      if (isAuth) {
        const pathParts = location.pathname.split('/').filter(part => part);
        const botName = pathParts[0];
        
        if (botName && botName !== 'dashboard') {
          await fetchListings(botName);
        } else {
          setError("Bot name not specified in URL path.");
          setIsLoading(false);
        }
      } else {
        setIsLoading(false);
      }
    };

    initializeApp();
  }, [location.pathname]);

  function unabbreviateNumber(num) {
    if (!num) return 0;
    const numString = num.toString().toLowerCase();
    const numMap = { k: 1e3, m: 1e6, b: 1e9, t: 1e12 };
    
    const lastChar = numString.slice(-1);
    const numPart = parseFloat(numString.slice(0, -1));
    
    return numMap[lastChar] ? numPart * numMap[lastChar] : parseFloat(numString);
  }

  function formatNumber(num) {
    if (!num) return "0";
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  // Apply filters
  useEffect(() => {
    if (!isMenuOpen) {
      const applyFilters = () => {
        let allItems = [];
        
        if (filters.type === "all" || filters.type === "account") {
          allItems = allItems.concat(listings.accounts);
        }
        if (filters.type === "all" || filters.type === "alt") {
          allItems = allItems.concat(listings.alts);
        }
        if (filters.type === "all" || filters.type === "profile") {
          allItems = allItems.concat(listings.profiles);
        }

        return allItems.filter((item) => {
          const stats = item.stats || {};
          
          return (
            parseFloat(stats.catacombs_level || 0) >= filters.catacombs_level &&
            parseFloat(unabbreviateNumber(stats.liquid_networth || 0)) >= filters.coins &&
            parseFloat(unabbreviateNumber(stats.total_networth || 0)) >= filters.networth &&
            parseFloat(stats.skill_average || 0) >= filters.skill_average &&
            parseFloat(stats.zombie_slayer_level || 0) >= filters.zombie_slayer &&
            parseFloat(stats.spider_slayer_level || 0) >= filters.spider_slayer &&
            parseFloat(stats.wolf_slayer_level || 0) >= filters.wolf_slayer &&
            parseFloat(stats.enderman_slayer_level || 0) >= filters.enderman_slayer &&
            parseFloat(stats.blaze_slayer_level || 0) >= filters.blaze_slayer &&
            parseFloat(stats.vampire_slayer_level || 0) >= filters.vampire_slayer &&
            parseFloat(item.price) <= filters.maxPrice &&
            parseFloat(item.price) >= filters.minPrice
          );
        });
      };

      setFilteredItems(applyFilters());
    }
  }, [listings, filters, isMenuOpen]);

  const handleFilterChange = useCallback((e, field) => {
    setFilters((prev) => ({ ...prev, [field]: field === 'type' ? e.target.value : parseFloat(e.target.value) }));
  }, []);

  const handleUnlistItem = async (channelId, messageId) => {
    const itemKey = `${channelId}-${messageId}`;
    
    // Confirm before unlisting
    if (!window.confirm("Are you sure you want to unlist this item?")) {
      return;
    }
    
    try {
      setUnlistingItems(prev => new Set([...prev, itemKey]));
      
      const pathParts = location.pathname.split('/').filter(part => part);
      const botName = pathParts[0];
      
      const response = await fetch(`https://v2.noemt.dev/api/bot/${botName}/unlist/item`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          channel_id: channelId,
          message_id: messageId
        })
      });
      
      if (response.ok) {
        // Show success notification
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg z-50 transition-opacity';
        notification.textContent = 'Item unlisted successfully!';
        document.body.appendChild(notification);
        
        setTimeout(() => {
          notification.style.opacity = '0';
          setTimeout(() => document.body.removeChild(notification), 300);
        }, 3000);
        
        // Refresh listings after successful unlist
        await fetchListings(botName);
      } else {
        const error = await response.json();
        alert(`Failed to unlist item: ${error.detail || 'Unknown error'}`);
      }
    } catch (err) {
      console.error("Error unlisting item:", err);
      alert("Failed to unlist item");
    } finally {
      setUnlistingItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(itemKey);
        return newSet;
      });
    }
  };

  // Dynamic styles based on theme
  const themeStyles = {
    background: isDarkMode ? "#070707" : "#f0f2f5",
    cardBg: isDarkMode ? "#101010" : "#ffffff",
    primaryText: isDarkMode ? "text-white" : "text-gray-800",
    secondaryText: isDarkMode ? "text-[#aaa]" : "text-gray-600",
  };

  // Display loading state
  if (isLoading) {
    return (
      <div className={`flex flex-col min-h-screen items-center justify-center ${isDarkMode ? "bg-[#070707] text-white" : "bg-[#f0f2f5] text-gray-800"}`}>
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
        <p>Loading listings...</p>
      </div>
    );
  }

  // Display authentication required state
  if (!isAuthenticated) {
    return (
      <div className={`flex flex-col min-h-screen items-center justify-center ${isDarkMode ? "bg-[#070707] text-white" : "bg-[#f0f2f5] text-gray-800"}`}>
        <div className="text-center">
          <div className="mb-6">
            <span className="text-6xl mb-4 block">🔐</span>
            <h1 className="text-3xl font-bold mb-2">Authentication Required</h1>
            <p className={`${isDarkMode ? "text-gray-400" : "text-gray-600"} mb-6`}>
              Please login with Discord to access the listings
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Display error state
  if (error) {
    return (
      <div className={`flex flex-col min-h-screen items-center justify-center ${isDarkMode ? "bg-[#070707] text-white" : "bg-[#f0f2f5] text-gray-800"}`}>
        <div className="bg-red-500 text-white p-4 rounded-lg mb-4 max-w-md text-center">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col min-h-screen ${isDarkMode ? "bg-[#070707]" : "bg-[#f0f2f5]"}`}>
      <Header 
        isDarkMode={isDarkMode} 
        toggleDarkMode={() => setIsDarkMode(!isDarkMode)}
        user={user}
      />

      {/* Filters Button */}
      <button
        onClick={() => setIsMenuOpen((prev) => !prev)}
        className="fixed bottom-4 left-4 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg z-50 transition-colors"
      >
        Filters
      </button>

      {/* Filter Modal */}
      {isMenuOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setIsMenuOpen(false)}
        >
          <div
            className={`${isDarkMode ? "bg-[#101010]" : "bg-white"} p-6 rounded-lg w-full max-w-md mx-4 max-h-[80vh] overflow-y-auto`}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4">
              <h3 className={`text-xl font-bold ${themeStyles.primaryText}`}>Filters</h3>
              <button
                onClick={() => setIsMenuOpen(false)}
                className="text-gray-400 hover:text-gray-600 text-xl"
              >
                ✕
              </button>
            </div>

            <div className="flex flex-col gap-4">
              {/* Type Filter */}
              <div className="flex flex-col">
                <label className={`mb-2 ${themeStyles.primaryText}`}>Type</label>
                <select
                  value={filters.type}
                  onChange={(e) => handleFilterChange(e, 'type')}
                  className={`p-2 rounded border ${isDarkMode ? "bg-[#2a2a2a] border-gray-600 text-white" : "bg-white border-gray-300 text-gray-800"}`}
                >
                  <option value="all">All Types</option>
                  <option value="account">Accounts</option>
                  <option value="alt">Alts</option>
                  <option value="profile">Profiles</option>
                </select>
              </div>

              {/* Numeric Filters */}
              {[
                { label: "Catacombs Level", field: "catacombs_level", max: 60 },
                { label: "Coins", field: "coins", max: 20000000000, step: 1000000 },
                { label: "Networth", field: "networth", max: 200000000000, step: 10000000 },
                { label: "Skill Average", field: "skill_average", max: 55 },
                { label: "Zombie Slayer", field: "zombie_slayer", max: 9 },
                { label: "Spider Slayer", field: "spider_slayer", max: 9 },
                { label: "Wolf Slayer", field: "wolf_slayer", max: 9 },
                { label: "Enderman Slayer", field: "enderman_slayer", max: 9 },
                { label: "Blaze Slayer", field: "blaze_slayer", max: 9 },
                { label: "Vampire Slayer", field: "vampire_slayer", max: 5 },
                { label: "Max Price", field: "maxPrice", max: 10000, step: 10 },
                { label: "Min Price", field: "minPrice", max: 10000, step: 10 },
              ].map((filter) => (
                <div key={filter.field} className="flex flex-col">
                  <label className={`mb-2 ${themeStyles.primaryText}`}>
                    {filter.label}: {formatNumber(filters[filter.field])}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max={filter.max}
                    step={filter.step || 1}
                    value={filters[filter.field]}
                    onChange={(e) => handleFilterChange(e, filter.field)}
                    className="w-full"
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <main className="flex-grow p-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-between items-center mb-6">
            <h1 className={`text-3xl font-bold ${themeStyles.primaryText}`}>
              Listed Items ({filteredItems.length})
            </h1>
            <button
              onClick={() => {
                const pathParts = location.pathname.split('/').filter(part => part);
                const botName = pathParts[0];
                if (botName) fetchListings(botName);
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              🔄 Refresh
            </button>
          </div>
          
          {/* Stats Summary */}
          {listings.accounts.length > 0 || listings.alts.length > 0 || listings.profiles.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className={`${isDarkMode ? "bg-[#101010]" : "bg-white"} p-4 rounded-lg`}>
                <p className={`text-sm ${themeStyles.secondaryText}`}>Total Items</p>
                <p className={`text-2xl font-bold ${themeStyles.primaryText}`}>
                  {listings.accounts.length + listings.alts.length + listings.profiles.length}
                </p>
              </div>
              <div className={`${isDarkMode ? "bg-[#101010]" : "bg-white"} p-4 rounded-lg border-l-4 border-blue-400`}>
                <p className={`text-sm ${themeStyles.secondaryText}`}>Accounts</p>
                <p className={`text-2xl font-bold ${themeStyles.primaryText}`}>
                  {listings.accounts.length}
                </p>
              </div>
              <div className={`${isDarkMode ? "bg-[#101010]" : "bg-white"} p-4 rounded-lg border-l-4 border-green-400`}>
                <p className={`text-sm ${themeStyles.secondaryText}`}>Alts</p>
                <p className={`text-2xl font-bold ${themeStyles.primaryText}`}>
                  {listings.alts.length}
                </p>
              </div>
              <div className={`${isDarkMode ? "bg-[#101010]" : "bg-white"} p-4 rounded-lg border-l-4 border-purple-400`}>
                <p className={`text-sm ${themeStyles.secondaryText}`}>Profiles</p>
                <p className={`text-2xl font-bold ${themeStyles.primaryText}`}>
                  {listings.profiles.length}
                </p>
              </div>
            </div>
          ) : null}
          
          {filteredItems.length === 0 ? (
            <div className={`text-center py-12 ${isDarkMode ? "bg-[#101010]" : "bg-white"} rounded-lg`}>
              <span className="text-6xl mb-4 block">📋</span>
              <p className={`text-xl ${themeStyles.primaryText} mb-2`}>
                {listings.accounts.length === 0 && listings.alts.length === 0 && listings.profiles.length === 0 
                  ? "No items listed yet" 
                  : "No items match your filters"}
              </p>
              <p className={`${themeStyles.secondaryText}`}>
                {listings.accounts.length === 0 && listings.alts.length === 0 && listings.profiles.length === 0 
                  ? "Listed items will appear here once added to your bot" 
                  : "Try adjusting your filter criteria"}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {filteredItems.map((item) => (
                <ItemCard 
                  key={`${item.type}-${item.uuid}-${item.number}`} 
                  item={item} 
                  isDarkMode={isDarkMode}
                  themeStyles={themeStyles}
                  onUnlist={handleUnlistItem}
                  isUnlisting={unlistingItems.has(`${item.channel_id}-${item.message_id}`)}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      <Footer isDarkMode={isDarkMode} />
    </div>
  );
};

const ItemCard = React.memo(({ item, isDarkMode, themeStyles, onUnlist, isUnlisting }) => {
  const stats = item.stats || {};
  
  const getTypeIcon = () => {
    switch (item.type) {
      case 'account': return '👤';
      case 'alt': return '🔄';
      case 'profile': return '📊';
      default: return '❓';
    }
  };

  const getTypeColor = () => {
    switch (item.type) {
      case 'account': return 'border-blue-400';
      case 'alt': return 'border-green-400';
      case 'profile': return 'border-purple-400';
      default: return 'border-gray-400';
    }
  };

  const formatNetworth = (value) => {
    return value
  };

  return (
    <div className={`${isDarkMode ? "bg-[#101010]" : "bg-white"} rounded-lg p-4 border-l-4 ${getTypeColor()} relative`}>
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xl">{getTypeIcon()}</span>
            <h3 className={`text-lg font-bold ${themeStyles.primaryText}`}>
              {item.type.charAt(0).toUpperCase() + item.type.slice(1)} #{item.number}
            </h3>
          </div>
          {item.show_username && item.username ? (
            <a 
              href={`https://sky.shiiyu.moe/stats/${item.username}`}
              target="_blank"
              rel="noopener noreferrer"
              className={`text-sm ${themeStyles.secondaryText} hover:text-blue-400 transition-colors underline`}
            >
              🎮 {item.username}
            </a>
          ) : (
            <p className={`text-sm ${themeStyles.secondaryText}`}>
              🔒 Anonymous User
            </p>
          )}
        </div>
        
        <div className="text-right">
          <p className={`text-xl font-bold text-green-400`}>
            💰 ${item.price}
          </p>
          <button
            onClick={() => onUnlist(item.channel_id, item.message_id)}
            disabled={isUnlisting}
            className={`px-3 py-1 rounded text-sm mt-2 transition-colors ${
              isUnlisting 
                ? 'bg-gray-500 cursor-not-allowed' 
                : 'bg-red-600 hover:bg-red-700'
            } text-white`}
          >
            {isUnlisting ? '⏳ Unlisting...' : '🗑️ Unlist'}
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {stats.skill_average && (
          <div>
            <p className={`text-xs ${themeStyles.secondaryText}`}>⚔️ Skill Average</p>
            <p className={`text-sm font-medium ${themeStyles.primaryText}`}>{stats.skill_average}</p>
          </div>
        )}
        
        {stats.catacombs_level && (
          <div>
            <p className={`text-xs ${themeStyles.secondaryText}`}>🏴‍☠️ Catacombs</p>
            <p className={`text-sm font-medium ${themeStyles.primaryText}`}>{stats.catacombs_level}</p>
          </div>
        )}
        
        {stats.total_networth && (
          <div>
            <p className={`text-xs ${themeStyles.secondaryText}`}>💎 Networth</p>
            <p className={`text-sm font-medium ${themeStyles.primaryText}`}>{formatNetworth(stats.total_networth)}</p>
          </div>
        )}
        
        {stats.skyblock_level && (
          <div>
            <p className={`text-xs ${themeStyles.secondaryText}`}>🌟 SB Level</p>
            <p className={`text-sm font-medium ${themeStyles.primaryText}`}>{stats.skyblock_level}</p>
          </div>
        )}
      </div>

      {/* Slayers */}
      {(stats.zombie_slayer_level || stats.spider_slayer_level || stats.wolf_slayer_level) && (
        <div className="mb-3">
          <p className={`text-xs ${themeStyles.secondaryText} mb-1`}>🔥 Slayers</p>
          <p className={`text-sm ${themeStyles.primaryText}`}>
            🧟‍♂️{stats.zombie_slayer_level || 0}/🕷️{stats.spider_slayer_level || 0}/🐺{stats.wolf_slayer_level || 0}/👁️{stats.enderman_slayer_level || 0}/🔥{stats.blaze_slayer_level || 0}/🧛{stats.vampire_slayer_level || 0}
          </p>
        </div>
      )}

      {/* Payment Methods */}
      {item.payment_methods && (
        <div className="mb-3">
          <p className={`text-xs ${themeStyles.secondaryText} mb-1`}>💳 Payment Methods</p>
          <p 
            className={`text-sm ${themeStyles.primaryText} truncate cursor-help`}
            title={item.payment_methods}
          >
            {item.payment_methods}
          </p>
        </div>
      )}

      {/* Additional Info */}
      {item.additional_information && (
        <div className="mb-3">
          <p className={`text-xs ${themeStyles.secondaryText} mb-1`}>📝 Additional Info</p>
          <p className={`text-sm ${themeStyles.primaryText} break-words`}>{item.additional_information}</p>
        </div>
      )}

      {/* Alt-specific fields */}
      {item.type === 'alt' && (item.farming || item.mining) && (
        <div className="mb-3">
          <p className={`text-xs ${themeStyles.secondaryText} mb-1`}>🎯 Specialization</p>
          <div className="flex gap-2">
            {item.farming && <span className="bg-green-600 text-white px-2 py-1 rounded text-xs">🌾 Farming</span>}
            {item.mining && <span className="bg-orange-600 text-white px-2 py-1 rounded text-xs">⛏️ Mining</span>}
          </div>
        </div>
      )}

      {/* Mining and HOTM Stats for accounts and alts */}
      {(item.type === 'account' || item.type === 'alt') && (stats.heart_of_the_mountain_level || stats.mithril_powder || stats.gemstone_powder || stats.glaciate_powder) && (
        <div className="mb-3">
          <p className={`text-xs ${themeStyles.secondaryText} mb-1`}>⛏️ Heart of the Mountain</p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {stats.heart_of_the_mountain_level && (
              <div>
                <span className={themeStyles.secondaryText}>🏔️ Level: </span>
                <span className={themeStyles.primaryText}>{stats.heart_of_the_mountain_level}</span>
              </div>
            )}
            {stats.mithril_powder && (
              <div>
                <span className={themeStyles.secondaryText}>🟢 Mithril: </span>
                <span className={themeStyles.primaryText}>{formatNetworth(stats.mithril_powder)}</span>
              </div>
            )}
            {stats.gemstone_powder && (
              <div>
                <span className={themeStyles.secondaryText}>💎 Gemstone: </span>
                <span className={themeStyles.primaryText}>{formatNetworth(stats.gemstone_powder)}</span>
              </div>
            )}
            {stats.glaciate_powder && (
              <div>
                <span className={themeStyles.secondaryText}>❄️ Glacite: </span>
                <span className={themeStyles.primaryText}>{formatNetworth(stats.glaciate_powder)}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Profile-specific fields */}
      {item.type === 'profile' && (
        <div className="mb-3">
          <p className={`text-xs ${themeStyles.secondaryText} mb-1`}>📊 Profile Stats</p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {stats.minion_slots && (
              <div>
                <span className={themeStyles.secondaryText}>🤖 Minions: </span>
                <span className={themeStyles.primaryText}>{stats.minion_slots}</span>
              </div>
            )}
            {stats.minion_bonus_slots && (
              <div>
                <span className={themeStyles.secondaryText}>⭐ Bonus: </span>
                <span className={themeStyles.primaryText}>{stats.minion_bonus_slots}</span>
              </div>
            )}
            {stats.maxed_collections && (
              <div>
                <span className={themeStyles.secondaryText}>🏆 Maxed: </span>
                <span className={themeStyles.primaryText}>{stats.maxed_collections}</span>
              </div>
            )}
            {stats.unlocked_collections && (
              <div>
                <span className={themeStyles.secondaryText}>🔓 Unlocked: </span>
                <span className={themeStyles.primaryText}>{stats.unlocked_collections}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Networth breakdown for accounts and alts */}
      {(item.type === 'account' || item.type === 'alt') && (stats.soulbound_networth || stats.liquid_networth) && (
        <div className="mb-3">
          <p className={`text-xs ${themeStyles.secondaryText} mb-1`}>💰 Networth Breakdown</p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {stats.liquid_networth && (
              <div>
                <span className={themeStyles.secondaryText}>💧 Liquid: </span>
                <span className={themeStyles.primaryText}>{formatNetworth(stats.liquid_networth)}</span>
              </div>
            )}
            {stats.soulbound_networth && (
              <div>
                <span className={themeStyles.secondaryText}>🔗 Soulbound: </span>
                <span className={themeStyles.primaryText}>{formatNetworth(stats.soulbound_networth)}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Listed by section */}
      {item.listed_by && (
        <div className={`mt-4 pt-3 border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
          <ListedByCard listedBy={item.listed_by} isDarkMode={isDarkMode} themeStyles={themeStyles} />
        </div>
      )}
    </div>
  );
});

const ListedByCard = React.memo(({ listedBy, isDarkMode, themeStyles }) => {
  const location = useLocation();
  const [userInfo, setUserInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        setLoading(true);
        
        // Extract bot name from URL
        const pathParts = location.pathname.split('/').filter(part => part);
        const botName = pathParts[0];
        
        if (botName && listedBy) {
          const response = await fetch(`https://v2.noemt.dev/api/bot/${botName}/users/info`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify([listedBy])
          });
          
          if (response.ok) {
            const result = await response.json();
            if (result.success && result.data && result.data[listedBy]) {
              setUserInfo({
                id: listedBy,
                ...result.data[listedBy]
              });
            } else {
              // Fallback if user not found
              setUserInfo({ id: listedBy, username: `User ${listedBy}`, error: true });
            }
          } else {
            setUserInfo({ id: listedBy, username: `User ${listedBy}`, error: true });
          }
        }
      } catch (err) {
        console.error("Error fetching user info:", err);
        setUserInfo({ id: listedBy, username: `User ${listedBy}`, error: true });
      } finally {
        setLoading(false);
      }
    };

    if (listedBy) {
      fetchUserInfo();
    }
  }, [listedBy, location.pathname]);

  if (loading) {
    return (
      <div className="flex items-center gap-2">
        <div className={`w-6 h-6 rounded-full ${isDarkMode ? 'bg-gray-700' : 'bg-gray-300'} animate-pulse`}></div>
        <div className={`h-4 w-20 ${isDarkMode ? 'bg-gray-700' : 'bg-gray-300'} rounded animate-pulse`}></div>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <div className="w-6 h-6 rounded-full overflow-hidden bg-purple-600">
        {userInfo?.avatar && !userInfo.error ? (
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
        <div 
          className="w-full h-full bg-purple-600 flex items-center justify-center text-white text-xs" 
          style={{ display: (userInfo?.avatar && !userInfo.error) ? 'none' : 'flex' }}
        >
          👤
        </div>
      </div>
      <div>
        <p className={`text-xs ${themeStyles.secondaryText}`}>👑 Listed by</p>
        <p className={`text-xs ${themeStyles.primaryText} font-medium`}>
          {userInfo?.error ? 
            `User ${listedBy}` : 
            (userInfo?.display_name || userInfo?.name || userInfo?.username || `User ${listedBy}`)
          }
        </p>
      </div>
    </div>
  );
});

export default React.memo(Listings);
