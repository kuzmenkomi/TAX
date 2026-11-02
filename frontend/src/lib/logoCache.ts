/**
 * Logo Cache — двухуровневое кэширование иконок с Logo.dev
 *
 * L1: Map в памяти      — мгновенно, живёт пока открыта вкладка
 * L2: localStorage      — base64 dataURL, TTL 30 дней
 *
 * Результат: ~1 HTTP-запрос на домен за 30 дней на одном браузере.
 */

const CACHE_PREFIX = 'declairo_logo_v1_';
const CACHE_TTL_MS = 30 * 24 * 60 * 60 * 1000; // 30 дней

/** L1 — in-memory (сбрасывается при закрытии вкладки) */
const memCache = new Map<string, string>();

interface StoredEntry {
    dataUrl: string;
    expiresAt: number;
}

function storageKey(domain: string): string {
    return CACHE_PREFIX + domain.toLowerCase().replace(/\W/g, '_');
}

function readStorage(domain: string): string | null {
    try {
        const raw = localStorage.getItem(storageKey(domain));
        if (!raw) return null;
        const entry: StoredEntry = JSON.parse(raw);
        if (Date.now() > entry.expiresAt) {
            localStorage.removeItem(storageKey(domain));
            return null;
        }
        return entry.dataUrl;
    } catch {
        return null;
    }
}

function writeStorage(domain: string, dataUrl: string): void {
    try {
        const entry: StoredEntry = { dataUrl, expiresAt: Date.now() + CACHE_TTL_MS };
        localStorage.setItem(storageKey(domain), JSON.stringify(entry));
    } catch {
        // localStorage переполнен — игнорируем, L1-кэш всё равно работает
    }
}

function blobToDataUrl(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result as string);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

/** Ключ — промис, чтобы два одновременных вызова не делали два запроса */
const inFlight = new Map<string, Promise<string>>();

/**
 * Возвращает dataURL иконки.
 * Порядок: L1 mem → L2 localStorage → Logo.dev API (1 раз за 30 дней).
 * Бросает ошибку если API недоступен или токен не задан.
 */
export async function getLogoDataUrl(domain: string, token: string): Promise<string> {
    if (!token) throw new Error('VITE_LOGO_DEV_TOKEN not set');

    // L1
    const fromMem = memCache.get(domain);
    if (fromMem) return fromMem;

    // L2
    const fromStorage = readStorage(domain);
    if (fromStorage) {
        memCache.set(domain, fromStorage);
        return fromStorage;
    }

    // Дедупликация параллельных запросов
    const existing = inFlight.get(domain);
    if (existing) return existing;

    const fetchPromise = (async () => {
        const url = `https://img.logo.dev/${domain}?token=${token}&size=64&format=webp`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Logo.dev: ${res.status} for ${domain}`);
        const blob = await res.blob();
        const dataUrl = await blobToDataUrl(blob);
        memCache.set(domain, dataUrl);
        writeStorage(domain, dataUrl);
        return dataUrl;
    })().finally(() => inFlight.delete(domain));

    inFlight.set(domain, fetchPromise);
    return fetchPromise;
}

/** Очищает просроченные записи из localStorage (вызывать при старте приложения) */
export function pruneExpiredLogos(): void {
    try {
        const keysToDelete: string[] = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (!key?.startsWith(CACHE_PREFIX)) continue;
            const raw = localStorage.getItem(key);
            if (!raw) continue;
            try {
                const entry: StoredEntry = JSON.parse(raw);
                if (Date.now() > entry.expiresAt) keysToDelete.push(key);
            } catch {
                keysToDelete.push(key);
            }
        }
        keysToDelete.forEach(k => localStorage.removeItem(k));
    } catch { /* ignore */ }
}
