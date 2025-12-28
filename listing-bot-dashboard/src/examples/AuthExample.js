// Example usage of the new authentication system
// This file demonstrates how to use the authentication functions

import React, { useState, useEffect } from 'react';

const ExampleDashboard = () => {
  const [user, setUser] = useState(null);
  const [botData, setBotData] = useState(null);
  const [authorizedBots, setAuthorizedBots] = useState(null);
  const [loading, setLoading] = useState(false);

  // Check if user is authenticated
  const checkAuth = async () => {
    try {
      const response = await fetch('https://v2.noemt.dev/auth/me', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        return true;
      }
      return false;
    } catch (err) {
      console.error("Auth check failed:", err);
      return false;
    }
  };

  // Fetch bot data
  const fetchBotData = async (botName) => {
    try {
      setLoading(true);
      const response = await fetch(`https://v2.noemt.dev/dash/${botName}`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setBotData(data);
      } else {
        console.error('Failed to fetch bot data');
      }
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch authorized bots
  const fetchAuthorizedBots = async (botName) => {
    try {
      const response = await fetch(`https://v2.noemt.dev/api/bot/${botName}/auth/bots`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setAuthorizedBots(data);
        return data;
      }
    } catch (err) {
      console.error('Error fetching authorized bots:', err);
    }
    return null;
  };

  // Fetch user information
  const fetchUsersInfo = async (botName, userIds) => {
    try {
      const response = await fetch(`https://v2.noemt.dev/api/bot/${botName}/users/info`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(userIds)
      });
      
      if (response.ok) {
        return await response.json();
      }
    } catch (err) {
      console.error('Error fetching users info:', err);
    }
    return null;
  };

  // Example usage in component
  useEffect(() => {
    const initializeAuth = async () => {
      const isAuthenticated = await checkAuth();
      
      if (isAuthenticated) {
        // Extract bot name from URL path - using /{bot_name} pattern
        const pathParts = window.location.pathname.split('/').filter(part => part);
        const botName = pathParts[0]; // First path segment is the bot name
        
        if (botName && botName !== 'dashboard') {
          // Fetch bot dashboard data
          await fetchBotData(botName);
          
          // Fetch authorized bots
          await fetchAuthorizedBots(botName);
          
          // Example: Fetch info for specific users
          const userIds = ['123456789', '987654321'];
          const usersInfo = await fetchUsersInfo(botName, userIds);
          console.log('Users info:', usersInfo);
        } else {
          console.log('No bot name found in URL path');
        }
      } else {
        // Redirect to login
        const currentUrl = encodeURIComponent(window.location.href);
        window.location.href = `https://v2.noemt.dev/auth/discord/login?redirect_url=${currentUrl}`;
      }
    };

    initializeAuth();
  }, []);

  // Login handler
  const handleLogin = () => {
    const currentUrl = encodeURIComponent(window.location.href);
    window.location.href = `https://v2.noemt.dev/auth/discord/login?redirect_url=${currentUrl}`;
  };

  // Logout handler
  const handleLogout = async () => {
    try {
      await fetch('https://v2.noemt.dev/auth/logout', {
        credentials: 'include'
      });
      setUser(null);
      setBotData(null);
      setAuthorizedBots(null);
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  if (!user) {
    return (
      <div>
        <h1>Please Login</h1>
        <button onClick={handleLogin}>Login with Discord</button>
      </div>
    );
  }

  return (
    <div>
      <h1>Welcome, {user.user_info?.global_name || user.user_info?.username}!</h1>
      <button onClick={handleLogout}>Logout</button>
      
      {loading && <p>Loading...</p>}
      
      {botData && (
        <div>
          <h2>Bot Data</h2>
          <pre>{JSON.stringify(botData, null, 2)}</pre>
        </div>
      )}
      
      {authorizedBots && (
        <div>
          <h2>Authorized Bots</h2>
          <pre>{JSON.stringify(authorizedBots, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default ExampleDashboard;
