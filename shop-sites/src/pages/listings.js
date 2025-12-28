import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Footer from "../components/footer";
import initializeAuth from "../initializeAuth";
import SEO from "../components/SEO";
import getBotName from "../utils/getBotName";

const Listings = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [shopData, setShopData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedListing, setSelectedListing] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [botName, setBotName] = useState('');

  useEffect(() => {
    const initializeApp = async () => {
      try {
        const botName = await getBotName(location);
        if (botName) {
          setBotName(botName);
          await fetchShopData(botName);
        } else {
          setError("Bot name not specified. Please provide a bot name in the URL path (e.g., /your-bot-name). ");
          setLoading(false);
        }
      } catch (error) {
        setError("Failed to determine bot name. Please check your domain configuration.");
        setLoading(false);
      }
    };
    initializeApp();
  }, [location.pathname]);

  const fetchShopData = async (botName) => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`https://v2.noemt.dev/api/bot/${botName}/shop/info`);
      if (!response.ok) {
        throw new Error(`Failed to fetch shop data: ${response.status}`);
      }
      const data = await response.json();
      if (data.success) {
        setShopData(data);
      } else {
        setError("Failed to load shop data");
      }
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const getAllItems = () => {
    if (!shopData?.listings) return [];
    return Object.values(shopData.listings).flat();
  };

  const getCategories = () => {
    const items = getAllItems();
    const categories = {
      all: { name: 'All Items', items: items, color: 'text-purple-400', icon: '🛍️' },
      accounts: { 
        name: 'Accounts', 
        items: items.filter(item => 
          item.type?.toLowerCase().includes('account') || 
          item.description?.toLowerCase().includes('account') ||
          !item.type // fallback for items without explicit type
        ), 
        color: 'text-blue-400', 
        icon: '👤' 
      },
      profiles: { 
        name: 'Profiles', 
        items: items.filter(item => 
          item.type?.toLowerCase().includes('profile') || 
          item.description?.toLowerCase().includes('profile')
        ), 
        color: 'text-green-400', 
        icon: '📊' 
      },
      alts: { 
        name: 'Alts', 
        items: items.filter(item => 
          item.type?.toLowerCase().includes('alt') || 
          item.description?.toLowerCase().includes('alt') ||
          item.profile?.toLowerCase().includes('alt')
        ), 
        color: 'text-yellow-400', 
        icon: '🎭' 
      }
    };
    return categories;
  };

  const getFilteredItems = () => {
    const categories = getCategories();
    return categories[selectedCategory]?.items || [];
  };

  const formatNumber = (num) => {
    if (num >= 1000000000) {
      return (num / 1000000000).toFixed(1) + 'B';
    }
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const renderPaymentIcons = (methods) => {
    if (!methods) return null;
    return (
      <div className="flex gap-1 mt-1 flex-wrap">
        {methods.split("/").map((m, i) => (
          <img
            key={i}
            src={`/assets/${m.trim().toUpperCase()}.png`}
            alt={m.trim()}
            className="w-5 h-5 rounded"
            onError={e => (e.target.style.display = 'none')}
          />
        ))}
      </div>
    );
  };

  const handleBuyClick = async () => {
    try {
      const result = await initializeAuth(botName);
      if (result && result.url) {
        window.open(result.url, '_blank');
      } else {
        console.error('No URL received from ticket API');
      }
    } catch (error) {
      console.error('Failed to open ticket:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        {/* Header Skeleton */}
        <header className="bg-black/20 backdrop-blur-lg border-b border-white/10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <div className="h-6 w-24 bg-white/10 rounded animate-pulse"></div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="h-8 w-16 bg-white/10 rounded animate-pulse"></div>
                <div className="h-8 w-20 bg-white/10 rounded animate-pulse"></div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content Skeleton */}
        <div className="flex-1 flex min-h-[calc(100vh-4rem)]">
          {/* Left Sidebar Skeleton */}
          <div className="w-80 bg-black/30 backdrop-blur-lg border-r border-white/10 overflow-hidden flex flex-col">
            <div className="p-4 border-b border-white/10">
              <div className="h-6 w-20 bg-white/10 rounded animate-pulse"></div>
            </div>
            
            {/* Categories Skeleton */}
            <div className="p-4 border-b border-white/10">
              <div className="space-y-2">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="h-8 bg-white/5 rounded animate-pulse"></div>
                ))}
              </div>
            </div>
            
            {/* Listings Skeleton */}
            <div className="flex-1 overflow-y-auto">
              {[1, 2, 3, 4, 5, 6].map(i => (
                <div key={i} className="px-4 py-3 border-b border-white/5 flex items-center space-x-3">
                  <div className="w-4 h-4 bg-white/10 rounded animate-pulse"></div>
                  <div className="w-6 h-6 bg-white/10 rounded animate-pulse"></div>
                  <div className="flex-1">
                    <div className="h-4 w-16 bg-white/10 rounded animate-pulse mb-1"></div>
                    <div className="h-3 w-20 bg-white/10 rounded animate-pulse"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Content Skeleton */}
          <div className="flex-1 p-6">
            <div className="bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 p-8 shadow-2xl">
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center space-x-4">
                  <div className="w-16 h-16 bg-white/10 rounded-full animate-pulse"></div>
                  <div>
                    <div className="h-8 w-40 bg-white/10 rounded animate-pulse mb-2"></div>
                    <div className="h-5 w-32 bg-white/10 rounded animate-pulse"></div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="h-10 w-24 bg-white/10 rounded animate-pulse mb-2"></div>
                  <div className="h-4 w-20 bg-white/10 rounded animate-pulse"></div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="bg-white/5 rounded-xl p-4 text-center border border-white/10">
                    <div className="h-8 w-12 bg-white/10 rounded animate-pulse mx-auto mb-2"></div>
                    <div className="h-3 w-16 bg-white/10 rounded animate-pulse mx-auto"></div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 px-4">
        <div className="bg-red-500/20 backdrop-blur-lg border border-red-500/30 text-white p-8 rounded-2xl mb-8 max-w-md text-center shadow-2xl">
          <p className="font-bold text-xl mb-3 text-red-300">Error</p>
          <p className="text-red-100">{error}</p>
        </div>
        <button
          onClick={() => window.location.reload()}
          className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white px-8 py-4 rounded-xl font-semibold transition-all transform hover:scale-105 shadow-lg"
        >
          Try Again
        </button>
      </div>
    );
  }

  const categories = getCategories();
  const filteredItems = getFilteredItems();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <SEO 
        title={`Browse Listings - ${shopData?.guild?.name || "Gaming Shop"}`}
        description={`Browse ${filteredItems.length} premium gaming accounts and services. Find accounts, profiles, and alts with detailed stats and secure purchasing.`}
        keywords="browse listings, gaming accounts for sale, minecraft accounts, skyblock profiles, buy gaming accounts"
        url={location.pathname}
      />
      {/* Header */}
      <header className="bg-black/20 backdrop-blur-lg border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                noemt.dev
              </h1>
            </div>
            <nav className="flex items-center space-x-4">
              <button
                onClick={async () => {
                  const botName = await getBotName(location);
                  const hostname = window.location.hostname;
                  if (!hostname.includes('noemt.dev') && hostname !== 'localhost') {
                    navigate('/');
                  } else {
                    navigate(`/${botName}`);
                  }
                }}
                className="bg-white/10 backdrop-blur-sm hover:bg-white/20 text-white px-6 py-2 rounded-lg font-medium transition-all border border-white/20 hover:scale-105 duration-300"
              >
                Home
              </button>
              <button
                onClick={async () => {
                  const botName = await getBotName(location);
                  const hostname = window.location.hostname;
                  if (!hostname.includes('noemt.dev') && hostname !== 'localhost') {
                    navigate('/listings');
                  } else {
                    navigate(`/${botName}/listings`);
                  }
                }}
                className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white px-6 py-2 rounded-lg font-medium transition-all transform hover:scale-105 shadow-lg duration-300"
              >
                Listings
              </button>
              <button
                onClick={async () => {
                  const botName = await getBotName(location);
                  const hostname = window.location.hostname;
                  if (!hostname.includes('noemt.dev') && hostname !== 'localhost') {
                    navigate('/vouches');
                  } else {
                    navigate(`/${botName}/vouches`);
                  }
                }}
                className="bg-white/10 backdrop-blur-sm hover:bg-white/20 text-white px-6 py-2 rounded-lg font-medium transition-all border border-white/20 hover:scale-105 duration-300"
              >
                Vouches
              </button>
            </nav>
          </div>
        </div>
      </header>

      <div className="flex-1 flex min-h-[calc(100vh-4rem)]">
        <div className="w-80 bg-black/30 backdrop-blur-lg border-r border-white/10 overflow-hidden flex flex-col">
          <div className="p-4 border-b border-white/10">
            <h2 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              listings
            </h2>
          </div>
          
          <div className="border-b border-white/10 p-4 animate-fade-in-up" style={{animationDelay: '0.1s'}}>
            <div className="space-y-2">
              {Object.entries(categories).map(([key, category], index) => (
                <button
                  key={key}
                  onClick={() => setSelectedCategory(key)}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-all duration-300 flex items-center justify-between transform hover:scale-105 hover:shadow-lg animate-fade-in-up ${
                    selectedCategory === key 
                      ? 'bg-white/15 border border-white/20 shadow-lg scale-105' 
                      : 'hover:bg-white/10 border border-transparent hover:border-white/10'
                  }`}
                  style={{animationDelay: `${0.2 + (index * 0.05)}s`}}
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-lg transition-transform duration-300 hover:scale-125 hover:animate-bounce">{category.icon}</span>
                    <span className={`font-medium transition-colors duration-300 ${category.color} ${selectedCategory === key ? 'animate-pulse' : ''}`}>
                      {category.name}
                    </span>
                  </div>
                  <span className="text-xs text-gray-400 bg-white/10 px-2 py-1 rounded transition-all duration-300 hover:bg-white/20 hover:scale-110">
                    {category.items.length}
                  </span>
                </button>
              ))}
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {filteredItems.length > 0 ? (
              filteredItems.map((listing, index) => (
                <button
                  key={listing.id || index}
                  onClick={() => setSelectedListing(listing)}
                  className={`w-full text-left px-4 py-3 hover:bg-white/10 transition-all duration-300 border-b border-white/5 flex items-center justify-between group transform hover:scale-[1.02] hover:shadow-lg animate-fade-in-up ${
                    selectedListing?.id === listing.id ? 'bg-white/15 border-l-4 border-l-purple-400 shadow-lg animate-pulse-glow' : ''
                  }`}
                  style={{animationDelay: `${0.4 + (index * 0.02)}s`}}
                >
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <span className="text-gray-500 transition-colors duration-300 group-hover:text-gray-300">#</span>
                    <span className="text-yellow-400 text-lg transition-transform duration-300 group-hover:scale-125 group-hover:animate-spin">⭐</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-green-400 font-semibold text-sm transition-all duration-300 group-hover:text-green-300 group-hover:scale-105">
                        $ {listing.price}
                      </div>
                      <div className="text-gray-400 text-xs truncate transition-colors duration-300 group-hover:text-gray-300">
                        {listing.profile || `listing-${listing.number || index + 1}`}
                      </div>
                      {listing.type && (
                        <div className="text-xs text-purple-300 truncate transition-colors duration-300 group-hover:text-purple-200">
                          {listing.type}
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              ))
            ) : (
              <div className="p-6 text-center text-gray-400 animate-fade-in-up">
                <div className="text-4xl mb-2 animate-bounce">
                  {categories[selectedCategory]?.icon || '📭'}
                </div>
                <p className="transition-colors duration-300 hover:text-gray-300">No {categories[selectedCategory]?.name.toLowerCase()} available</p>
              </div>
            )}
          </div>
        </div>

        <div className="flex-1 p-6">
          {selectedListing ? (
            <div className="bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 p-8 shadow-2xl hover:shadow-purple-500/10 transition-all duration-500 animate-slide-up-fade">
              <div className="flex items-center justify-between mb-8 animate-fade-in-up">
                <div className="flex items-center space-x-4">
                  <img
                    src={selectedListing.seller?.discord_member?.avatar_url}
                    alt={selectedListing.seller?.discord_member?.display_name}
                    className="w-16 h-16 rounded-full border-4 border-purple-400 shadow-lg hover:shadow-purple-400/50 transition-all duration-300 hover:scale-110 animate-float"
                  />
                  <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent hover:from-purple-200 hover:to-pink-200 transition-all duration-300 animate-gradient-x">
                      Account on {selectedListing.profile} Profile
                    </h1>
                    <p className="text-purple-200 text-lg hover:text-purple-100 transition-colors duration-300">
                      Listed by {selectedListing.seller?.discord_member?.display_name}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-4xl font-bold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent hover:scale-110 transition-transform duration-300 animate-pulse">
                    ${selectedListing.price}
                  </div>
                  <div className="text-purple-200 hover:text-purple-100 transition-colors duration-300">
                    Listing #{selectedListing.number}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-white/5 rounded-xl p-4 text-center border border-white/10">
                  <div className="text-2xl font-bold text-purple-400 mb-1">
                    {selectedListing.stats?.catacombs_level || 0}
                  </div>
                  <div className="text-xs text-purple-200">Catacombs Level</div>
                </div>
                <div className="bg-white/5 rounded-xl p-4 text-center border border-white/10">
                  <div className="text-2xl font-bold text-green-400 mb-1">
                    {selectedListing.stats?.skill_average?.toFixed(1) || 0}
                  </div>
                  <div className="text-xs text-purple-200">Skill Average</div>
                </div>
                <div className="bg-white/5 rounded-xl p-4 text-center border border-white/10">
                  <div className="text-2xl font-bold text-blue-400 mb-1">
                    {selectedListing.stats?.total_networth ? formatNumber(parseFloat(selectedListing.stats.total_networth.replace(/[^\d.]/g, '')) * 1000000000) : '0'}
                  </div>
                  <div className="text-xs text-purple-200">Networth</div>
                </div>
                <div className="bg-white/5 rounded-xl p-4 text-center border border-white/10">
                  <div className="text-2xl font-bold text-yellow-400 mb-1">
                    {selectedListing.stats?.skyblock_level?.toFixed(0) || 0}
                  </div>
                  <div className="text-xs text-purple-200">Skyblock Level</div>
                </div>
              </div>

              {/* Slayer Stats */}
              <div className="mb-8">
                <h3 className="text-xl font-bold text-white mb-4">Slayer Progress</h3>
                <div className="grid grid-cols-5 gap-3">
                  {[
                    { name: 'Revenant Horror', level: selectedListing.stats?.zombie_slayer_level, color: 'text-green-400' },
                    { name: 'Tarantula Broodmother', level: selectedListing.stats?.spider_slayer_level, color: 'text-red-400' },
                    { name: 'Sven Packmaster', level: selectedListing.stats?.wolf_slayer_level, color: 'text-blue-400' },
                    { name: 'Voidgloom Seraph', level: selectedListing.stats?.enderman_slayer_level, color: 'text-purple-400' },
                    { name: 'Inferno Demonlord', level: selectedListing.stats?.blaze_slayer_level, color: 'text-orange-400' },
                  ].map(slayer => (
                    <div key={slayer.name} className="bg-white/5 rounded-lg p-3 text-center border border-white/10">
                      <div className={`text-xl font-bold ${slayer.color} mb-1`}>
                        {slayer.level || 0}
                      </div>
                      <div className="text-xs text-purple-200">{slayer.name}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Payment Methods & Actions */}
              <div className="flex items-center justify-between bg-white/5 rounded-2xl p-6 border border-white/10">
                <div>
                  <h3 className="text-lg font-bold text-white mb-2">Payment Methods</h3>
                  {renderPaymentIcons(selectedListing.payment_methods)}
                </div>
                <div className="flex space-x-4">
                  <button
                    onClick={handleBuyClick}
                    className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white px-6 py-3 rounded-xl font-semibold transition-all transform hover:scale-105 shadow-lg"
                  >
                    💵 Buy
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="text-6xl mb-4">🛍️</div>
                <h2 className="text-3xl font-bold text-white mb-4">Select a Listing</h2>
                <p className="text-purple-200 text-lg">
                  Choose a channel from the sidebar to view account details
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default Listings;
