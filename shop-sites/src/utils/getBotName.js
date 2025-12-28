// Utility function to get bot name based on domain or URL path
export const getBotName = async (location) => {
  const hostname = window.location.hostname;
  
  // Check if this is a custom domain (not a noemt.dev domain)
  if (!hostname.includes('noemt.dev') && hostname !== 'localhost') {
    try {
      const response = await fetch('https://v2.noemt.dev/custom/bot/name', {
        headers: {
          'Host': hostname
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.name;
      }
    } catch (error) {
      console.error('Failed to fetch bot name for custom domain:', error);
    }
  }
  
  // Fall back to extracting from URL path for noemt.dev domains
  const pathParts = location.pathname.split('/').filter(part => part);
  return pathParts[0] || null;
};

export default getBotName;
