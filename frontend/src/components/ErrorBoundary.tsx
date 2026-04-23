import React, { ReactNode, ErrorInfo } from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
    // In production, you could send this to an error tracking service
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.handleReset);
      }

      return (
        <div className="min-h-screen bg-[#0d0f14] flex items-center justify-center p-4">
          <div className="bg-[#1e2330] border border-white/5 rounded-[14px] max-w-md w-full p-8">
            <div className="flex justify-center mb-4">
              <div className="bg-[#f06a6a]/10 p-3 rounded-xl border border-[#f06a6a]/15">
                <AlertTriangle className="text-[#f06a6a]" size={32} />
              </div>
            </div>
            
            <h1 className="text-2xl font-syne font-bold text-center text-white mb-2">
              Something went wrong
            </h1>
            
            <p className="text-center text-[#5a6175] text-[13px] mb-6">
              An unexpected error occurred. The error details have been logged.
            </p>

            <div className="bg-[#12151c] rounded-lg p-4 mb-6 overflow-auto max-h-32 text-[11px] text-[#f06a6a] font-mono border border-white/5">
              {this.state.error.message || 'Unknown error'}
            </div>

            <button
              onClick={this.handleReset}
              className="w-full bg-brand-green-500 hover:bg-brand-green-400 text-brand-dark font-bold py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center gap-2 mb-2 text-[13px]"
            >
              <RotateCcw size={16} />
              Try Again
            </button>

            <button
              onClick={() => window.location.href = '/'}
              className="w-full bg-white/5 hover:bg-white/10 text-[#8b93a8] font-medium py-2.5 px-4 rounded-lg transition-colors border border-white/5 text-[13px]"
            >
              Go Home
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
