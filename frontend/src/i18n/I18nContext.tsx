import { createContext, useContext, useMemo, useState, ReactNode } from 'react';

export type Locale = 'pt' | 'es' | 'en';

type Dict = Record<string, string>;

const dicts: Record<Locale, Dict> = {
  pt: {
    // ===== AUTH PAGES =====
    'auth.login': 'Entrar',
    'auth.register': 'Criar conta',
    'auth.email': 'Email',
    'auth.password': 'Senha',
    'auth.confirmPassword': 'Confirmar senha',
    'auth.name': 'Nome completo',
    'auth.submit': 'Continuar',
    'auth.haveAccount': 'Já tem conta?',
    'auth.noAccount': 'Ainda não tem conta?',
    'auth.forgotPassword': 'Esqueceu a senha?',
    'auth.orContinueWith': 'Ou continue com',
    'auth.google': 'Google',
    'auth.github': 'GitHub',
    'auth.privacy': 'Ao se registrar, você concorda com nossos Termos de Serviço e Política de Privacidade.',
    'auth.termsOfService': 'Termos de Serviço',
    'auth.privacyPolicy': 'Política de Privacidade',
    'auth.error.invalidEmail': 'Email inválido',
    'auth.error.passwordTooShort': 'Senha deve ter pelo menos 8 caracteres',
    'auth.error.passwordsNotMatch': 'Senhas não conferem',
    'auth.error.emailExists': 'Este email já está registrado',
    'auth.error.invalidCredentials': 'Email ou senha incorretos',
    'auth.loading': 'Carregando...',
    'auth.emailSent': 'Email enviado! Verifique sua caixa de entrada.',
    'auth.welcomeBack': 'Bem-vindo de volta!',
    'auth.firstName': 'Primeiro nome',
    'auth.lastName': 'Sobrenome',
    'auth.legalPrefix': 'Ao se registrar, você concorda com nossos',
    'auth.startCalculating': 'Comece a calcular seus impostos hoje.',
    'auth.submitRegistration': 'Criar minha conta',
    'auth.success.registered': 'Conta criada com sucesso!',
    'auth.error.missingFields': 'Por favor, preencha todos os campos',
    'auth.error.registrationFailed': 'Falha ao criar conta',
    'auth.error.unauthorized': 'Não autorizado. Por favor, entre novamente.',
    
    // ===== ONBOARDING =====
    'onboarding.title': 'Quase lá!',
    'onboarding.countryTitle': 'Onde você investe?',
    'onboarding.countrySubtitle': 'Isso nos ajuda a configurar as regras fiscais locais e a moeda base.',
    'onboarding.structureTitle': 'Qual sua estrutura?',
    'onboarding.structureSubtitle': 'Pessoa física ou jurídica? Isso muda a forma de cálculo.',
    'onboarding.portfolioTitle': 'Tamanho do portfólio',
    'onboarding.portfolioSubtitle': 'Apenas uma estimativa para otimizarmos seu painel.',
    'onboarding.completeTitle': 'Pronto para começar!',
    'onboarding.completeSubtitle': 'Seu perfil institucional está agora ativo.',
    'onboarding.redirecting': 'Redirecionando para o portal...',

    // ===== LANDING PAGE =====
    'landing.title': 'The #1 Crypto Tax Software',
    'landing.subtitle': 'Crypto taxes done in minutes. Built to save you time & maximize your refund.',
    'landing.heroFeature1': 'Free Portfolio Tracking',
    'landing.heroFeature2': 'Advanced DeFi & NFT Support',
    'landing.heroFeature3': 'TurboTax Partner',
    'landing.getStarted': 'Get Started For Free',
    'landing.seeReport': 'See Example Report',
    'landing.hero.import': 'Import Transactions',
    'landing.hero.importDesc': 'Connect your wallets and exchanges. We support 500+ integrations.',
    'landing.hero.sync': 'Auto-Sync & Smart Matching',
    'landing.hero.syncDesc': 'Automatically sync new transactions daily.',
    'landing.hero.dashboard': 'Real-Time Dashboard',
    'landing.hero.dashboardDesc': 'Track your portfolio value and tax liability.',
    'landing.faq.title': 'Frequently Asked Questions',
    'landing.testimonials': 'Trusted by Crypto Investors Worldwide',
    'landing.integrations': '500+ Integrations',
    'landing.calculate': 'Calculate Your Crypto Taxes Today',

    // ===== NAVIGATION & HEADER =====
    'nav.dashboard': 'Painel',
    'nav.transactions': 'Transações',
    'nav.tax': 'Impostos',
    'nav.issues': 'Alertas',
    'nav.wallets': 'Carteiras',
    'header.search': 'Buscar transações, carteiras, ativos…',
    'header.addWallet': 'Adicionar carteira',
    'header.lang': 'Idioma',
    'header.profile': 'Perfil',
    'header.logout': 'Sair',

    // ===== TAX CENTER =====
    'tax.title': 'Centro fiscal',
    'tax.subtitle': 'CSV ou API Binance — cálculo de P&L para o Brasil.',
    'tax.quote': 'Moeda de cotação',
    'tax.multi': 'Vários CSV (mesmo formato)',
    'tax.binance.title': 'Sincronizar Binance (API read-only)',
    'tax.binance.key': 'API Key',
    'tax.binance.secret': 'API Secret',
    'tax.binance.run': 'Sincronizar e analisar',
    'tax.download': 'CSV contador (BR)',
    'tax.method': 'Método contábil',
    'tax.country': 'País',

    // ===== ISSUES & QUALITY =====
    'issues.title': 'Qualidade dos dados',
    'issues.empty': 'Execute uma análise no Centro fiscal para ver alertas.',
    'issues.severity.error': 'Erro',
    'issues.severity.warning': 'Aviso',
    'issues.severity.info': 'Info',

    // ===== COMMON =====
    'common.save': 'Salvar',
    'common.cancel': 'Cancelar',
    'common.delete': 'Deletar',
    'common.edit': 'Editar',
    'common.loading': 'Carregando...',
    'common.error': 'Erro',
    'common.success': 'Sucesso!',
    'common.back': 'Voltar',
    'common.complete': 'completo',
    'common.processing': 'Processando...',
  },
  es: {
    // ===== AUTH PAGES =====
    'auth.login': 'Iniciar sesión',
    'auth.register': 'Crear cuenta',
    'auth.email': 'Correo electrónico',
    'auth.password': 'Contraseña',
    'auth.confirmPassword': 'Confirmar contraseña',
    'auth.name': 'Nombre completo',
    'auth.submit': 'Continuar',
    'auth.haveAccount': '¿Ya tienes cuenta?',
    'auth.noAccount': '¿Aún no tienes cuenta?',
    'auth.forgotPassword': '¿Olvidaste tu contraseña?',
    'auth.orContinueWith': 'O continúa con',
    'auth.google': 'Google',
    'auth.github': 'GitHub',
    'auth.privacy': 'Al registrarte, aceptas nuestros Términos de Servicio y Política de Privacidad.',
    'auth.termsOfService': 'Términos de Servicio',
    'auth.privacyPolicy': 'Política de Privacidad',
    'auth.error.invalidEmail': 'Correo inválido',
    'auth.error.passwordTooShort': 'La contraseña debe tener al menos 8 caracteres',
    'auth.error.passwordsNotMatch': 'Las contraseñas no coinciden',
    'auth.error.emailExists': 'Este correo ya está registrado',
    'auth.error.invalidCredentials': 'Correo o contraseña incorrectos',
    'auth.loading': 'Cargando...',
    'auth.emailSent': '¡Correo enviado! Revisa tu bandeja de entrada.',
    'auth.welcomeBack': '¡Bienvenido de nuevo!',
    'auth.firstName': 'Primer nombre',
    'auth.lastName': 'Apellido',
    'auth.legalPrefix': 'Al registrarte, aceptas nuestros',
    'auth.startCalculating': 'Comienza a calcular tus impuestos hoy.',
    'auth.submitRegistration': 'Crear mi cuenta',
    'auth.success.registered': '¡Cuenta creada con éxito!',
    'auth.error.missingFields': 'Por favor, completa todos los campos',
    'auth.error.registrationFailed': 'Error al crear la cuenta',
    'auth.error.unauthorized': 'No autorizado. Por favor, inicia sesión de nuevo.',
    
    // ===== ONBOARDING =====
    'onboarding.title': '¡Casi listo!',
    'onboarding.countryTitle': '¿Dónde inviertes?',
    'onboarding.countrySubtitle': 'Esto nos ayuda a configurar las reglas fiscales locales y la moneda base.',
    'onboarding.structureTitle': '¿Cuál es tu estructura?',
    'onboarding.structureSubtitle': '¿Persona física o jurídica? Esto cambia la forma de cálculo.',
    'onboarding.portfolioTitle': 'Tamaño de cartera',
    'onboarding.portfolioSubtitle': 'Solo una estimación para optimizar tu panel.',
    'onboarding.completeTitle': '¡Listo para comenzar!',
    'onboarding.completeSubtitle': 'Tu perfil institucional ya está activo.',
    'onboarding.redirecting': 'Redirigiendo al portal...',

    // ===== LANDING PAGE =====
    'landing.title': 'El #1 Software de Impuestos Cripto',
    'landing.subtitle': 'Impuestos cripto en minutos. Hecho para ahorrar tiempo y maximizar tu reembolso.',
    'landing.heroFeature1': 'Seguimiento de Cartera Gratuito',
    'landing.heroFeature2': 'Soporte Avanzado DeFi y NFT',
    'landing.heroFeature3': 'Socio de TurboTax',
    'landing.getStarted': 'Comenzar Gratis',
    'landing.seeReport': 'Ver Ejemplo de Informe',
    'landing.hero.import': 'Importar Transacciones',
    'landing.hero.importDesc': 'Conecta tus carteras e intercambios. Soportamos 500+ integraciones.',
    'landing.hero.sync': 'Sincronización Automática y Coincidencia Inteligente',
    'landing.hero.syncDesc': 'Sincroniza automáticamente nuevas transacciones diariamente.',
    'landing.hero.dashboard': 'Panel en Tiempo Real',
    'landing.hero.dashboardDesc': 'Monitorea tu valor de cartera y responsabilidad fiscal.',
    'landing.faq.title': 'Preguntas Frecuentes',
    'landing.testimonials': 'Confiado por Inversores Cripto en Todo el Mundo',
    'landing.integrations': '500+ Integraciones',
    'landing.calculate': 'Calcula Tus Impuestos Cripto Hoy',

    // ===== NAVIGATION & HEADER =====
    'nav.dashboard': 'Panel',
    'nav.transactions': 'Transacciones',
    'nav.tax': 'Impuestos',
    'nav.issues': 'Alertas',
    'nav.wallets': 'Carteras',
    'header.search': 'Buscar transacciones, carteras, activos…',
    'header.addWallet': 'Añadir cartera',
    'header.lang': 'Idioma',
    'header.profile': 'Perfil',
    'header.logout': 'Cerrar sesión',

    // ===== TAX CENTER =====
    'tax.title': 'Centro fiscal',
    'tax.subtitle': 'CSV o API Binance — P&L enfocado en Brasil.',
    'tax.quote': 'Moneda de cotización',
    'tax.multi': 'Varios CSV (mismo formato)',
    'tax.binance.title': 'Sincronizar Binance (API solo lectura)',
    'tax.binance.key': 'API Key',
    'tax.binance.secret': 'API Secret',
    'tax.binance.run': 'Sincronizar y analizar',
    'tax.download': 'CSV contador (BR)',
    'tax.method': 'Método contable',
    'tax.country': 'País',

    // ===== ISSUES & QUALITY =====
    'issues.title': 'Calidad de datos',
    'issues.empty': 'Ejecuta un análisis en el Centro fiscal para ver alertas.',
    'issues.severity.error': 'Error',
    'issues.severity.warning': 'Advertencia',
    'issues.severity.info': 'Info',

    // ===== COMMON =====
    'common.save': 'Guardar',
    'common.cancel': 'Cancelar',
    'common.delete': 'Eliminar',
    'common.edit': 'Editar',
    'common.loading': 'Cargando...',
    'common.error': 'Error',
    'common.success': '¡Éxito!',
    'common.back': 'Volver',
    'common.complete': 'completado',
    'common.processing': 'Procesando...',
  },
  en: {
    // ===== AUTH PAGES =====
    'auth.login': 'Log in',
    'auth.register': 'Sign up',
    'auth.email': 'Email',
    'auth.password': 'Password',
    'auth.confirmPassword': 'Confirm password',
    'auth.name': 'Full name',
    'auth.submit': 'Continue',
    'auth.haveAccount': 'Already have an account?',
    'auth.noAccount': "Don't have an account yet?",
    'auth.forgotPassword': 'Forgot password?',
    'auth.orContinueWith': 'Or continue with',
    'auth.google': 'Google',
    'auth.github': 'GitHub',
    'auth.privacy': 'By signing up, you agree to our Terms of Service and Privacy Policy.',
    'auth.termsOfService': 'Terms of Service',
    'auth.privacyPolicy': 'Privacy Policy',
    'auth.error.invalidEmail': 'Invalid email',
    'auth.error.passwordTooShort': 'Password must be at least 8 characters',
    'auth.error.passwordsNotMatch': 'Passwords do not match',
    'auth.error.emailExists': 'This email is already registered',
    'auth.error.invalidCredentials': 'Invalid email or password',
    'auth.loading': 'Loading...',
    'auth.emailSent': 'Email sent! Check your inbox.',
    'auth.welcomeBack': 'Welcome back!',
    'auth.firstName': 'First Name',
    'auth.lastName': 'Last Name',
    'auth.legalPrefix': 'By signing up, you agree to our',
    'auth.startCalculating': 'Start calculating your taxes today.',
    'auth.submitRegistration': 'Create my account',
    'auth.success.registered': 'Account created successfully!',
    'auth.error.missingFields': 'Please fill all fields',
    'auth.error.registrationFailed': 'Registration failed',
    'auth.error.unauthorized': 'Unauthorized. Please log in again.',
    
    // ===== ONBOARDING =====
    'onboarding.title': 'Almost there!',
    'onboarding.countryTitle': 'Where do you invest?',
    'onboarding.countrySubtitle': 'This helps us set up the local tax rules and base currency for your account.',
    'onboarding.structureTitle': 'Your Tax Structure',
    'onboarding.structureSubtitle': 'Are you an individual or a business? This changes the reporting requirements.',
    'onboarding.portfolioTitle': 'Portfolio Size',
    'onboarding.portfolioSubtitle': 'Just an estimate to help us optimize your dashboard experience.',
    'onboarding.completeTitle': 'Ready to Launch!',
    'onboarding.completeSubtitle': 'Your institutional profile is now active.',
    'onboarding.redirecting': 'Redirecting to portal...',

    // ===== LANDING PAGE =====
    'landing.title': 'The #1 Crypto Tax Software',
    'landing.subtitle': 'Crypto taxes done in minutes. Built to save you time & maximize your refund.',
    'landing.heroFeature1': 'Free Portfolio Tracking',
    'landing.heroFeature2': 'Advanced DeFi & NFT Support',
    'landing.heroFeature3': 'TurboTax Partner',
    'landing.getStarted': 'Get Started For Free',
    'landing.seeReport': 'See Example Report',
    'landing.hero.import': 'Import Transactions',
    'landing.hero.importDesc': 'Connect your wallets and exchanges. We support 500+ integrations.',
    'landing.hero.sync': 'Auto-Sync & Smart Matching',
    'landing.hero.syncDesc': 'Automatically sync new transactions daily.',
    'landing.hero.dashboard': 'Real-Time Dashboard',
    'landing.hero.dashboardDesc': 'Track your portfolio value and tax liability.',
    'landing.faq.title': 'Frequently Asked Questions',
    'landing.testimonials': 'Trusted by Crypto Investors Worldwide',
    'landing.integrations': '500+ Integrations',
    'landing.calculate': 'Calculate Your Crypto Taxes Today',

    // ===== NAVIGATION & HEADER =====
    'nav.dashboard': 'Dashboard',
    'nav.transactions': 'Transactions',
    'nav.tax': 'Taxes',
    'nav.issues': 'Alerts',
    'nav.wallets': 'Wallets',
    'header.search': 'Search transactions, wallets, assets…',
    'header.addWallet': 'Add wallet',
    'header.lang': 'Language',
    'header.profile': 'Profile',
    'header.logout': 'Log out',

    // ===== TAX CENTER =====
    'tax.title': 'Tax Center',
    'tax.subtitle': 'CSV or Binance API — P&L calculation for Brazil.',
    'tax.quote': 'Quote currency',
    'tax.multi': 'Multiple CSVs (same format)',
    'tax.binance.title': 'Sync Binance (read-only API)',
    'tax.binance.key': 'API Key',
    'tax.binance.secret': 'API Secret',
    'tax.binance.run': 'Sync and analyze',
    'tax.download': 'CSV for accountant (BR)',
    'tax.method': 'Accounting method',
    'tax.country': 'Country',

    // ===== ISSUES & QUALITY =====
    'issues.title': 'Data quality',
    'issues.empty': 'Run an analysis in Tax Center to see alerts.',
    'issues.severity.error': 'Error',
    'issues.severity.warning': 'Warning',
    'issues.severity.info': 'Info',

    // ===== COMMON =====
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.delete': 'Delete',
    'common.edit': 'Edit',
    'common.loading': 'Loading...',
    'common.error': 'Error',
    'common.success': 'Success!',
    'common.back': 'Back',
    'common.complete': 'complete',
    'common.processing': 'Processing...',
  },
};

type I18nState = {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string) => string;
};

const I18nContext = createContext<I18nState | null>(null);

const STORAGE = 'declairo_locale_v1';

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => {
    try {
      const s = localStorage.getItem(STORAGE) as Locale | null;
      if (s === 'pt' || s === 'es' || s === 'en') return s;
    } catch {
      /* ignore */
    }
    return 'pt';
  });

  const setLocale = (l: Locale) => {
    setLocaleState(l);
    try {
      localStorage.setItem(STORAGE, l);
    } catch {
      /* ignore */
    }
  };

  const value = useMemo<I18nState>(() => {
    const t = (key: string) => dicts[locale][key] ?? dicts.en[key] ?? key;
    return { locale, setLocale, t };
  }, [locale]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used inside I18nProvider');
  return ctx;
}
