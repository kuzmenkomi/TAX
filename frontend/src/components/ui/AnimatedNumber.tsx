import { motion, useSpring, useTransform } from 'framer-motion';
import { useEffect } from 'react';

interface AnimatedNumberProps {
  value: number;
  format?: 'currency' | 'decimal' | 'compact';
  currency?: string;
  className?: string;
  prefix?: string;
  suffix?: string;
  duration?: number;
}

/**
 * Animates a number counting from 0 to the target value.
 */
export function AnimatedNumber({
  value,
  format = 'decimal',
  currency = 'BRL',
  className = '',
  prefix = '',
  suffix = '',
  duration = 1500, // ms
}: AnimatedNumberProps) {
  // Use a spring physics model for smooth deceleration
  const spring = useSpring(0, {
    stiffness: 45,
    damping: 15,
    restDelta: 0.001,
  });

  useEffect(() => {
    spring.set(value);
  }, [value, spring]);

  // Transform the raw number into a formatted string during animation
  const displayValue = useTransform(spring, (current) => {
    let formatted: string;
    
    if (format === 'currency') {
      formatted = new Intl.NumberFormat(currency === 'BRL' ? 'pt-BR' : 'en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(current);
    } else if (format === 'compact') {
      formatted = new Intl.NumberFormat('en-US', {
        notation: 'compact',
        compactDisplay: 'short',
        maximumFractionDigits: 1,
      }).format(current);
    } else {
      formatted = new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 8,
      }).format(current);
    }

    return `${prefix}${formatted}${suffix}`;
  });

  return <motion.span className={className}>{displayValue}</motion.span>;
}

/**
 * A smaller, simpler counter for integers (like transaction counts)
 */
export function AnimatedCount({ value, className = '' }: { value: number; className?: string }) {
  const spring = useSpring(0, { stiffness: 50, damping: 20 });
  
  useEffect(() => {
    spring.set(value);
  }, [value, spring]);
  
  const display = useTransform(spring, (current) => Math.round(current).toString());
  
  return <motion.span className={className}>{display}</motion.span>;
}
