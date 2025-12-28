import { useEffect } from 'react';

const SEO = ({ 
  title = "noemt.dev - Premium Gaming Accounts & Services Marketplace",
  description = "Premium gaming accounts marketplace - Buy and sell high-quality gaming accounts, profiles, and services with secure transactions and verified sellers.",
  keywords = "gaming accounts, minecraft accounts, skyblock profiles, gaming marketplace, buy accounts, sell accounts, discord shop, gaming services",
  image = "/assets/icon.webp",
  url = "https://noemt.dev",
  type = "website"
}) => {
  useEffect(() => {
    // Update document title
    const fullTitle = title.includes('noemt.dev') ? title : `${title} | noemt.dev`;
    document.title = fullTitle;

    // Update meta description
    let metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute('content', description);
    }

    // Update meta keywords
    let metaKeywords = document.querySelector('meta[name="keywords"]');
    if (metaKeywords) {
      metaKeywords.setAttribute('content', keywords);
    }

    // Update Open Graph tags
    let ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle) {
      ogTitle.setAttribute('content', fullTitle);
    }

    let ogDescription = document.querySelector('meta[property="og:description"]');
    if (ogDescription) {
      ogDescription.setAttribute('content', description);
    }

    let ogImage = document.querySelector('meta[property="og:image"]');
    if (ogImage) {
      const fullImage = image.startsWith('http') ? image : `https://noemt.dev${image}`;
      ogImage.setAttribute('content', fullImage);
    }

    let ogUrl = document.querySelector('meta[property="og:url"]');
    if (ogUrl) {
      const fullUrl = url.startsWith('http') ? url : `https://noemt.dev${url}`;
      ogUrl.setAttribute('content', fullUrl);
    }

    // Update Twitter Card tags
    let twitterTitle = document.querySelector('meta[name="twitter:title"]');
    if (twitterTitle) {
      twitterTitle.setAttribute('content', fullTitle);
    }

    let twitterDescription = document.querySelector('meta[name="twitter:description"]');
    if (twitterDescription) {
      twitterDescription.setAttribute('content', description);
    }

    let twitterImage = document.querySelector('meta[name="twitter:image"]');
    if (twitterImage) {
      const fullImage = image.startsWith('http') ? image : `https://noemt.dev${image}`;
      twitterImage.setAttribute('content', fullImage);
    }

    // Add structured data
    let existingScript = document.querySelector('script[type="application/ld+json"]');
    if (existingScript) {
      existingScript.remove();
    }

    const structuredData = {
      "@context": "https://schema.org",
      "@type": "Organization",
      "name": "noemt.dev",
      "url": "https://noemt.dev",
      "logo": "https://noemt.dev/assets/icon.webp",
      "description": description,
      "sameAs": [
        "https://discord.gg/noemt"
      ]
    };

    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.textContent = JSON.stringify(structuredData);
    document.head.appendChild(script);

    // Cleanup function to remove script when component unmounts
    return () => {
      const scriptToRemove = document.querySelector('script[type="application/ld+json"]');
      if (scriptToRemove) {
        scriptToRemove.remove();
      }
    };
  }, [title, description, keywords, image, url, type]);

  return null; // This component doesn't render anything
};

export default SEO;
