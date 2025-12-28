import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import SellerHeader from "../components/SellerHeader";
import Footer from "../components/footer";

const SellerDashboard = () => {
  const navigate = useNavigate();
  
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [configuration, setConfiguration] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [syncResults, setSyncResults] = useState(null);

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

  const handleLogin = () => {
    const currentUrl = encodeURIComponent(window.location.href);
    window.location.href = `https://v2.noemt.dev/auth/discord/login?redirect_url=${currentUrl}`;
  };

  const fetchAccounts = async () => {
    try {
      const response = await fetch('https://v2.noemt.dev/api/seller/accounts', {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setAccounts(data);
      } else if (response.status === 401) {
        setIsAuthenticated(false);
      }
    } catch (err) {
      console.error("Error fetching accounts:", err);
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
      }
    } catch (err) {
      console.error("Error fetching configuration:", err);
    }
  };

  const getPaymentMethodsString = () => {
    if (configuration?.servers) {
      const successfulServer = Object.values(configuration.servers).find(result => result.success && result.data);
      if (successfulServer?.data?.payment_methods) {
        let paymentMethods = successfulServer.data.payment_methods;
        if (Array.isArray(paymentMethods)) {
          return paymentMethods.join('/');
        } else if (typeof paymentMethods === 'string') {
          return paymentMethods;
        }
      }
    }
    return null;
  };

  const handleSyncAll = async () => {
    if (!accounts?.servers) return;
    
    setSyncing(true);
    setSyncResults(null);
    
    try {
      const syncPromises = [];
      
      // Sync accounts across all servers
      Object.values(accounts.servers).forEach(serverData => {
        if (serverData.success && serverData.data?.accounts) {
          serverData.data.accounts.forEach(account => {
            let itemData = {
              username: account.username,
              price: parseInt(account.price) // Ensure it's an int
            };
            
            // Add optional fields for accounts
            if (account.additional_information && account.additional_information !== "No Information Provided.") {
              itemData.additional_information = account.additional_information;
            }
            if (account.show_ign !== undefined) {
              itemData.show_ign = account.show_ign;
            }
            if (account.profile) {
              itemData.profile = account.profile;
            }
            
            // Add payment methods from configuration
            const paymentMethodsString = getPaymentMethodsString();
            if (paymentMethodsString) {
              itemData.payment_methods = paymentMethodsString;
            }
            
            const syncPromise = fetch('https://v2.noemt.dev/api/seller/list', {
              method: 'POST',
              credentials: 'include',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                type: 'account',
                item: itemData
              })
            });
            syncPromises.push(syncPromise);
          });
        }
        
        // Sync profiles
        if (serverData.success && serverData.data?.profiles) {
          serverData.data.profiles.forEach(profile => {
            let itemData = {
              username: profile.username,
              price: parseInt(profile.price) // Ensure it's an int
            };
            
            // Add optional fields for profiles
            if (profile.additional_information && profile.additional_information !== "No Information Provided.") {
              itemData.additional_information = profile.additional_information;
            }
            if (profile.show_ign !== undefined) {
              itemData.show_ign = profile.show_ign;
            }
            if (profile.profile) {
              itemData.profile = profile.profile;
            }
            
            // Add payment methods from configuration
            const paymentMethodsString = getPaymentMethodsString();
            if (paymentMethodsString) {
              itemData.payment_methods = paymentMethodsString;
            }
            
            const syncPromise = fetch('https://v2.noemt.dev/api/seller/list', {
              method: 'POST',
              credentials: 'include',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                type: 'profile',
                item: itemData
              })
            });
            syncPromises.push(syncPromise);
          });
        }
        
        // Sync alts
        if (serverData.success && serverData.data?.alts) {
          serverData.data.alts.forEach(alt => {
            let itemData = {
              username: alt.username,
              price: parseInt(alt.price), // Ensure it's an int
              farming: alt.farming !== false, // Default to true if not specified
              mining: alt.mining === true     // Default to false if not specified
            };
            
            // Ensure at least one of farming/mining is true
            if (!itemData.farming && !itemData.mining) {
              itemData.farming = true; // Default to farming if both are false
            }
            
            // Add payment methods from configuration
            const paymentMethodsString = getPaymentMethodsString();
            if (paymentMethodsString) {
              itemData.payment_methods = paymentMethodsString;
            }
            
            const syncPromise = fetch('https://v2.noemt.dev/api/seller/list', {
              method: 'POST',
              credentials: 'include',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                type: 'alt',
                item: itemData
              })
            });
            syncPromises.push(syncPromise);
          });
        }
      });
      
      const results = await Promise.allSettled(syncPromises);
      const successful = results.filter(result => result.status === 'fulfilled' && result.value.ok).length;
      const total = results.length;
      
      setSyncResults({
        successful,
        total,
        failed: total - successful
      });
    } catch (err) {
      console.error("Error syncing:", err);
      setError("Failed to sync accounts");
    } finally {
      setSyncing(false);
    }
  };

  // Dynamic styles based on theme
  const themeStyles = {
    background: isDarkMode ? 'bg-[#070707]' : 'bg-gray-50',
    cardBg: isDarkMode ? 'bg-[#101010]' : 'bg-white',
    text: isDarkMode ? 'text-white' : 'text-gray-800',
    secondaryText: isDarkMode ? 'text-gray-400' : 'text-gray-600',
    border: isDarkMode ? 'border-gray-700' : 'border-gray-200',
    input: isDarkMode ? 'bg-[#1a1a1a] border-gray-600' : 'bg-white border-gray-300',
    button: isDarkMode ? 'bg-indigo-600 hover:bg-indigo-700' : 'bg-indigo-600 hover:bg-indigo-700',
  };

  if (loading) {
    return (
      <div className={`flex flex-col min-h-screen ${themeStyles.background}`}>
        <div className="flex flex-col min-h-screen items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
          <p className={themeStyles.text}>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className={`flex flex-col min-h-screen ${themeStyles.background}`}>
        <SellerHeader
          isDarkMode={isDarkMode}
          toggleDarkMode={toggleDarkMode}
          user={user}
          onLogout={handleLogout}
        />
        
        <div className="flex-1 flex items-center justify-center px-4">
          <div className={`${themeStyles.cardBg} rounded-xl p-8 shadow-lg text-center max-w-md w-full border ${themeStyles.border}`}>
            <div className="mb-6">
              <svg className="w-16 h-16 mx-auto text-indigo-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <h2 className={`text-2xl font-bold ${themeStyles.text} mb-2`}>Authentication Required</h2>
              <p className={themeStyles.secondaryText}>
                Please log in with Discord to access your seller dashboard.
              </p>
            </div>
            
            <button
              onClick={handleLogin}
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.211.375-.445.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z"/>
              </svg>
              Login with Discord
            </button>
          </div>
        </div>
        
        <Footer isDarkMode={isDarkMode} />
      </div>
    );
  }

  // Calculate total counts
  const getTotalCounts = () => {
    if (!accounts?.servers) return { accounts: 0, profiles: 0, alts: 0, servers: 0 };
    
    let totalAccounts = 0;
    let totalProfiles = 0;
    let totalAlts = 0;
    let totalServers = 0;
    
    Object.values(accounts.servers).forEach(serverData => {
      if (serverData.success && serverData.data) {
        totalServers++;
        totalAccounts += serverData.data.accounts?.length || 0;
        totalProfiles += serverData.data.profiles?.length || 0;
        totalAlts += serverData.data.alts?.length || 0;
      }
    });
    
    return { accounts: totalAccounts, profiles: totalProfiles, alts: totalAlts, servers: totalServers };
  };

  const counts = getTotalCounts();

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

        {/* Welcome Section */}
        <div className={`${themeStyles.cardBg} rounded-xl p-6 shadow-lg border ${themeStyles.border} mb-6`}>
          <h1 className={`text-2xl font-bold ${themeStyles.text} mb-2`}>
            👋 Welcome back, {user?.username || user?.display_name || user?.global_name || 'User'}!
          </h1>
          <p className={themeStyles.secondaryText}>
            🎯 Manage your listings across all servers from one centralized dashboard.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <div className={`${themeStyles.cardBg} rounded-xl p-6 shadow-lg border ${themeStyles.border}`}>
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-blue-100 dark:bg-blue-900 mr-4">
                <span className="text-2xl">👤</span>
              </div>
              <div>
                <p className={`text-2xl font-bold ${themeStyles.text}`}>{counts.accounts}</p>
                <p className={themeStyles.secondaryText}>📊 Accounts</p>
              </div>
            </div>
          </div>

          <div className={`${themeStyles.cardBg} rounded-xl p-6 shadow-lg border ${themeStyles.border}`}>
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-green-100 dark:bg-green-900 mr-4">
                <span className="text-2xl">📋</span>
              </div>
              <div>
                <p className={`text-2xl font-bold ${themeStyles.text}`}>{counts.profiles}</p>
                <p className={themeStyles.secondaryText}>📈 Profiles</p>
              </div>
            </div>
          </div>

          <div className={`${themeStyles.cardBg} rounded-xl p-6 shadow-lg border ${themeStyles.border}`}>
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-purple-100 dark:bg-purple-900 mr-4">
                <span className="text-2xl">🔄</span>
              </div>
              <div>
                <p className={`text-2xl font-bold ${themeStyles.text}`}>{counts.alts}</p>
                <p className={themeStyles.secondaryText}>⚡ Alts</p>
              </div>
            </div>
          </div>

          <div className={`${themeStyles.cardBg} rounded-xl p-6 shadow-lg border ${themeStyles.border}`}>
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-orange-100 dark:bg-orange-900 mr-4">
                <span className="text-2xl">🖥️</span>
              </div>
              <div>
                <p className={`text-2xl font-bold ${themeStyles.text}`}>{counts.servers}</p>
                <p className={themeStyles.secondaryText}>🌐 Servers</p>
              </div>
            </div>
          </div>
        </div>

        {/* Sync Section */}
        <div className={`${themeStyles.cardBg} rounded-xl p-6 shadow-lg border ${themeStyles.border} mb-6`}>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4">
            <div>
              <h2 className={`text-xl font-bold ${themeStyles.text} mb-2`}>🔄 Sync Across Servers</h2>
              <p className={themeStyles.secondaryText}>
                ⚡ Synchronize all your listings across every server to ensure consistency.
              </p>
            </div>
            <button
              onClick={handleSyncAll}
              disabled={syncing || !accounts?.servers || Object.keys(accounts.servers).length === 0}
              className={`mt-4 sm:mt-0 px-6 py-3 ${themeStyles.button} text-white font-medium rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2`}
            >
              {syncing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
                  🔄 Syncing...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  🚀 Sync All Listings
                </>
              )}
            </button>
          </div>

          {syncResults && (
            <div className={`p-4 rounded-lg ${syncResults.failed === 0 ? 'bg-green-100 border border-green-200' : 'bg-yellow-100 border border-yellow-200'} mb-4`}>
              <p className={`font-medium ${syncResults.failed === 0 ? 'text-green-800' : 'text-yellow-800'}`}>
                Sync completed: {syncResults.successful}/{syncResults.total} successful
                {syncResults.failed > 0 && `, ${syncResults.failed} failed`}
              </p>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className={`${themeStyles.cardBg} rounded-xl p-6 shadow-lg border ${themeStyles.border}`}>
          <h2 className={`text-xl font-bold ${themeStyles.text} mb-4`}>⚡ Quick Actions</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <button
              onClick={() => navigate('/listings')}
              className={`p-4 rounded-lg border ${themeStyles.border} hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors duration-200 text-left`}
            >
              <h3 className={`font-medium ${themeStyles.text} mb-1`}>📋 View Listings</h3>
              <p className={`text-sm ${themeStyles.secondaryText}`}>🔍 Manage your current listings</p>
            </button>
            
            <button
              onClick={() => navigate('/configuration')}
              className={`p-4 rounded-lg border ${themeStyles.border} hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors duration-200 text-left`}
            >
              <h3 className={`font-medium ${themeStyles.text} mb-1`}>⚙️ Configuration</h3>
              <p className={`text-sm ${themeStyles.secondaryText}`}>🛠️ Update your seller settings</p>
            </button>
            
            <button
              onClick={() => {
                // Navigate to listings with new item mode
                navigate('/listings?new=true');
              }}
              className={`p-4 rounded-lg border ${themeStyles.border} hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors duration-200 text-left`}
            >
              <h3 className={`font-medium ${themeStyles.text} mb-1`}>➕ New Listing</h3>
              <p className={`text-sm ${themeStyles.secondaryText}`}>✨ Create a new listing</p>
            </button>
          </div>
        </div>
      </div>
      
      <Footer isDarkMode={isDarkMode} />
    </div>
  );
};

export default SellerDashboard;
