const express = require('express');
const axios = require('axios');
const fs = require('fs');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Fitbit API credentials from environment variables
const clientId = process.env.FITBIT_CLIENT_ID;
const clientSecret = process.env.FITBIT_CLIENT_SECRET;
const redirectUri = process.env.FITBIT_REDIRECT_URI;

// In-memory token store (can be replaced with persistent storage)
let tokenStore = {
  access_token: null,
  refresh_token: null,
  expires_at: null
};

// Serve static files including iframe.html
app.use('/public', express.static(__dirname + '/public'));

app.get('/auth', (req, res) => {
  const url = \`https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=\${clientId}&redirect_uri=\${redirectUri}&scope=nutrition&expires_in=604800\`;
  res.redirect(url);
});

app.get('/callback', async (req, res) => {
  const code = req.query.code;
  const tokenUrl = 'https://api.fitbit.com/oauth2/token';
  const authHeader = Buffer.from(\`\${clientId}:\${clientSecret}\`).toString('base64');

  try {
    const response = await axios.post(tokenUrl, null, {
      params: {
        client_id: clientId,
        grant_type: 'authorization_code',
        redirect_uri: redirectUri,
        code: code
      },
      headers: {
        Authorization: \`Basic \${authHeader}\`,
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });

    const data = response.data;
    tokenStore.access_token = data.access_token;
    tokenStore.refresh_token = data.refresh_token;
    tokenStore.expires_at = Date.now() + data.expires_in * 1000;

    res.redirect('/public/iframe.html');
  } catch (error) {
    res.send('Error getting token');
  }
});

async function refreshAccessToken() {
  const tokenUrl = 'https://api.fitbit.com/oauth2/token';
  const authHeader = Buffer.from(\`\${clientId}:\${clientSecret}\`).toString('base64');

  try {
    const response = await axios.post(tokenUrl, null, {
      params: {
        grant_type: 'refresh_token',
        refresh_token: tokenStore.refresh_token
      },
      headers: {
        Authorization: \`Basic \${authHeader}\`,
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });

    const data = response.data;
    tokenStore.access_token = data.access_token;
    tokenStore.refresh_token = data.refresh_token;
    tokenStore.expires_at = Date.now() + data.expires_in * 1000;
  } catch (error) {
    console.error('Error refreshing token:', error.response?.data || error.message);
  }
}

app.get('/food-count', async (req, res) => {
  if (!tokenStore.access_token) {
    return res.status(401).json({ error: 'Not authenticated' });
  }

  if (Date.now() >= tokenStore.expires_at) {
    await refreshAccessToken();
  }

  const today = new Date().toISOString().split('T')[0];

  try {
    const response = await axios.get(\`https://api.fitbit.com/1/user/-/foods/log/date/\${today}.json\`, {
      headers: {
        Authorization: \`Bearer \${tokenStore.access_token}\`
      }
    });

    const foods = response.data.foods;
    let hotdogs = 0, burgers = 0, apples = 0;

    foods.forEach(food => {
      const name = food.loggedFood.name;
      if (name === 'Regulation Hotdog') hotdogs++;
      if (name === 'Regulation Burger') burgers++;
      if (name === 'Regulation Apple') apples++;
    });

    res.json({ hotdogs, burgers, apples });
  } catch (error) {
    res.send('Error fetching food logs');
  }
});

app.listen(PORT, () => console.log(\`Server running on port \${PORT}\`));
