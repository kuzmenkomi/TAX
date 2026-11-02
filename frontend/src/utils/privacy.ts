export function maskValue(value: string, hidden: boolean): string {
  return hidden ? '***' : value;
}

export function maskCount(value: number | string, hidden: boolean): string {
  return hidden ? '***' : String(value);
}

