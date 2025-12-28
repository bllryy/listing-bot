// App.js
import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Lazy load the components for better performance
const Index = React.lazy(() => import('./pages/index'));
const Listings = React.lazy(() => import('./pages/listings'));
const Auth = React.lazy(() => import('./pages/auth'));
const Config = React.lazy(() => import('./pages/config'));

function App() {
  return (
    <Router>
      <Suspense fallback={
        <div className="flex flex-col min-h-screen items-center justify-center bg-[#070707] text-white">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
          <p>Loading dashboard...</p>
        </div>
      }>
        <Routes>
          <Route path="/:botName/config" element={<Config />} />
          <Route path="/:botName/auth" element={<Auth />} />
          <Route path="/:botName/listings" element={<Listings />} />
          <Route path="/:botName" element={<Index />} />
        </Routes>
      </Suspense>
    </Router>
  );
}

export default App;