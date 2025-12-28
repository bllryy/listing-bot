// App.js
import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Lazy load the components for better performance
const SellerDashboard = React.lazy(() => import('./pages/SellerDashboard'));
const SellerAuth = React.lazy(() => import('./pages/SellerAuth'));
const SellerListings = React.lazy(() => import('./pages/SellerListings'));
const SellerConfiguration = React.lazy(() => import('./pages/SellerConfiguration'));

function App() {
  return (
    <Router>
      <Suspense fallback={
        <div className="flex flex-col min-h-screen items-center justify-center bg-[#070707] text-white">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
          <p>Loading seller dashboard...</p>
        </div>
      }>
        <Routes>
          <Route path="/auth" element={<SellerAuth />} />
          <Route path="/listings" element={<SellerListings />} />
          <Route path="/configuration" element={<SellerConfiguration />} />
          <Route path="/" element={<SellerDashboard />} />
        </Routes>
      </Suspense>
    </Router>
  );
}

export default App;