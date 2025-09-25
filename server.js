const express = require('express');
const axios = require('axios');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

const clientId = process.env.FITBIT_CLIENT_ID;
const clientSecret = process.env.FITBIT_CLIENT_SECRET;
let accessToken = process.env.FITBIT_ACCESS_TOKEN;
let refreshToken = process.env.FITBIT_REFRESH_TOKEN;

app.use('/public', express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
  res.redirect('/public/iframe.html');
});

app.get('/food-count', async (req, res) => {
  const today = new Date();
  const start = new Date(today.getFullYear() - (today.getMonth() < 8 ? 1 : 0), 8, 1); // Sept 1st of current or previous year
  const end = new Date(start.getFullYear() + 1, 8, 1); // Sept 1st next year

  let hotdogs = 0, burgers = 0, apples = 0;

  const authHeader = `Bearer ${accessToken}`;

  for (let d = new Date(start); d < end; d.setDate(d.getDate() + 1)) {
    const dateStr = d.toISOString().split('T')[0];
    try {
      const response = await axios.get(`https://api.fitbit.com/1/user/-/foods/log/date/${dateStr}.json`, {
        headers: { Authorization: authHeader }
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
        // Token expired, refresh it
        try {
          const tokenResponse = await axios.post('https://api.fitbit.com/oauth2/token', null, {
            params: {
              grant_type: 'refresh_token',
              refresh_token: refreshToken,
              client_id: clientId
            },
            headers: {
              Authorization: 'Basic ' + Buffer.from(`${clientId}:${clientSecret}`).toString('base64'),
              'Content-Type': 'application/x-www-form-urlencoded'
            }
          });
          accessToken = tokenResponse.data.access_token;
          refreshToken = tokenResponse.data.refresh_token;
        } catch (refreshError) {
          return res.status(500).json({ error: 'Failed to refresh token' });
        }
      } else {
        console.error(`Error fetching data for ${dateStr}:`, error.message);
      }
    }
  }

  res.json({ hotdogs, burgers, apples });
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
