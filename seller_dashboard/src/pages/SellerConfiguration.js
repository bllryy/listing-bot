import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import SellerHeader from "../components/SellerHeader";
import Footer from "../components/footer";

const SellerConfiguration = () => {
  const navigate = useNavigate();
  
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [configuration, setConfiguration] = useState(null);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  const [formData, setFormData] = useState({
    sellauth: {
      store_id: '',
      store_name: '',
      product_id: '',
      variant_id: ''
    },
    payment_methods: [],
    payment_details: {
      paypal_email: '',
      business_name: '',
      currency: '',
      bitcoin_address: '',
      ethereum_address: '',
      litecoin_address: ''
    }
  });

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
        await fetchConfiguration();
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

  const fetchConfiguration = async () => {
    try {
      const response = await fetch('https://v2.noemt.dev/api/seller/configuration', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setConfiguration(data);
        
        // Parse the configuration from all servers and merge
        const mergedConfig = {
          sellauth: {
            store_id: '',
            store_name: '',
            product_id: '',
            variant_id: ''
          },
          payment_methods: [],
          payment_details: {
            paypal_email: '',
            business_name: '',
            currency: '',
            bitcoin_address: '',
            ethereum_address: '',
            litecoin_address: ''
          }
        };

        const allowedPaymentMethods = ['paypal', 'bitcoin', 'litecoin', 'ethereum', 'venmo', 'cashapp', 'zelle', 'paysafecard', 'google_pay', 'apple_pay', 'binance_pay', 'swap', 'bank_transfer', 'usdc', 'usdt', 'solana'];
        let allUsedMethods = new Set();

        // Get configuration from the first successful server response
        if (data.servers) {
          const successfulServer = Object.values(data.servers).find(result => result.success && result.data);
          if (successfulServer) {
            const serverData = successfulServer.data;
            
            if (serverData.sellauth) {
              mergedConfig.sellauth = { ...mergedConfig.sellauth, ...serverData.sellauth };
            }
            
            if (serverData.payment_methods) {
              let methods = Array.isArray(serverData.payment_methods) 
                ? serverData.payment_methods 
                : typeof serverData.payment_methods === 'string' 
                  ? serverData.payment_methods.split(/[\/,]/).map(m => m.trim()).filter(m => m)
                  : [];
              
              // Collect all used methods
              methods.forEach(method => allUsedMethods.add(method.toLowerCase()));
              
              // Filter to only allowed methods
              const validMethods = methods.filter(method => allowedPaymentMethods.includes(method.toLowerCase()));
              const invalidMethods = methods.filter(method => !allowedPaymentMethods.includes(method.toLowerCase()));
              
              if (invalidMethods.length > 0) {
                // Show user which methods are invalid and suggest correction
                const suggestedMethods = Array.from(allUsedMethods).filter(method => allowedPaymentMethods.includes(method));
                const correctedString = suggestedMethods.join('/');
                
                if (window.confirm(
                  `Found invalid payment methods: ${invalidMethods.join(', ')}\n\n` +
                  `Valid methods are: ${allowedPaymentMethods.join(', ')}\n\n` +
                  `Would you like to update your configuration to: ${correctedString}?`
                )) {
                  mergedConfig.payment_methods = suggestedMethods;
                } else {
                  mergedConfig.payment_methods = validMethods;
                }
              } else {
                mergedConfig.payment_methods = validMethods;
              }
            }
            
            if (serverData.payment_details) {
              mergedConfig.payment_details = { ...mergedConfig.payment_details, ...serverData.payment_details };
            }
          }
        }

        setFormData(mergedConfig);
      } else if (response.status === 401) {
        setIsAuthenticated(false);
        navigate('/auth');
      }
    } catch (err) {
      console.error("Error fetching configuration:", err);
      setError("Failed to fetch configuration");
    }
  };

  const handleSaveConfiguration = async () => {
    setSaving(true);
    setError(null);
    setSuccessMessage('');

    try {
      const response = await fetch('https://v2.noemt.dev/api/seller/configuration', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Configuration update result:', result);
        setSuccessMessage('Configuration saved successfully across all servers!');
        
        // Clear success message after 3 seconds
        setTimeout(() => setSuccessMessage(''), 3000);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to save configuration');
      }
    } catch (err) {
      console.error("Error saving configuration:", err);
      setError("Failed to save configuration");
    } finally {
      setSaving(false);
    }
  };

  const handlePaymentMethodToggle = (method) => {
    const currentMethods = formData.payment_methods || [];
    if (currentMethods.includes(method)) {
      setFormData({
        ...formData,
        payment_methods: currentMethods.filter(m => m !== method)
      });
    } else {
      setFormData({
        ...formData,
        payment_methods: [...currentMethods, method]
      });
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
          <p className={themeStyles.text}>Loading configuration...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    navigate('/auth');
    return null;
  }

  const availablePaymentMethods = ['paypal', 'bitcoin', 'litecoin', 'ethereum', 'venmo', 'cashapp', 'zelle', 'paysafecard', 'google_pay', 'apple_pay', 'binance_pay', 'swap', 'bank_transfer', 'usdc', 'usdt', 'solana'];

  return (
    <div className={`flex flex-col min-h-screen ${themeStyles.background}`}>
      <SellerHeader
        isDarkMode={isDarkMode}
        toggleDarkMode={toggleDarkMode}
        user={user}
        onLogout={handleLogout}
      />
      
      <div className="flex-1 px-4 py-6 max-w-4xl mx-auto w-full">
        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {successMessage && (
          <div className="mb-6 p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg">
            {successMessage}
          </div>
        )}

        <h1 className={`text-2xl font-bold ${themeStyles.text} mb-6`}>⚙️ Seller Configuration</h1>

        {/* SellAuth Configuration */}
        <div className={`${themeStyles.cardBg} rounded-xl p-6 shadow-lg border ${themeStyles.border} mb-6`}>
          <h2 className={`text-xl font-bold ${themeStyles.text} mb-4`}>🔗 SellAuth Integration</h2>
          <p className={`${themeStyles.secondaryText} mb-4`}>
            🛒 Configure your SellAuth store integration for automated sales handling.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={`block text-sm font-medium ${themeStyles.text} mb-1`}>Store ID</label>
              <input
                type="text"
                value={formData.sellauth.store_id || ''}
                onChange={(e) => setFormData({
                  ...formData,
                  sellauth: { ...formData.sellauth, store_id: e.target.value }
                })}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${themeStyles.input}`}
                placeholder="Your SellAuth store ID"
              />
            </div>

            <div>
              <label className={`block text-sm font-medium ${themeStyles.text} mb-1`}>Store Name</label>
              <input
                type="text"
                value={formData.sellauth.store_name || ''}
                onChange={(e) => setFormData({
                  ...formData,
                  sellauth: { ...formData.sellauth, store_name: e.target.value }
                })}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${themeStyles.input}`}
                placeholder="Your store name"
              />
            </div>

            <div>
              <label className={`block text-sm font-medium ${themeStyles.text} mb-1`}>Product ID</label>
              <input
                type="text"
                value={formData.sellauth.product_id || ''}
                onChange={(e) => setFormData({
                  ...formData,
                  sellauth: { ...formData.sellauth, product_id: e.target.value }
                })}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${themeStyles.input}`}
                placeholder="Product ID"
              />
            </div>

            <div>
              <label className={`block text-sm font-medium ${themeStyles.text} mb-1`}>Variant ID</label>
              <input
                type="text"
                value={formData.sellauth.variant_id || ''}
                onChange={(e) => setFormData({
                  ...formData,
                  sellauth: { ...formData.sellauth, variant_id: e.target.value }
                })}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${themeStyles.input}`}
                placeholder="Variant ID"
              />
            </div>
          </div>
        </div>

        {/* Payment Methods */}
        <div className={`${themeStyles.cardBg} rounded-xl p-6 shadow-lg border ${themeStyles.border} mb-6`}>
          <h2 className={`text-xl font-bold ${themeStyles.text} mb-4`}>💳 Payment Methods</h2>
          <p className={`${themeStyles.secondaryText} mb-4`}>
            ✅ Select the payment methods you accept for your listings.
          </p>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {availablePaymentMethods.map(method => (
              <label key={method} className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.payment_methods.includes(method)}
                  onChange={() => handlePaymentMethodToggle(method)}
                  className="mr-2"
                />
                <span className={`text-sm ${themeStyles.text} capitalize`}>
                  {method.replace('_', ' ')}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Payment Details */}
        <div className={`${themeStyles.cardBg} rounded-xl p-6 shadow-lg border ${themeStyles.border} mb-6`}>
          <h2 className={`text-xl font-bold ${themeStyles.text} mb-4`}>💰 Payment Details</h2>
          <p className={`${themeStyles.secondaryText} mb-4`}>
            🔧 Configure your payment details for each method you accept.
          </p>
          
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className={`block text-sm font-medium ${themeStyles.text} mb-1`}>PayPal Email</label>
                <input
                  type="email"
                  value={formData.payment_details.paypal_email || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    payment_details: { ...formData.payment_details, paypal_email: e.target.value }
                  })}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${themeStyles.input}`}
                  placeholder="your@email.com"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium ${themeStyles.text} mb-1`}>Business Name</label>
                <input
                  type="text"
                  value={formData.payment_details.business_name || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    payment_details: { ...formData.payment_details, business_name: e.target.value }
                  })}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${themeStyles.input}`}
                  placeholder="Your business name"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium ${themeStyles.text} mb-1`}>Currency</label>
                <select
                  value={formData.payment_details.currency || 'USD'}
                  onChange={(e) => setFormData({
                    ...formData,
                    payment_details: { ...formData.payment_details, currency: e.target.value }
                  })}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${themeStyles.input}`}
                >
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                  <option value="CAD">CAD ($)</option>
                  <option value="AUD">AUD ($)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className={`block text-sm font-medium ${themeStyles.text} mb-1`}>Bitcoin Address</label>
                <input
                  type="text"
                  value={formData.payment_details.bitcoin_address || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    payment_details: { ...formData.payment_details, bitcoin_address: e.target.value }
                  })}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${themeStyles.input}`}
                  placeholder="Bitcoin wallet address"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium ${themeStyles.text} mb-1`}>Ethereum Address</label>
                <input
                  type="text"
                  value={formData.payment_details.ethereum_address || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    payment_details: { ...formData.payment_details, ethereum_address: e.target.value }
                  })}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${themeStyles.input}`}
                  placeholder="Ethereum wallet address"
                />
              </div>

              <div>
                <label className={`block text-sm font-medium ${themeStyles.text} mb-1`}>Litecoin Address</label>
                <input
                  type="text"
                  value={formData.payment_details.litecoin_address || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    payment_details: { ...formData.payment_details, litecoin_address: e.target.value }
                  })}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${themeStyles.input}`}
                  placeholder="Litecoin wallet address"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            onClick={handleSaveConfiguration}
            disabled={saving}
            className={`px-8 py-3 ${themeStyles.button} text-white font-medium rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2`}
          >
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
                💾 Saving...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
                💾 Save Configuration
              </>
            )}
          </button>
        </div>
      </div>
      
      <Footer isDarkMode={isDarkMode} />
    </div>
  );
};

export default SellerConfiguration;
