async function initializeAuth(botName) {
  try {
    const response = await fetch(`https://v2.noemt.dev/api/${botName}/initialize/website/ticket/open`);
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Failed to initialize auth:', error);
    return null;
  }
}
export default initializeAuth;