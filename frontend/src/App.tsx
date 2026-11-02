import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { I18nProvider } from './i18n/I18nContext';
import { AppProvider } from './context/AppContext';
import { ToastProvider } from './context/ToastContext';
import { ToastContainer } from './components/ToastContainer';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LazyWeb3Provider } from './components/LazyWeb3Provider';
import { ThemeProvider } from './context/ThemeContext';
import { ScrollToTop } from './components/ScrollToTop';

const HomePage = lazy(() => import('./pages/HomePage').then((module) => ({ default: module.HomePage })));
const RegisterPage = lazy(() => import('./pages/RegisterPage').then((module) => ({ default: module.RegisterPage })));
const LoginPage = lazy(() => import('./pages/LoginPage').then((module) => ({ default: module.LoginPage })));
const EmailVerificationPage = lazy(() =>
  import('./pages/EmailVerificationPage').then((module) => ({ default: module.EmailVerificationPage })),
);
const PasswordResetPage = lazy(() =>
  import('./pages/PasswordResetPage').then((module) => ({ default: module.PasswordResetPage })),
);
const OnboardingPage = lazy(() => import('./pages/OnboardingPage').then((module) => ({ default: module.OnboardingPage })));
const DashboardShell = lazy(() => import('./pages/DashboardShell').then((module) => ({ default: module.DashboardShell })));
const PrivacyPage = lazy(() => import('./pages/PrivacyPage').then((module) => ({ default: module.PrivacyPage })));
const TermsPage = lazy(() => import('./pages/TermsPage').then((module) => ({ default: module.TermsPage })));
const ContactPage = lazy(() => import('./pages/ContactPage').then((module) => ({ default: module.ContactPage })));
const SecurityPage = lazy(() => import('./pages/SecurityPage').then((module) => ({ default: module.SecurityPage })));
const DisclaimerPage = lazy(() => import('./pages/DisclaimerPage').then((module) => ({ default: module.DisclaimerPage })));
const CookiePolicyPage = lazy(() => import('./pages/CookiePolicyPage').then((module) => ({ default: module.CookiePolicyPage })));
const OAuthCallback = lazy(() => import('./pages/OAuthCallback'));
const BillingPage = lazy(() => import('./pages/BillingPage').then((module) => ({ default: module.BillingPage })));
const BlogPage = lazy(() => import('./pages/BlogPage').then((module) => ({ default: module.BlogPage })));
const BlogArticlePage = lazy(() => import('./pages/BlogArticlePage').then((module) => ({ default: module.BlogArticlePage })));

function RouteFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center text-sm font-bold" style={{ color: 'var(--text)' }}>
      Loading...
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <AuthProvider>
        <I18nProvider>
          <ThemeProvider>
            <AppProvider>
              <ToastProvider>
                <LazyWeb3Provider>
                  <ToastContainer />
                  <ErrorBoundary>
                    <Suspense fallback={<RouteFallback />}>
                      <Routes>
                        <Route path="/" element={<HomePage />} />
                        <Route path="/register" element={<RegisterPage />} />
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/verify-email" element={<EmailVerificationPage />} />
                        <Route path="/password-reset" element={<PasswordResetPage />} />
                        <Route path="/privacy" element={<PrivacyPage />} />
                        <Route path="/terms" element={<TermsPage />} />
                        <Route path="/contact" element={<ContactPage />} />
                        <Route path="/security" element={<SecurityPage />} />
                        <Route path="/disclaimer" element={<DisclaimerPage />} />
                        <Route path="/cookie-policy" element={<CookiePolicyPage />} />
                        <Route path="/blog" element={<BlogPage />} />
                        <Route path="/blog/:slug" element={<BlogArticlePage />} />
                        <Route
                          path="/onboarding"
                          element={
                            <ProtectedRoute>
                              <OnboardingPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/dashboard"
                          element={
                            <ProtectedRoute>
                              <ErrorBoundary>
                                <DashboardShell />
                              </ErrorBoundary>
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/billing"
                          element={
                            <ProtectedRoute>
                              <BillingPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/oauth/callback"
                          element={<OAuthCallback />}
                        />
                        <Route path="*" element={<Navigate to="/" replace />} />
                      </Routes>
                    </Suspense>
                  </ErrorBoundary>
                </LazyWeb3Provider>
              </ToastProvider>
            </AppProvider>
          </ThemeProvider>
        </I18nProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
