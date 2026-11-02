// ============================================================
// Глобальный стор — хранит результаты анализа из бэкенда
// Все компоненты читают данные отсюда
// ============================================================

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { AnalyzeResult } from '../api/v1';

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

  // Версия данных — инкрементируется при добавлении кошелька/CSV/биржи
  // Все страницы подписываются на это значение для авто-обновления
  dataVersion: number;
  bumpDataVersion: () => void;

  // Приватный режим для сумм и балансов
  isPrivacyMode: boolean;
  setIsPrivacyMode: (hidden: boolean) => void;
  togglePrivacyMode: () => void;
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
  const [dataVersion, setDataVersion] = useState(0);
  const [isPrivacyMode, setIsPrivacyModeState] = useState<boolean>(() => localStorage.getItem('declairo_privacy_mode') === 'true');
  const bumpDataVersion = useCallback(() => setDataVersion(v => v + 1), []);
  const setIsPrivacyMode = useCallback((hidden: boolean) => {
    setIsPrivacyModeState(hidden);
    localStorage.setItem('declairo_privacy_mode', String(hidden));
  }, []);
  const togglePrivacyMode = useCallback(() => {
    setIsPrivacyModeState((prev) => {
      const next = !prev;
      localStorage.setItem('declairo_privacy_mode', String(next));
      return next;
    });
  }, []);

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
      dataVersion, bumpDataVersion,
      isPrivacyMode, setIsPrivacyMode, togglePrivacyMode,
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
