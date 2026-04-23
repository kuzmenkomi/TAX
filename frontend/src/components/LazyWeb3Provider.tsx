import React, { Suspense, lazy, useState, useEffect } from 'react';

// Lazy load the heavy web3 dependencies
const Web3ProviderContent = lazy(() => import('./Web3ProviderContent'));

export function LazyWeb3Provider({ children }: { children: React.ReactNode }) {
  const [shouldLoad, setShouldLoad] = useState(false);

  // We can trigger loading on first interaction or specifically when Connect Wallet is requested
  // For now, we'll provide a globally accessible trigger
  useEffect(() => {
    (window as any).__loadWeb3 = () => setShouldLoad(true);
  }, []);

  if (!shouldLoad) {
    return <>{children}</>;
  }

  return (
    <Suspense fallback={<div className="fixed inset-0 bg-brand-dark/50 backdrop-blur-sm z-[9999] flex items-center justify-center text-brand-green-500 font-syne font-bold">Initializing Web3...</div>}>
      <Web3ProviderContent>
        {children}
      </Web3ProviderContent>
    </Suspense>
  );
}

// Helper to trigger load from anywhere
export const triggerWeb3Load = () => {
  if ((window as any).__loadWeb3) {
    (window as any).__loadWeb3();
  }
};
