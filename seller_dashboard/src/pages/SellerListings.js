import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import SellerHeader from "../components/SellerHeader";
import Footer from "../components/footer";

const SellerListings = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isNewListing = searchParams.get('new') === 'true';
  
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [configuration, setConfiguration] = useState(null);
  const [showNewListingForm, setShowNewListingForm] = useState(isNewListing);
  const [activeTab, setActiveTab] = useState('accounts');
  const [usersInfo, setUsersInfo] = useState({});
  const [listingFormData, setListingFormData] = useState({
    type: 'account',
    username: '',
    price: '',
    additional_information: '',
    show_ign: true,
    profile: '',
    farming: true,
    mining: false
  });
  const [submittingListing, setSubmittingListing] = useState(false);
  const [validatingUsername, setValidatingUsername] = useState(false);
  const [usernameValid, setUsernameValid] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  // Username validation function
  const validateUsername = async (username) => {
    if (!username || username.length < 3) {
      setUsernameValid(false);
      return false;
    }
    
    setValidatingUsername(true);
    try {
      const response = await fetch(`https://mowojang.matdoes.dev/${username}`);
      if (response.ok) {
        const data = await response.json();
        if (data.id && data.name) {
          setUsernameValid(true);
          return true;
        }
      }
      setUsernameValid(false);
      return false;
    } catch (err) {
      console.error("Error validating username:", err);
      setUsernameValid(false);
      return false;
    } finally {
      setValidatingUsername(false);
    }
  };

  // Debounced username validation
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (listingFormData.username) {
        validateUsername(listingFormData.username);
      } else {
        setUsernameValid(null);
      }
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [listingFormData.username]);

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
        await Promise.all([
          fetchAccounts(),
          fetchConfiguration()
        ]);
      }
      setLoading(false);
    };

    initializeApp();
  }, []);

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
        console.log('Auth/me response:', userData);
        
        if (userData.authenticated && userData.user_info) {
          // Extract user info and construct avatar URL
          const userInfo = userData.user_info;
          const avatarUrl = userInfo.avatar 
            ? `https://cdn.discordapp.com/avatars/${userInfo.id}/${userInfo.avatar}.png`
            : null;
          
          const processedUser = {
            ...userInfo,
            avatar: avatarUrl,
            discord_id: userData.discord_id
          };
          
          setUser(processedUser);
          setIsAuthenticated(true);
          return true;
        } else {
          setIsAuthenticated(false);
          return false;
        }
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
      navigate('/auth');
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  const fetchAccounts = async () => {
    setRefreshing(true);
    try {
      const response = await fetch('https://v2.noemt.dev/api/seller/accounts', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        // The endpoint returns server-based structure with accounts, profiles, alts in each server's data
        setAccounts(data);
        
        // Fetch user info for all unique user IDs from listings
        const userIds = new Set();
        if (data?.servers) {
          Object.values(data.servers).forEach(serverData => {
            if (serverData.success && serverData.data) {
              [...(serverData.data.accounts || []), ...(serverData.data.profiles || []), ...(serverData.data.alts || [])]
                .forEach(item => {
                  if (item.listed_by) {
                    userIds.add(item.listed_by);
                  }
                });
            }
          });
        }
      } else if (response.status === 401) {
        setIsAuthenticated(false);
        navigate('/auth');
      }
    } catch (err) {
      console.error("Error fetching accounts:", err);
      setError("Failed to fetch listings");
    } finally {
      setRefreshing(false);
    }
  };

  const fetchConfiguration = async () => {
    try {
      const response = await fetch('https://v2.noemt.dev/api/seller/configuration', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setConfiguration(data);
      } else if (response.status === 401) {
        setIsAuthenticated(false);
        navigate('/auth');
      }
    } catch (err) {
      console.error("Error fetching configuration:", err);
    }
  };

  const handleSubmitListing = async (e) => {
    e.preventDefault();
    
    // Validate username first
    if (!usernameValid) {
      setError("Please enter a valid Minecraft username");
      return;
    }
    
    // Validate alt farming/mining
    if (listingFormData.type === 'alt' && !listingFormData.farming && !listingFormData.mining) {
      setError("For alts, at least one of farming or mining must be selected");
      return;
    }
    
    setSubmittingListing(true);
    setError(null);

    try {
      let itemData = {
        username: listingFormData.username,
        price: parseInt(listingFormData.price) // Convert to int as required
      };

      // Add optional fields for accounts and profiles
      if (listingFormData.type === 'account' || listingFormData.type === 'profile') {
        if (listingFormData.additional_information.trim()) {
          itemData.additional_information = listingFormData.additional_information;
        }
        itemData.show_ign = listingFormData.show_ign;
        if (listingFormData.profile.trim()) {
          itemData.profile = listingFormData.profile;
        }
      }

      // Add mining/farming for alts
      if (listingFormData.type === 'alt') {
        itemData.farming = listingFormData.farming;
        itemData.mining = listingFormData.mining;
      }

      // Add payment methods from configuration
      if (configuration?.servers) {
        const successfulServer = Object.values(configuration.servers).find(result => result.success && result.data);
        if (successfulServer?.data?.payment_methods) {
          let paymentMethods = successfulServer.data.payment_methods;
          if (Array.isArray(paymentMethods)) {
            itemData.payment_methods = paymentMethods.join('/');
          } else if (typeof paymentMethods === 'string') {
            itemData.payment_methods = paymentMethods;
          }
        }
      }

      const response = await fetch('https://v2.noemt.dev/api/seller/list', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: listingFormData.type,
          item: itemData
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Listing result:', result);
        
        // Reset form
        setListingFormData({
          type: 'account',
          username: '',
          price: '',
          additional_information: '',
          show_ign: true,
          profile: '',
          farming: true,
          mining: false
        });
        
        setUsernameValid(null);
        setShowNewListingForm(false);
        
        // Refresh listings
        await fetchAccounts();
        
        // Show success message
        alert('Listing created successfully! It may take a moment to appear in all servers.');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to create listing');
      }
    } catch (err) {
      console.error("Error creating listing:", err);
      setError("Failed to create listing");
    } finally {
      setSubmittingListing(false);
    }
  };

  // Dynamic styles based on theme
  const themeStyles = {
    background: isDarkMode ? 'bg-[#070707]' : 'bg-gray-50',
    cardBg: isDarkMode ? 'bg-[#101010]' : 'bg-white',
    text: isDarkMode ? 'text-white' : 'text-gray-800',
    secondaryText: isDarkMode ? 'text-gray-400' : 'text-gray-600',
    border: isDarkMode ? 'border-gray-700' : 'border-gray-200',
    input: isDarkMode ? 'bg-[#1a1a1a] border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900',
    button: isDarkMode ? 'bg-indigo-600 hover:bg-indigo-700' : 'bg-indigo-600 hover:bg-indigo-700',
  };

  if (loading) {
    return (
      <div className={`flex flex-col min-h-screen ${themeStyles.background}`}>
        <div className="flex flex-col min-h-screen items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
          <p className={themeStyles.text}>Loading listings...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    navigate('/auth');
    return null;
  }

  // Get all listings organized by type
  const getAllListings = () => {
    if (!accounts?.servers) return { accounts: [], profiles: [], alts: [] };
    
    const allAccounts = [];
    const allProfiles = [];
    const allAlts = [];
    
    // Track unique listings by key to avoid duplicates
    const seenAccounts = new Set();
    const seenProfiles = new Set();
    const seenAlts = new Set();
    
    Object.entries(accounts.servers).forEach(([serverName, serverData]) => {
      if (serverData.success && serverData.data) {
        // Process accounts
        if (serverData.data.accounts) {
          serverData.data.accounts.forEach(account => {
            const uniqueKey = `${account.uuid}_${account.number}_${account.profile || 'none'}`;
            if (!seenAccounts.has(uniqueKey)) {
              seenAccounts.add(uniqueKey);
              allAccounts.push({ ...account, server: serverName });
            }
          });
        }
        
        // Process profiles
        if (serverData.data.profiles) {
          serverData.data.profiles.forEach(profile => {
            const uniqueKey = `${profile.uuid}_${profile.number}_${profile.profile || 'none'}`;
            if (!seenProfiles.has(uniqueKey)) {
              seenProfiles.add(uniqueKey);
              allProfiles.push({ ...profile, server: serverName });
            }
          });
        }
        
        // Process alts
        if (serverData.data.alts) {
          serverData.data.alts.forEach(alt => {
            const uniqueKey = `${alt.uuid}_${alt.number}_${alt.farming}_${alt.mining}`;
            if (!seenAlts.has(uniqueKey)) {
              seenAlts.add(uniqueKey);
              allAlts.push({ ...alt, server: serverName });
            }
          });
        }
      }
    });
    
    return { accounts: allAccounts, profiles: allProfiles, alts: allAlts };
  };

  const listings = getAllListings();

  const formatNumber = (num) => {
    if (!num) return "0";
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'account': return '👤';
      case 'alt': return '🔄';
      case 'profile': return '📊';
      default: return '❓';
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'account': return 'border-blue-400';
      case 'alt': return 'border-green-400';
      case 'profile': return 'border-purple-400';
      default: return 'border-gray-400';
    }
  };

  const renderListingItem = (item, type) => {
    const stats = item.stats || {};
    
    return (
      <div key={`${item.uuid}-${item.number || Math.random()}`} className={`${themeStyles.cardBg} rounded-lg p-4 border-l-4 ${getTypeColor(type)} relative`}>
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">{getTypeIcon(type)}</span>
              <h3 className={`text-lg font-bold ${themeStyles.text}`}>
                {type.charAt(0).toUpperCase() + type.slice(1)} #{item.number}
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
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          {stats.skill_average && (
            <div>
              <p className={`text-xs ${themeStyles.secondaryText}`}>⚔️ Skill Average</p>
              <p className={`text-sm font-medium ${themeStyles.text}`}>{stats.skill_average}</p>
            </div>
          )}
          
          {stats.catacombs_level && (
            <div>
              <p className={`text-xs ${themeStyles.secondaryText}`}>🏴‍☠️ Catacombs</p>
              <p className={`text-sm font-medium ${themeStyles.text}`}>{stats.catacombs_level}</p>
            </div>
          )}
          
          {stats.total_networth && (
            <div>
              <p className={`text-xs ${themeStyles.secondaryText}`}>💎 Networth</p>
              <p className={`text-sm font-medium ${themeStyles.text}`}>{stats.total_networth}</p>
            </div>
          )}
          
          {stats.skyblock_level && (
            <div>
              <p className={`text-xs ${themeStyles.secondaryText}`}>🌟 SB Level</p>
              <p className={`text-sm font-medium ${themeStyles.text}`}>{stats.skyblock_level}</p>
            </div>
          )}
        </div>

        {/* Slayers */}
        {(stats.zombie_slayer_level || stats.spider_slayer_level || stats.wolf_slayer_level) && (
          <div className="mb-3">
            <p className={`text-xs ${themeStyles.secondaryText} mb-1`}>🔥 Slayers</p>
            <p className={`text-sm ${themeStyles.text}`}>
              🧟‍♂️{stats.zombie_slayer_level || 0}/🕷️{stats.spider_slayer_level || 0}/🐺{stats.wolf_slayer_level || 0}/👁️{stats.enderman_slayer_level || 0}/🔥{stats.blaze_slayer_level || 0}/🧛{stats.vampire_slayer_level || 0}
            </p>
          </div>
        )}

        {/* Payment Methods */}
        {item.payment_methods && (
          <div className={`text-sm ${themeStyles.secondaryText} mb-3`}>
            <p className={`text-xs ${themeStyles.secondaryText} mb-1`}>💳 Payment Methods</p>
            <span 
              className="tooltip-hover cursor-help"
              title={item.payment_methods}
            >
              {item.payment_methods.length > 50 
                ? `${item.payment_methods.substring(0, 50)}...` 
                : item.payment_methods
              }
            </span>
          </div>
        )}

        {/* Additional Info */}
        {item.additional_information && (
          <div className="mb-3">
            <p className={`text-xs ${themeStyles.secondaryText} mb-1`}>📝 Additional Info</p>
            <p className={`text-sm ${themeStyles.text} break-words`}>{item.additional_information}</p>
          </div>
        )}

        {/* Profile name for profiles */}
        {item.profile && (
          <div className="mb-3">
            <p className={`text-xs ${themeStyles.secondaryText} mb-1`}>📊 Profile</p>
            <p className={`text-sm ${themeStyles.text}`}>{item.profile}</p>
          </div>
        )}

        {/* Alt-specific fields */}
        {type === 'alt' && (item.farming || item.mining) && (
          <div className="mb-3">
            <p className={`text-xs ${themeStyles.secondaryText} mb-1`}>🎯 Specialization</p>
            <div className="flex gap-2">
              {item.farming && <span className="bg-green-600 text-white px-2 py-1 rounded text-xs">🌾 Farming</span>}
              {item.mining && <span className="bg-orange-600 text-white px-2 py-1 rounded text-xs">⛏️ Mining</span>}
            </div>
          </div>
        )}

        {/* Mining and HOTM Stats for accounts and alts */}
        {(type === 'account' || type === 'alt') && (stats.heart_of_the_mountain_level || stats.mithril_powder || stats.gemstone_powder || stats.glaciate_powder) && (
          <div className="mb-3">
            <p className={`text-xs ${themeStyles.secondaryText} mb-1`}>⛏️ Heart of the Mountain</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {stats.heart_of_the_mountain_level && (
                <div>
                  <span className={themeStyles.secondaryText}>🏔️ Level: </span>
                  <span className={themeStyles.text}>{stats.heart_of_the_mountain_level}</span>
                </div>
              )}
              {stats.mithril_powder && (
                <div>
                  <span className={themeStyles.secondaryText}>🟢 Mithril: </span>
                  <span className={themeStyles.text}>{formatNumber(stats.mithril_powder)}</span>
                </div>
              )}
              {stats.gemstone_powder && (
                <div>
                  <span className={themeStyles.secondaryText}>💎 Gemstone: </span>
                  <span className={themeStyles.text}>{formatNumber(stats.gemstone_powder)}</span>
                </div>
              )}
              {stats.glaciate_powder && (
                <div>
                  <span className={themeStyles.secondaryText}>❄️ Glacite: </span>
                  <span className={themeStyles.text}>{formatNumber(stats.glaciate_powder)}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Profile-specific fields */}
        {type === 'profile' && (
          <div className="mb-3">
            <p className={`text-xs ${themeStyles.secondaryText} mb-1`}>📊 Profile Stats</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {stats.minion_slots && (
                <div>
                  <span className={themeStyles.secondaryText}>🤖 Minions: </span>
                  <span className={themeStyles.text}>{stats.minion_slots}</span>
                </div>
              )}
              {stats.minion_bonus_slots && (
                <div>
                  <span className={themeStyles.secondaryText}>⭐ Bonus: </span>
                  <span className={themeStyles.text}>{stats.minion_bonus_slots}</span>
                </div>
              )}
              {stats.maxed_collections && (
                <div>
                  <span className={themeStyles.secondaryText}>🏆 Maxed: </span>
                  <span className={themeStyles.text}>{stats.maxed_collections}</span>
                </div>
              )}
              {stats.unlocked_collections && (
                <div>
                  <span className={themeStyles.secondaryText}>🔓 Unlocked: </span>
                  <span className={themeStyles.text}>{stats.unlocked_collections}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Networth breakdown for accounts and alts */}
        {(type === 'account' || type === 'alt') && (stats.soulbound_networth || stats.liquid_networth) && (
          <div className="mb-3">
            <p className={`text-xs ${themeStyles.secondaryText} mb-1`}>💰 Networth Breakdown</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {stats.liquid_networth && (
                <div>
                  <span className={themeStyles.secondaryText}>💧 Liquid: </span>
                  <span className={themeStyles.text}>{stats.liquid_networth}</span>
                </div>
              )}
              {stats.soulbound_networth && (
                <div>
                  <span className={themeStyles.secondaryText}>🔗 Soulbound: </span>
                  <span className={themeStyles.text}>{stats.soulbound_networth}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Listed by section */}
        {item.listed_by && (
          <div className={`mt-4 pt-3 border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
            <ListedByCard listedBy={item.listed_by} isDarkMode={isDarkMode} themeStyles={themeStyles} usersInfo={usersInfo} />
          </div>
        )}
      </div>
    );
  };

  const ListedByCard = ({ listedBy, isDarkMode, themeStyles, usersInfo }) => {
    const userInfo = usersInfo[listedBy] || { id: listedBy };
    const hasError = userInfo.error;

    return (
      <div className="flex items-center gap-2">
        <div className="w-6 h-6 rounded-full overflow-hidden bg-purple-600">
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
          <div 
            className="w-full h-full bg-purple-600 flex items-center justify-center text-white text-xs" 
            style={{ display: (!hasError && userInfo.avatar) ? 'none' : 'flex' }}
          >
            👤
          </div>
        </div>
        <div>
          <p className={`text-xs ${themeStyles.secondaryText}`}>👑 Listed by</p>
          <p className={`text-xs ${themeStyles.text} font-medium`}>
            {hasError ? 
              `User ${listedBy}` : 
              (userInfo.display_name || userInfo.global_name || userInfo.username || `User ${listedBy}`)
            }
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className={`flex flex-col min-h-screen ${themeStyles.background}`}>
      <SellerHeader
        isDarkMode={isDarkMode}
        toggleDarkMode={toggleDarkMode}
        user={user}
        onLogout={handleLogout}
      />
      
      <div className="flex-1 px-4 py-6 max-w-7xl mx-auto w-full">
        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {/* Header with New Listing Button */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
          <h1 className={`text-2xl font-bold ${themeStyles.text} mb-4 sm:mb-0`}>📋 My Listings</h1>
          <div className="flex gap-3">
            <button
              onClick={() => fetchAccounts()}
              disabled={refreshing}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors duration-200 flex items-center gap-2"
            >
              <div className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`}>
                {refreshing ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                )}
              </div>
              {refreshing ? 'Refreshing...' : '🔄 Refresh'}
            </button>
            <button
              onClick={() => setShowNewListingForm(!showNewListingForm)}
              className={`px-6 py-3 ${themeStyles.button} text-white font-medium rounded-lg transition-colors duration-200 flex items-center gap-2`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              {showNewListingForm ? '❌ Cancel' : '✨ New Listing'}
            </button>
          </div>
        </div>

        {/* Stats Summary */}
        {listings.accounts.length > 0 || listings.alts.length > 0 || listings.profiles.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className={`${themeStyles.cardBg} p-4 rounded-lg border ${themeStyles.border}`}>
              <p className={`text-sm ${themeStyles.secondaryText}`}>📊 Total Items</p>
              <p className={`text-2xl font-bold ${themeStyles.text}`}>
                {listings.accounts.length + listings.alts.length + listings.profiles.length}
              </p>
            </div>
            <div className={`${themeStyles.cardBg} p-4 rounded-lg border-l-4 border-blue-400 ${themeStyles.border}`}>
              <p className={`text-sm ${themeStyles.secondaryText}`}>👤 Accounts</p>
              <p className={`text-2xl font-bold ${themeStyles.text}`}>
                {listings.accounts.length}
              </p>
            </div>
            <div className={`${themeStyles.cardBg} p-4 rounded-lg border-l-4 border-green-400 ${themeStyles.border}`}>
              <p className={`text-sm ${themeStyles.secondaryText}`}>🔄 Alts</p>
              <p className={`text-2xl font-bold ${themeStyles.text}`}>
                {listings.alts.length}
              </p>
            </div>
            <div className={`${themeStyles.cardBg} p-4 rounded-lg border-l-4 border-purple-400 ${themeStyles.border}`}>
              <p className={`text-sm ${themeStyles.secondaryText}`}>📊 Profiles</p>
              <p className={`text-2xl font-bold ${themeStyles.text}`}>
                {listings.profiles.length}
              </p>
            </div>
          </div>
        ) : null}

        {/* New Listing Form */}
        {showNewListingForm && (
          <div className={`${themeStyles.cardBg} rounded-xl p-6 shadow-lg border ${themeStyles.border} mb-6`}>
            <h2 className={`text-xl font-bold ${themeStyles.text} mb-4`}>✨ Create New Listing</h2>
            <form onSubmit={handleSubmitListing} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className={`block text-sm font-medium ${themeStyles.text} mb-1`}>🏷️ Type</label>
                  <select
                    value={listingFormData.type}
                    onChange={(e) => setListingFormData({...listingFormData, type: e.target.value})}
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${themeStyles.input}`}
                    required
                  >
                    <option value="account">Account</option>
                    <option value="profile">Profile</option>
                    <option value="alt">Alt</option>
                  </select>
                </div>

                <div>
                  <label className={`block text-sm font-medium ${themeStyles.text} mb-1`}>💰 Price ($)</label>
                  <input
                    type="number"
                    min="0"
                    step="1"
                    value={listingFormData.price}
                    onChange={(e) => setListingFormData({...listingFormData, price: e.target.value})}
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${themeStyles.input}`}
                    placeholder="Enter price (whole numbers only)"
                    required
                  />
                  <p className={`mt-1 text-xs ${themeStyles.secondaryText}`}>
                    Price must be a whole number (integer)
                  </p>
                </div>
              </div>

              <div>
                <label className={`block text-sm font-medium ${themeStyles.text} mb-1`}>🎮 Username</label>
                <div className="relative">
                  <input
                    type="text"
                    value={listingFormData.username}
                    onChange={(e) => setListingFormData({...listingFormData, username: e.target.value})}
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 pr-10 ${themeStyles.input} ${
                      usernameValid === true ? 'border-green-500' : usernameValid === false ? 'border-red-500' : ''
                    }`}
                    placeholder="Enter Minecraft username"
                    required
                  />
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                    {validatingUsername ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-indigo-500"></div>
                    ) : usernameValid === true ? (
                      <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                      </svg>
                    ) : usernameValid === false ? (
                      <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    ) : null}
                  </div>
                </div>
                {usernameValid === false && (
                  <p className="mt-1 text-sm text-red-600">Invalid Minecraft username</p>
                )}
              </div>

              {/* Additional fields for accounts and profiles */}
              {(listingFormData.type === 'account' || listingFormData.type === 'profile') && (
                <>
                  <div>
                    <label className={`block text-sm font-medium ${themeStyles.text} mb-1`}>📝 Additional Information (Optional)</label>
                    <textarea
                      value={listingFormData.additional_information}
                      onChange={(e) => setListingFormData({...listingFormData, additional_information: e.target.value})}
                      className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${themeStyles.input}`}
                      rows="3"
                      placeholder="Default: No Information Provided."
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className={`block text-sm font-medium ${themeStyles.text} mb-1`}>📊 Profile (Optional)</label>
                      <input
                        type="text"
                        value={listingFormData.profile}
                        onChange={(e) => setListingFormData({...listingFormData, profile: e.target.value})}
                        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${themeStyles.input}`}
                        placeholder="Profile name"
                      />
                    </div>

                    <div className="flex items-end">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={listingFormData.show_ign}
                          onChange={(e) => setListingFormData({...listingFormData, show_ign: e.target.checked})}
                          className="mr-2"
                        />
                        <span className={`text-sm ${themeStyles.text}`}>👁️ Show Username (Default: true)</span>
                      </label>
                    </div>
                  </div>
                </>
              )}

              {/* Mining/Farming fields for alts */}
              {listingFormData.type === 'alt' && (
                <div>
                  <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>🎯 Alt Type (At least one must be selected)</label>
                  <div className="flex gap-4">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={listingFormData.farming}
                        onChange={(e) => setListingFormData({...listingFormData, farming: e.target.checked})}
                        className="mr-2"
                      />
                      <span className={`text-sm ${themeStyles.text}`}>🌾 Farming</span>
                    </label>

                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={listingFormData.mining}
                        onChange={(e) => setListingFormData({...listingFormData, mining: e.target.checked})}
                        className="mr-2"
                      />
                      <span className={`text-sm ${themeStyles.text}`}>⛏️ Mining</span>
                    </label>
                  </div>
                  {!listingFormData.farming && !listingFormData.mining && (
                    <p className="mt-1 text-sm text-red-600">At least one of farming or mining must be selected</p>
                  )}
                </div>
              )}

              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={submittingListing || !usernameValid || (listingFormData.type === 'alt' && !listingFormData.farming && !listingFormData.mining)}
                  className={`px-6 py-3 ${themeStyles.button} text-white font-medium rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2`}
                >
                  {submittingListing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
                      Creating...
                    </>
                  ) : (
                    'Create Listing'
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setShowNewListingForm(false)}
                  className={`px-6 py-3 bg-gray-500 hover:bg-gray-600 text-white font-medium rounded-lg transition-colors duration-200`}
                >
                  ❌ Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Tabs */}
        <div className="flex border-b border-gray-200 dark:border-gray-700 mb-6">
          <button
            onClick={() => setActiveTab('accounts')}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors duration-200 ${
              activeTab === 'accounts'
                ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            👤 Accounts ({listings.accounts.length})
          </button>
          <button
            onClick={() => setActiveTab('profiles')}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors duration-200 ${
              activeTab === 'profiles'
                ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            📊 Profiles ({listings.profiles.length})
          </button>
          <button
            onClick={() => setActiveTab('alts')}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors duration-200 ${
              activeTab === 'alts'
                ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            🔄 Alts ({listings.alts.length})
          </button>
        </div>

        {/* Listings Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {activeTab === 'accounts' && listings.accounts.map(account => renderListingItem(account, 'account'))}
          {activeTab === 'profiles' && listings.profiles.map(profile => renderListingItem(profile, 'profile'))}
          {activeTab === 'alts' && listings.alts.map(alt => renderListingItem(alt, 'alt'))}
        </div>

        {/* Empty State */}
        {((activeTab === 'accounts' && listings.accounts.length === 0) ||
          (activeTab === 'profiles' && listings.profiles.length === 0) ||
          (activeTab === 'alts' && listings.alts.length === 0)) && (
          <div className={`${themeStyles.cardBg} rounded-xl p-8 shadow-lg border ${themeStyles.border} text-center`}>
            <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2M4 13h2m6 0h2m-6 3v2m0 0h4m-4 0H6" />
            </svg>
            <h3 className={`text-lg font-medium ${themeStyles.text} mb-2`}>🔍 No {activeTab} found</h3>
            <p className={themeStyles.secondaryText}>
              You don't have any {activeTab} listed yet. Create a new listing to get started! 🚀
            </p>
            <button
              onClick={() => setShowNewListingForm(true)}
              className={`mt-4 px-6 py-3 ${themeStyles.button} text-white font-medium rounded-lg transition-colors duration-200`}
            >
              ✨ Create First Listing
            </button>
          </div>
        )}
      </div>
      
      <Footer isDarkMode={isDarkMode} />
    </div>
  );
};

export default SellerListings;
