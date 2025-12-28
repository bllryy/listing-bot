import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Footer from "../components/footer";
import SEO from "../components/SEO";
import getBotName from "../utils/getBotName";

const Index = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [shopData, setShopData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSeller, setSelectedSeller] = useState(null);
  const [showSellerPopup, setShowSellerPopup] = useState(false);

  useEffect(() => {
    const initializeApp = async () => {
      try {
        const botName = await getBotName(location);
        if (botName) {
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

  const handleSellerClick = (sellerId, sellerData) => {
    setSelectedSeller({ id: sellerId, ...sellerData });
    setShowSellerPopup(true);
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
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
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {/* Hero Section Skeleton */}
          <div className="text-center mb-16">
            <div className="w-32 h-32 bg-white/10 rounded-full mx-auto mb-8 animate-pulse"></div>
            <div className="h-16 w-96 bg-white/10 rounded mx-auto mb-6 animate-pulse"></div>
            <div className="h-6 w-64 bg-white/10 rounded mx-auto mb-8 animate-pulse"></div>
            <div className="flex justify-center space-x-4">
              <div className="h-12 w-32 bg-white/10 rounded animate-pulse"></div>
              <div className="h-12 w-32 bg-white/10 rounded animate-pulse"></div>
            </div>
          </div>

          {/* Stats Grid Skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10 shadow-2xl">
                <div className="h-12 w-12 bg-white/10 rounded-xl mx-auto mb-4 animate-pulse"></div>
                <div className="h-8 w-16 bg-white/10 rounded mx-auto mb-2 animate-pulse"></div>
                <div className="h-4 w-24 bg-white/10 rounded mx-auto animate-pulse"></div>
              </div>
            ))}
          </div>

          {/* Top Sellers Skeleton */}
          <div className="mb-16">
            <div className="h-8 w-48 bg-white/10 rounded mb-8 animate-pulse"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {[1, 2, 3].map(i => (
                <div key={i} className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10 shadow-2xl">
                  <div className="flex items-center space-x-4 mb-4">
                    <div className="w-12 h-12 bg-white/10 rounded-full animate-pulse"></div>
                    <div>
                      <div className="h-5 w-24 bg-white/10 rounded mb-2 animate-pulse"></div>
                      <div className="h-4 w-16 bg-white/10 rounded animate-pulse"></div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="h-4 w-32 bg-white/10 rounded animate-pulse"></div>
                    <div className="h-4 w-28 bg-white/10 rounded animate-pulse"></div>
                    <div className="h-4 w-20 bg-white/10 rounded animate-pulse"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </main>
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
          onClick={() => {
            setError(null);
            window.location.reload();
          }}
          className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white px-8 py-4 rounded-xl font-semibold transition-all transform hover:scale-105 shadow-lg"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <SEO 
        title={`${shopData?.guild?.name || "Premium Gaming Shop"} - Marketplace`}
        description={`Explore ${shopData?.guild?.name || "our premium gaming shop"} with ${shopData?.shop_stats?.total_listings || 0} listings from ${shopData?.shop_stats?.total_sellers || 0} verified sellers. Secure transactions and instant delivery.`}
        keywords="gaming accounts, minecraft accounts, skyblock profiles, gaming marketplace, verified sellers, secure transactions"
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
                className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white px-6 py-2 rounded-lg font-medium transition-all transform hover:scale-105 shadow-lg duration-300"
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
                className="bg-white/10 backdrop-blur-sm hover:bg-white/20 text-white px-6 py-2 rounded-lg font-medium transition-all border border-white/20 hover:scale-105 duration-300"
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

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          {shopData?.guild?.icon_url && (
            <img
              src={shopData.guild.icon_url}
              alt="Shop Icon"
              className="w-32 h-32 rounded-full mx-auto mb-8 border-4 border-purple-400 shadow-2xl ring-4 ring-purple-400/20"
            />
          )}
          <h1 className="text-7xl font-bold bg-gradient-to-r from-white via-purple-200 to-pink-200 bg-clip-text text-transparent mb-6 leading-tight">
            {shopData?.guild?.name || "Shop"}
          </h1>
          <p className="text-2xl text-purple-200 mb-8 font-light">
            {shopData?.guild?.member_count || 0} members strong
          </p>
        </div>

        {/* Stats Grid */}
        {shopData?.shop_stats && (
          <div className="grid grid-cols-2 gap-6 mb-16">
            <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 text-center border border-white/10 shadow-xl hover:bg-white/10 transition-all duration-150 group hover:shadow-2xl hover:-translate-y-1 animate-fade-in-up">
              <div className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent mb-3 group-hover:scale-110 transition-transform duration-150">
                {shopData.shop_stats.total_listings || 0}
              </div>
              <div className="text-sm text-purple-200 uppercase tracking-wider font-medium group-hover:text-purple-100 transition-colors duration-150">Items listed</div>
            </div>
            <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 text-center border border-white/10 shadow-xl hover:bg-white/10 transition-all duration-150 group hover:shadow-2xl hover:-translate-y-1 animate-fade-in-up" style={{animationDelay: '0.1s'}}>
              <div className="text-4xl font-bold bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent mb-3 group-hover:scale-110 transition-transform duration-150">
                {shopData.shop_stats.total_sellers || 0}
              </div>
              <div className="text-sm text-purple-200 uppercase tracking-wider font-medium group-hover:text-purple-100 transition-colors duration-150">Total Sellers</div>
            </div>
          </div>
        )}

        {/* Browse Listings Button */}
        <div className="text-center mb-16 animate-fade-in-up" style={{animationDelay: '0.3s'}}>
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
            className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-bold px-12 py-4 rounded-xl text-lg shadow-2xl hover:scale-105 transition-all duration-150 transform ring-4 ring-purple-500/20 hover:ring-purple-500/40 hover:shadow-purple-500/25 group relative overflow-hidden"
          >
            <span className="relative z-10 flex items-center justify-center space-x-2 group-hover:animate-bounce">
              <span>🛍️</span>
              <span>Explore All Listings</span>
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-pink-600 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-150 origin-left"></div>
          </button>
        </div>
      </main>

      {/* Sellers Section */}
      <div className="bg-black/20 backdrop-blur-lg py-20 border-t border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-5xl font-bold text-center mb-16 bg-gradient-to-r from-white via-purple-200 to-pink-200 bg-clip-text text-transparent">
            Our Sellers
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {shopData?.sellers && Object.entries(shopData.sellers).map(([sellerId, sellerData], index) => {
              if (!sellerData.discord_member) return null;
              return (
                <div
                  key={sellerId}
                  onClick={() => handleSellerClick(sellerId, sellerData)}
                  className="group bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10 hover:bg-white/15 transition-all duration-150 transform hover:scale-102 cursor-pointer shadow-xl hover:shadow-2xl hover:-translate-y-1 animate-fade-in-up"
                  style={{animationDelay: `${0.5 + (index * 0.1)}s`}}
                >
                  <div className="flex flex-col items-center">
                    <div className="relative mb-6 group-hover:animate-pulse">
                      <img
                        src={sellerData.discord_member.avatar_url}
                        alt={sellerData.discord_member.display_name}
                        className="w-20 h-20 rounded-full border-4 border-purple-400 shadow-lg ring-4 ring-purple-400/20 group-hover:ring-purple-400/60 transition-all duration-150 group-hover:scale-105 group-hover:shadow-2xl group-hover:shadow-purple-400/50"
                      />
                      <div className={`absolute -bottom-1 -right-1 w-6 h-6 rounded-full border-4 border-slate-900 shadow-lg transition-all duration-150 group-hover:scale-110 ${
                        sellerData.discord_member.is_online 
                          ? 'bg-green-400 animate-pulse ring-2 ring-green-400/50 group-hover:ring-green-400/80' 
                          : 'bg-gray-500'
                      }`}></div>
                    </div>
                    <h3 className="text-xl font-bold text-white mb-3 text-center group-hover:text-purple-200 transition-all duration-150 group-hover:scale-102">
                      {sellerData.discord_member.display_name}
                    </h3>
                    <div className="flex items-center space-x-2 mb-2 group-hover:animate-bounce">
                      <span className="text-yellow-400 group-hover:animate-spin transition-transform duration-1000">⭐</span>
                      <p className="text-purple-200 font-medium group-hover:text-purple-100 transition-colors duration-300">
                        {sellerData.vouches?.count || 0} vouches
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full transition-all duration-300 group-hover:scale-150 ${
                        sellerData.discord_member.is_online ? 'bg-green-400 group-hover:animate-ping' : 'bg-gray-500'
                      }`}></div>
                      <p className="text-sm text-purple-200 group-hover:text-purple-100 transition-colors duration-300">
                        {sellerData.discord_member.is_online ? 'Online Now' : 'Offline'}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Seller Popup */}
      {showSellerPopup && selectedSeller && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-slate-900/95 backdrop-blur-lg rounded-3xl p-10 max-w-md w-full max-h-[80vh] overflow-y-auto shadow-2xl border border-white/20 ring-1 ring-purple-500/20 animate-slide-up-fade transform hover:scale-102 transition-transform duration-150">
            <div className="flex justify-between items-start mb-8">
              <h3 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent animate-gradient-x">
                Seller Profile
              </h3>
              <button
                onClick={() => setShowSellerPopup(false)}
                className="text-gray-400 hover:text-red-400 text-3xl transition-all duration-150 transform hover:scale-110"
              >
                ×
              </button>
            </div>
            <div className="text-center mb-8 animate-fade-in-up" style={{animationDelay: '0.1s'}}>
              <div className="relative inline-block mb-6">
                <img
                  src={selectedSeller.discord_member?.avatar_url}
                  alt={selectedSeller.discord_member?.display_name}
                  className="w-32 h-32 rounded-full mx-auto border-4 border-purple-400 shadow-2xl ring-4 ring-purple-400/30 hover:ring-purple-400/60 transition-all duration-150 hover:scale-105 animate-float"
                />
                <div className={`absolute -bottom-2 -right-2 w-8 h-8 rounded-full border-4 border-slate-900 shadow-lg transition-all duration-150 hover:scale-110 ${
                  selectedSeller.discord_member?.is_online 
                    ? 'bg-green-400 animate-pulse ring-2 ring-green-400/50' 
                    : 'bg-gray-500'
                }`}></div>
              </div>
              <h4 className="text-2xl font-bold text-white mb-3 hover:text-purple-200 transition-colors duration-150">
                {selectedSeller.discord_member?.display_name}
              </h4>
              <p className="text-purple-200 text-lg mb-6 flex items-center justify-center space-x-2">
                <div className={`w-3 h-3 rounded-full transition-all duration-150 hover:scale-125 ${
                  selectedSeller.discord_member?.is_online ? 'bg-green-400 animate-pulse' : 'bg-gray-500'
                }`}></div>
                <span className="hover:text-purple-100 transition-colors duration-150">{selectedSeller.discord_member?.is_online ? 'Currently Online' : 'Offline'}</span>
              </p>
            </div>
            <div className="space-y-6">
              <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 hover:bg-white/10 transition-all duration-150 hover:shadow-lg hover:border-white/20 animate-fade-in-up" style={{animationDelay: '0.2s'}}>
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-yellow-400 text-xl hover:animate-spin transition-transform duration-1000">⭐</span>
                  <p className="font-bold text-white text-lg hover:text-purple-200 transition-colors duration-150">Vouches</p>
                </div>
                <p className="text-purple-200 text-lg hover:text-purple-100 transition-colors duration-150">
                  {selectedSeller.vouches?.count || 0} positive reviews
                </p>
              </div>
              {selectedSeller.payment_methods && (
                <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 hover:bg-white/10 transition-all duration-150 hover:shadow-lg hover:border-white/20 animate-fade-in-up" style={{animationDelay: '0.3s'}}>
                  <div className="flex items-center space-x-3 mb-3">
                    <span className="text-green-400 text-xl hover:animate-bounce">💳</span>
                    <p className="font-bold text-white text-lg hover:text-purple-200 transition-colors duration-150">Payment Methods</p>
                  </div>
                  <div className="text-purple-200">
                    {renderPaymentIcons(selectedSeller.payment_methods)}
                  </div>
                </div>
              )}
              {selectedSeller.discord_member?.joined_at && (
                <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 hover:bg-white/10 transition-all duration-150 hover:shadow-lg hover:border-white/20 animate-fade-in-up" style={{animationDelay: '0.4s'}}>
                  <div className="flex items-center space-x-3 mb-2">
                    <span className="text-blue-400 text-xl hover:animate-pulse">📅</span>
                    <p className="font-bold text-white text-lg hover:text-purple-200 transition-colors duration-150">Member Since</p>
                  </div>
                  <p className="text-purple-200 text-lg hover:text-purple-100 transition-colors duration-150">
                    {formatDate(selectedSeller.discord_member.joined_at)}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
};

export default Index;
