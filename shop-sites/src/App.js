// App.js
import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

const Index = React.lazy(() => import('./pages/index'));
const Listings = React.lazy(() => import('./pages/listings'));
const Vouches = React.lazy(() => import('./pages/vouches'));

function App() {
  return (
    <Router>
      <Suspense fallback={
        <div className="flex flex-col min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-purple-400 mb-6"></div>
          <p className="text-purple-200 text-lg font-medium">Loading...</p>
        </div>
      }>
        <Routes>
          {/* Custom domain routes (no bot name in path) */}
          <Route path="/listings" element={<Listings />} />
          <Route path="/vouches" element={<Vouches />} />
          <Route path="/" element={<Index />} />
          
          {/* Path-based routes for noemt.dev domains */}
          <Route path="/:botName/listings" element={<Listings />} />
          <Route path="/:botName/vouches" element={<Vouches />} />
          <Route path="/:botName" element={<Index />} />
        </Routes>
      </Suspense>
    </Router>
  );
}

export default App;