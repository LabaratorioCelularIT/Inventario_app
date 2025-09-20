import React from 'react';
import { Routes, Route } from 'react-router-dom';
import './styles/App.css';

// TODO: Import pages as they are created
// import Dashboard from './pages/Dashboard';
// import Inventory from './pages/Inventory';
// import Cash from './pages/Cash';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Inventario App - New Architecture</h1>
        <p>Modern Flask API + React Frontend</p>
      </header>
      
      <main>
        <Routes>
          <Route path="/" element={<div>Dashboard - Coming Soon</div>} />
          <Route path="/inventory" element={<div>Inventory - Coming Soon</div>} />
          <Route path="/cash" element={<div>Cash Register - Coming Soon</div>} />
        </Routes>
      </main>
    </div>
  );
}

export default App;