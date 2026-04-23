// ============================================================
// Глобальный стор — хранит результаты анализа из бэкенда
// Все компоненты читают данные отсюда
// ============================================================

import { createContext, useContext, useState, ReactNode } from 'react';
import { AnalyzeResult } from '../api/client';

interface AppState {
  // Results
  analyzeResult: AnalyzeResult | null;
  setAnalyzeResult: (res: AnalyzeResult | null) => void;

  // Jurisdictions
  jurisdictions: any[];
  setJurisdictions: (list: any[]) => void;
  currentJurisdiction: string;
  setCurrentJurisdiction: (code: string) => void;

  // Статус бэкенда
  backendOnline: boolean;
  setBackendOnline: (online: boolean) => void;

  // Идёт ли загрузка
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  // Ошибка
  error: string | null;
  setError: (err: string | null) => void;

  // Настройки анализа
  accountingMethod: string;
  setAccountingMethod: (method: string) => void;

  // Загруженный файл
  uploadedFile: File | null;
  setUploadedFile: (file: File | null) => void;
}

const AppContext = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [analyzeResult, setAnalyzeResult] = useState<AnalyzeResult | null>(null);
  const [jurisdictions, setJurisdictions] = useState<any[]>([]);
  const [currentJurisdiction, setCurrentJurisdiction] = useState<string>(localStorage.getItem('currentJurisdiction') || 'BR');
  const [backendOnline, setBackendOnline] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accountingMethod, setAccountingMethod] = useState('FIFO');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const handleSetJurisdiction = (code: string) => {
    setCurrentJurisdiction(code);
    localStorage.setItem('currentJurisdiction', code);
  };

  return (
    <AppContext.Provider value={{
      analyzeResult, setAnalyzeResult,
      jurisdictions, setJurisdictions,
      currentJurisdiction, setCurrentJurisdiction: handleSetJurisdiction,
      backendOnline, setBackendOnline,
      isLoading, setIsLoading,
      error, setError,
      accountingMethod, setAccountingMethod,
      uploadedFile, setUploadedFile,
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useAppContext must be used inside AppProvider');
  return ctx;
}
