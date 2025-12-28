import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Footer from "../components/footer";
import SEO from "../components/SEO";
import getBotName from "../utils/getBotName";

const Vouches = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [shopData, setShopData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSeller, setSelectedSeller] = useState('all');
  const [filteredVouches, setFilteredVouches] = useState([]);

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

  useEffect(() => {
    if (shopData?.vouches) {
      filterVouches();
    }
  }, [shopData, selectedSeller]);

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

  const filterVouches = () => {
    if (!shopData?.vouches) return;
    
    let filtered = shopData.vouches;
    
    if (selectedSeller !== 'all') {
      filtered = filtered.filter(vouch => {
        const [userId, message, avatar, username] = vouch;
        const sellerFromMessage = getSellerFromMessage(message);
        return username.toLowerCase().includes(selectedSeller.toLowerCase()) ||
               message.toLowerCase().includes(selectedSeller.toLowerCase()) ||
               sellerFromMessage === selectedSeller;
      });
    }
    
    setFilteredVouches(filtered.reverse());
  };

  const formatTimestamp = (userId) => {
    // Discord snowflake timestamp extraction
    const timestamp = (parseInt(userId) >> 22) + 1420070400000;
    const date = new Date(timestamp);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const getTimestampFromMessage = (message, fallbackUserId) => {
    // Try to extract timestamp from Discord mentions in the message (these are the sellers)
    const userMentionMatches = message.match(/<@(\d+)>/g);
    if (userMentionMatches && userMentionMatches.length > 0) {
      // Use the first mention found in the message (this is the seller being vouched for)
      const mentionedUserId = userMentionMatches[0].match(/<@(\d+)>/)[1];
      return formatTimestamp(mentionedUserId);
    }
    
    // Fall back to the vouch author's timestamp if no mentions found
    return formatTimestamp(fallbackUserId);
  };

  const getSellers = () => {
    if (!shopData?.sellers) return [];
    console.log('Raw shopData.sellers:', shopData.sellers); // Debug log
    const sellers = Object.entries(shopData.sellers)
      .filter(([sellerId, seller]) => {
        console.log('Checking seller:', seller, 'with ID:', sellerId); // Debug log
        return seller.discord_member;
      })
      .map(([sellerId, seller]) => ({
        name: seller.discord_member.display_name,
        id: sellerId // Use the key from the sellers object as the ID
      }));
    console.log('Processed sellers:', sellers); // Debug log
    return sellers;
  };

  const isSellerMentioned = (message) => {
    const sellers = getSellers();
    
    // Check for Discord user mentions (<@userId>)
    const userMentionMatches = message.match(/<@(\d+)>/g);
    if (userMentionMatches) {
      const mentionedIds = userMentionMatches.map(match => match.match(/<@(\d+)>/)[1]);
      const sellerMentioned = sellers.some(seller => mentionedIds.includes(seller.id));
      if (sellerMentioned) return true;
    }
    
    // Check for seller names in message
    return sellers.some(seller => 
      message.toLowerCase().includes(seller.name.toLowerCase())
    );
  };

  const getSellerFromMessage = (message) => {
    const sellers = getSellers();
    
    // Check for Discord user mentions (<@userId>)
    const userMentionMatches = message.match(/<@(\d+)>/g);
    if (userMentionMatches) {
      const mentionedIds = userMentionMatches.map(match => match.match(/<@(\d+)>/)[1]);
      const mentionedSeller = sellers.find(seller => mentionedIds.includes(seller.id));
      if (mentionedSeller) return mentionedSeller.name;
    }
    
    // Check for seller names in message
    const namedSeller = sellers.find(seller => 
      message.toLowerCase().includes(seller.name.toLowerCase())
    );
    
    return namedSeller ? namedSeller.name : null;
  };

  const highlightSellers = (message) => {
    let highlightedMessage = message;
    const sellers = getSellers();
    
    console.log('Sellers:', sellers); // Debug log
    console.log('Message:', message); // Debug log
    
    // Handle Discord user mentions (<@userId>) first - only highlight if they're sellers
    const userMentionMatches = message.match(/<@(\d+)>/g);
    if (userMentionMatches) {
      console.log('Found mentions:', userMentionMatches); // Debug log
      userMentionMatches.forEach(mention => {
        const userId = mention.match(/<@(\d+)>/)[1];
        console.log('Checking userId:', userId, 'type:', typeof userId); // Debug log
        console.log('Seller IDs:', sellers.map(s => `ID: "${s.id}" (${typeof s.id}) Name: "${s.name}"`)); // Debug log
        const seller = sellers.find(s => String(s.id) === String(userId));
        console.log('Found seller:', seller); // Debug log
        if (seller) {
          // Only replace if it's a known seller
          console.log('Replacing mention with seller name:', seller.name); // Debug log
          highlightedMessage = highlightedMessage.replace(
            mention,
            `<span class="bg-purple-500/30 text-purple-200 px-2 py-1 rounded-lg font-semibold border border-purple-400/50">@${seller.name}</span>`
          );
        }
        // If not a seller, leave the original <@userId> format unchanged
      });
    }
    
    // Handle seller names in text (but avoid double-highlighting already processed mentions)
    sellers.forEach(seller => {
      const regex = new RegExp(`\\b(${seller.name})\\b`, 'gi');
      // Only replace if it's not already in a span tag
      highlightedMessage = highlightedMessage.replace(regex, (match, p1, offset, string) => {
        // Check if this match is already inside a span tag
        const beforeMatch = string.substring(0, offset);
        const openSpans = (beforeMatch.match(/<span/g) || []).length;
        const closeSpans = (beforeMatch.match(/<\/span>/g) || []).length;
        
        if (openSpans > closeSpans) {
          // We're inside a span, don't replace
          return match;
        }
        
        return `<span class="bg-purple-500/30 text-purple-200 px-2 py-1 rounded-lg font-semibold border border-purple-400/50">${p1}</span>`;
      });
    });

    // Handle generic Discord mentions (@username) - but not if already highlighted
    highlightedMessage = highlightedMessage.replace(
      /@(\w+)/g, 
      (match, p1, offset, string) => {
        const beforeMatch = string.substring(0, offset);
        const openSpans = (beforeMatch.match(/<span/g) || []).length;
        const closeSpans = (beforeMatch.match(/<\/span>/g) || []).length;
        
        if (openSpans > closeSpans) {
          return match; // Already inside a span
        }
        
        return `<span class="bg-blue-500/20 text-blue-300 px-1 rounded">@${p1}</span>`;
      }
    );

    console.log('Final highlighted message:', highlightedMessage); // Debug log
    return highlightedMessage;
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
                <div className="h-8 w-20 bg-white/10 rounded animate-pulse"></div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content Skeleton */}
        <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center mb-12">
            <div className="h-12 w-64 bg-white/10 rounded mx-auto mb-4 animate-pulse"></div>
            <div className="h-6 w-48 bg-white/10 rounded mx-auto animate-pulse"></div>
          </div>

          {/* Filter Skeleton */}
          <div className="mb-8">
            <div className="h-10 w-64 bg-white/10 rounded animate-pulse"></div>
          </div>

          {/* Vouches Skeleton */}
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-white/10 rounded-full animate-pulse"></div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <div className="h-5 w-24 bg-white/10 rounded animate-pulse"></div>
                      <div className="h-4 w-32 bg-white/10 rounded animate-pulse"></div>
                    </div>
                    <div className="h-16 w-full bg-white/10 rounded animate-pulse"></div>
                  </div>
                </div>
              </div>
            ))}
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
          onClick={() => window.location.reload()}
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
        title={`Customer Reviews - ${shopData?.guild?.name || "Gaming Shop"}`}
        description={`Read ${filteredVouches.length} authentic customer reviews and testimonials. See what customers say about our gaming accounts and services.`}
        keywords="customer reviews, testimonials, vouches, gaming accounts reviews, seller feedback, trusted marketplace"
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
                className="bg-white/10 backdrop-blur-sm hover:bg-white/20 text-white px-6 py-2 rounded-lg font-medium transition-all border border-white/20 hover:scale-102 duration-150"
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
                className="bg-white/10 backdrop-blur-sm hover:bg-white/20 text-white px-6 py-2 rounded-lg font-medium transition-all border border-white/20 hover:scale-102 duration-150"
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
                className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white px-6 py-2 rounded-lg font-medium transition-all transform hover:scale-102 shadow-lg duration-150"
              >
                Vouches
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-12 animate-fade-in-up">
          <h1 className="text-6xl font-bold bg-gradient-to-r from-white via-purple-200 to-pink-200 bg-clip-text text-transparent mb-4 leading-tight">
            Vouches
          </h1>
          <p className="text-xl text-purple-200 font-light">
            See what our customers are saying • {filteredVouches.length} reviews
          </p>
        </div>

        {/* Filter Section */}
        <div className="mb-8 animate-fade-in-up" style={{animationDelay: '0.1s'}}>
          <div className="flex flex-wrap items-center gap-4">
            <label className="text-purple-200 font-medium">Filter by seller:</label>
            <div className="relative">
              <select
                value={selectedSeller}
                onChange={(e) => setSelectedSeller(e.target.value)}
                className="bg-gray-800/90 border border-gray-700/50 rounded-xl px-4 py-3 pr-10 
                  text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50
                  transition-all duration-150 cursor-pointer backdrop-blur-sm
                  hover:bg-gray-750/90 hover:border-gray-600/50 appearance-none"
              >
                <option value="all" className="bg-gray-800 text-white py-2">All Sellers</option>
                {getSellers().map(seller => (
                  <option 
                    key={seller.id || seller.name} 
                    value={seller.name} 
                    className="bg-gray-800 text-white py-2 hover:bg-gray-700"
                  >
                    {seller.name}
                  </option>
                ))}
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
            <div className="text-sm text-purple-300">
              Showing {filteredVouches.length} of {shopData?.vouches?.length || 0} vouches
            </div>
          </div>
        </div>

        {/* Vouches List */}
        <div className="space-y-4">
          {filteredVouches.length > 0 ? (
            filteredVouches.map((vouch, index) => {
              const [userId, message, avatarUrl, username] = vouch;
              return (
                <div
                  key={`${userId}-${index}`}
                  className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10 hover:bg-white/10 transition-all duration-150 hover:shadow-lg hover:border-white/20 animate-fade-in-up hover:scale-[1.01] group"
                  style={{animationDelay: `${0.1 + (index * 0.02)}s`}}
                >
                  {/* Discord Message Format */}
                  <div className="flex items-start space-x-4">
                    {/* Avatar */}
                    <div className="relative">
                      <img
                        src={avatarUrl}
                        alt={username}
                        className="w-12 h-12 rounded-full border-2 border-purple-400/50 hover:border-purple-400 transition-all duration-150 group-hover:scale-105"
                        onError={(e) => {
                          e.target.src = 'https://cdn.discordapp.com/embed/avatars/0.png';
                        }}
                      />
                      <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-slate-900 animate-pulse"></div>
                    </div>
                    
                    {/* Message Content */}
                    <div className="flex-1 min-w-0">
                      {/* Username and Timestamp */}
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="font-bold text-white hover:text-purple-200 transition-colors duration-150 group-hover:scale-102">
                          {username}
                        </h3>
                        <span className="text-xs text-gray-400 hover:text-gray-300 transition-colors duration-150">
                          {getTimestampFromMessage(message, userId)}
                        </span>
                        {getSellers().some(seller => isSellerMentioned(message, seller)) && (
                          <span className="bg-green-500/20 text-green-300 text-xs px-2 py-1 rounded-full animate-pulse">
                            ⭐ Vouched for a seller
                          </span>
                        )}
                      </div>
                      
                      {/* Message Text */}
                      <div 
                        className="text-purple-100 leading-relaxed hover:text-white transition-colors duration-150"
                        dangerouslySetInnerHTML={{ 
                          __html: highlightSellers(message) 
                        }}
                      />
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-center py-20 animate-fade-in-up">
              <div className="text-6xl mb-6 animate-bounce">💬</div>
              <h3 className="text-2xl font-bold text-white mb-4">No vouches found</h3>
              <p className="text-purple-200">
                {selectedSeller === 'all' 
                  ? "No customer reviews available yet." 
                  : `No reviews found for "${selectedSeller}".`
                }
              </p>
              {selectedSeller !== 'all' && (
                <button
                  onClick={() => setSelectedSeller('all')}
                  className="mt-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white px-6 py-2 rounded-lg font-medium transition-all transform hover:scale-102 shadow-lg duration-150"
                >
                  View All Vouches
                </button>
              )}
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Vouches;
