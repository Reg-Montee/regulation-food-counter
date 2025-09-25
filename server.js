const express = require('express');
const axios = require('axios');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use('/public', express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
  res.redirect('/public/iframe.html');
});

app.get('/auth', (req, res) => {
  const url = `https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=${process.env.FITBIT_CLIENT_ID}&redirect_uri=${process.env.FITBIT_REDIRECT_URI}&scope=nutrition&expires_in=604800`;
  res.redirect(url);
});

app.get('/callback', async (req, res) => {
  const code = req.query.code;
  const tokenUrl = 'https://api.fitbit.com/oauth2/token';
  const authHeader = Buffer.from(`${process.env.FITBIT_CLIENT_ID}:${process.env.FITBIT_CLIENT_SECRET}`).toString('base64');

  try {
    const response = await axios.post(tokenUrl, null, {
      params: {
        client_id: process.env.FITBIT_CLIENT_ID,
        grant_type: 'authorization_code',
        redirect_uri: process.env.FITBIT_REDIRECT_URI,
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
  const token = req.query.token;
  const refresh = req.query.refresh;
  const today = new Date();
  const startDate = new Date(today.getFullYear() - 1, 8, 1); // Sept 1 last year
  const endDate = new Date(today.getFullYear(), 7, 31); // Aug 31 this year

  let hotdogs = 0, burgers = 0, apples = 0;

  try {
    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
      const dateStr = d.toISOString().split('T')[0];
      const response = await axios.get(`https://api.fitbit.com/1/user/-/foods/log/date/${dateStr}.json`, {
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
    }

    res.json({ hotdogs, burgers, apples });
  } catch (error) {
    res.send('Error fetching food logs');
  }
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));