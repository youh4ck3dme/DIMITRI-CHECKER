import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import HomePageNew from './pages/HomePageNew';
import TermsOfService from './pages/TermsOfService';
import PrivacyPolicy from './pages/PrivacyPolicy';
import DisclaimerPage from './pages/Disclaimer';
import CookiePolicy from './pages/CookiePolicy';
import DataProcessingAgreement from './pages/DataProcessingAgreement';

function App() {
  return (
    <ErrorBoundary>
      <Router
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <Routes>
          <Route path="/" element={<HomePageNew />} />
          <Route path="/vop" element={<TermsOfService />} />
          <Route path="/privacy" element={<PrivacyPolicy />} />
          <Route path="/disclaimer" element={<DisclaimerPage />} />
          <Route path="/cookies" element={<CookiePolicy />} />
          <Route path="/dpa" element={<DataProcessingAgreement />} />
        </Routes>
      </Router>
    </ErrorBoundary>
  );
}

export default App;

