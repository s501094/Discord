const express = require('express');
const app = express();

app.get('/auth', (req, res) => {
    res.send("Authorization successful! You can close this window.");
});

app.listen(3000, () => console.log('Server running on http://localhost:3000'));

