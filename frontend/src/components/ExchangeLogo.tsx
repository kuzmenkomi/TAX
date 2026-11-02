import React, { useState, useEffect, useRef } from 'react';
import { getLogoDataUrl } from '../lib/logoCache';

const TOKEN = import.meta.env.VITE_LOGO_DEV_TOKEN ?? '';

interface ExchangeLogoProps {
    /** Домен биржи, напр. "binance.com" */
    domain: string;
    /** Текстовый/JSX fallback пока грузится или если API недоступен */
    fallback: React.ReactNode;
    /** CSS классы для <img> */
    className?: string;
    /** Alt-текст */
    alt?: string;
}

/**
 * Рендерит иконку биржи с Logo.dev.
 * Кэширует результат в localStorage (30 дней) и памяти — каждый домен
 * запрашивается у API не чаще одного раза за 30 дней на одном браузере.
 */
export function ExchangeLogo({ domain, fallback, className = '', alt = '' }: ExchangeLogoProps) {
    const [src, setSrc] = useState<string | null>(null);
    const [failed, setFailed] = useState(false);
    const mounted = useRef(true);

    useEffect(() => {
        mounted.current = true;
        if (!TOKEN || !domain) {
            setFailed(true);
            return;
        }

        setSrc(null);
        setFailed(false);

        getLogoDataUrl(domain, TOKEN)
            .then(dataUrl => { if (mounted.current) setSrc(dataUrl); })
            .catch(() => { if (mounted.current) setFailed(true); });

        return () => { mounted.current = false; };
    }, [domain]);

    if (failed || (!TOKEN && !src)) {
        return <>{fallback}</>;
    }

    if (!src) {
        // Skeleton пока грузится
        return (
            <div
                className={`${className} rounded-md animate-pulse`}
                style={{ background: 'var(--border2)' }}
            />
        );
    }

    return (
        <img
            src={src}
            alt={alt}
            className={className}
            onError={() => setFailed(true)}
            loading="lazy"
            decoding="async"
        />
    );
}
