const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const STATE_FILE = path.join(__dirname, 'state.json');

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

function readState() {
  try {
    return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
  } catch {
    const initial = [
      { id: 1, title: 'INERTIA', occupied: false },
      { id: 2, title: 'ORIGINAL', occupied: false },
      { id: 3, title: '93 tpm', occupied: false },
      { id: 4, title: 'TOO MANY AND ONE', occupied: false }
    ];
    fs.writeFileSync(STATE_FILE, JSON.stringify(initial, null, 2));
    return initial;
  }
}

function writeState(state) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

const clients = new Set();

function broadcast(state) {
  const data = JSON.stringify(state);
  for (const client of clients) {
    client.write(`data: ${data}\n\n`);
  }
}

app.get('/api/state', (req, res) => {
  res.json(readState());
});

app.get('/api/events', (req, res) => {
  res.set({
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive'
  });
  res.flushHeaders();
  res.write(`data: ${JSON.stringify(readState())}\n\n`);
  clients.add(res);
  req.on('close', () => clients.delete(res));
});

app.put('/api/state/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const state = readState();
  const item = state.find(i => i.id === id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  item.occupied = !item.occupied;
  writeState(state);
  broadcast(state);
  res.json(state);
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
