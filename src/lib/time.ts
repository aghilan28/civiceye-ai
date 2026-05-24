export function nowIso() {
  return new Date().toISOString();
}

export function addHoursIso(sourceIso: string, hours: number) {
  const source = new Date(sourceIso);
  source.setHours(source.getHours() + hours);
  return source.toISOString();
}

export function createId(prefix: string) {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`.toUpperCase();
}
