const express = require('express');
const axios = require('axios');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

const clientId = process.env.FITBIT_CLIENT_ID;
const clientSecret = process.env.FITBIT_CLIENT_SECRET;
const redirectUri = process.env.FITBIT_REDIRECT_URI;

app.use(express.static(path.join(__dirname, 'public')));

app.get('/auth', (req, res) => {
  const url = `https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=${clientId}&redirect_uri=${redirectUri}&scope=nutrition&expires_in=604800`;
  res.redirect(url);
});

app.get('/callback', async (req, res) => {
  const code = req.query.code;
  const tokenUrl = 'https://api.fitbit.com/oauth2/token';
  const authHeader = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');

  try {
    const response = await axios.post(tokenUrl, null, {
      params: {
        client_id: clientId,
        grant_type: 'authorization_code',
        redirect_uri: redirectUri,
        code: code
      },
      headers: {
        Authorization: `Basic ${authHeader}`,
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });

    const accessToken = response.data.access_token;
    const refreshToken = response.data.refresh_token;
    res.redirect(`/food-count?token=${accessToken}&refresh=${refreshToken}`);
  } catch (error) {
    res.send('Error getting token');
  }
});

app.get('/food-count', async (req, res) => {
  let token = req.query.token;
  let refresh = req.query.refresh;
  const userId = '-';
  const startDate = new Date();
  startDate.setMonth(8); // September
  startDate.setDate(1);
  startDate.setFullYear(startDate.getMonth() < 8 ? startDate.getFullYear() - 1 : startDate.getFullYear());
  const endDate = new Date(startDate);
  endDate.setFullYear(startDate.getFullYear() + 1);

  let hotdogs = 0, burgers = 0, apples = 0;

  async function refreshToken(oldRefreshToken) {
    const tokenUrl = 'https://api.fitbit.com/oauth2/token';
    const authHeader = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');
    try {
      const response = await axios.post(tokenUrl, null, {
        params: {
          grant_type: 'refresh_token',
          refresh_token: oldRefreshToken
        },
        headers: {
          Authorization: `Basic ${authHeader}`,
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      return response.data.access_token;
    } catch (error) {
      return null;
    }
  }

  async function fetchLogs(dateStr) {
    try {
      const response = await axios.get(`https://api.fitbit.com/1/user/${userId}/foods/log/date/${dateStr}.json`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      const foods = response.data.foods;
      foods.forEach(food => {
        const name = food.loggedFood.name;
        if (name === 'Regulation Hotdog') hotdogs++;
        if (name === 'Regulation Burger') burgers++;
        if (name === 'Regulation Apple') apples++;
      });
    } catch (error) {
      if (error.response && error.response.status === 401) {
        const newToken = await refreshToken(refresh);
        if (newToken) {
          token = newToken;
          await fetchLogs(dateStr);
        }
      }
    }
  }

  const currentDate = new Date(startDate);
  while (currentDate < endDate) {
    const dateStr = currentDate.toISOString().split('T')[0];
    await fetchLogs(dateStr);
    currentDate.setDate(currentDate.getDate() + 1);
  }

  res.json({ hotdogs, burgers, apples });
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
