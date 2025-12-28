# Authentication System Update

This dashboard has been updated to work with the new Discord OAuth2 authentication system.

## How it works

1. **Authentication Required**: Users must login with Discord to access any bot dashboard
2. **Session-based**: Uses secure session cookies for authentication
3. **Bot Ownership Verification**: Users can only access bots they own on Discord
4. **Automatic Redirects**: Users are automatically redirected after login

## Usage

### Accessing a Bot Dashboard

To access a specific bot's dashboard, navigate directly to:

```
https://yourdomain.com/your-bot-name
```

The bot name is now passed as the first path segment in the URL.

### Authentication Flow

1. User visits the dashboard
2. If not authenticated, they see a login prompt
3. User clicks "Login with Discord"
4. Discord OAuth2 flow begins
5. User authorizes the application
6. User is redirected back to the dashboard
7. Dashboard fetches bot data for the authenticated user

### API Endpoints Used

- `GET /auth/me` - Check current authentication status
- `GET /auth/discord/login` - Start Discord OAuth2 flow
- `GET /auth/logout` - Logout and clear session
- `GET /dash/{bot_name}` - Get bot dashboard data (requires authentication)
- `GET /api/bot/{bot_name}/auth/bots` - Get authorized bots (requires authentication)
- `GET /api/bot/{bot_name}/auth/users` - Get authorized users (requires authentication)
- `POST /api/bot/{bot_name}/users/info` - Get detailed user info (requires authentication)

### Security Features

- **CORS enabled** with credentials
- **Session-based authentication** with automatic cleanup
- **Bot ownership verification** on every request
- **Secure cookie handling**
- **Automatic session expiration** (24 hours)

## Development Notes

### Environment Variables Required

The API server requires these environment variables:

```env
API_KEY=your-api-key-here
```

### Discord OAuth2 Configuration

The following Discord OAuth2 settings are configured in the API:

- **Client ID**: `1394403872809816125`
- **Redirect URI**: `https://v2.noemt.dev/auth/discord/callback`
- **Scopes**: `identify`

### Frontend Configuration

The React frontend automatically:

- Checks authentication status on page load
- Handles login/logout flows
- Manages session state
- Provides proper error handling
- Shows user information in the header

## Error Handling

The dashboard handles various error states:

- **401 Unauthorized**: User needs to login
- **403 Forbidden**: User doesn't own the requested bot
- **404 Not Found**: Bot doesn't exist
- **503 Service Unavailable**: Bot is not responding

## Additional Features

- **Dark/Light mode toggle**
- **User profile display** in header
- **Bot statistics dashboard**
- **Real-time status indicators**
- **Quick action buttons**
- **Responsive design**

## API Functions Available

The dashboard includes helper functions for all authenticated API endpoints:

```javascript
// Check authentication
await checkAuth()

// Fetch bot dashboard data
await fetchBotData(botName)

// Get authorized bots
await fetchAuthorizedBots(botName)

// Get authorized users
await fetchAuthorizedUsers(botName)

// Get detailed user information
await fetchUsersInfo(botName, userIds)

// Get bot statistics
await fetchBotStats(botName)
```

All functions automatically include credentials and handle authentication errors.
