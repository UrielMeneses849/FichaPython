export const PROJECT_PROGRESS_DISCLAIMER = 'NOTA: El porcentaje de avance reportado corresponde al tiempo transcurrido desde la fecha estimada de inicio del proyecto hasta la fecha de publicación, tomando como referencia del 100% la fecha de término estimada del proyecto.';

export function formatProjectCoordinate(value, axis) {
  const raw = String(value ?? '').trim();
  if (!raw) return 'Desconocido';
  const coordinate = Number(raw.replace(',', '.'));
  const limit = axis === 'latitude' ? 90 : 180;
  if (!Number.isFinite(coordinate) || Math.abs(coordinate) > limit) return 'Desconocido';
  return `${coordinate.toFixed(6)}°`;
}
export const valueOrUnknown = (value) => String(value || '').trim() || 'Desconocido';

const dateFormatter = new Intl.DateTimeFormat('es-MX', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  timeZone: 'UTC',
});

export const formatProjectDate = (value) => {
  const raw = String(value || '').trim();
  if (!raw) return 'Desconocido';

  const isoMatch = raw.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  const localMatch = raw.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  const parts = isoMatch
    ? [Number(isoMatch[1]), Number(isoMatch[2]), Number(isoMatch[3])]
    : localMatch
      ? [Number(localMatch[3]), Number(localMatch[2]), Number(localMatch[1])]
      : null;

  if (!parts) return raw;

  const [year, month, day] = parts;
  const date = new Date(Date.UTC(year, month - 1, day));
  const isValid = date.getUTCFullYear() === year
    && date.getUTCMonth() === month - 1
    && date.getUTCDate() === day;

  return isValid ? dateFormatter.format(date).replace('.', '') : raw;
};

export const cleanDisplayValue = (value) => {
  const cleaned = String(value || '')
    .trim()
    .replace(/^[,;:\s]+/, '')
    .replace(/\s+/g, ' ');
  return cleaned || 'Desconocido';
};

export const formatProjectLocation = (obra) => {
  const values = [obra.esta_descripcion, obra.muni_descripcion, obra.proy_localizacion]
    .map((value) => String(value || '').trim())
    .filter((value) => value && value.toLowerCase() !== 'desconocido');

  return [...new Set(values)].join(', ') || 'Desconocido';
};

export const formatNumber = (value) => {
  const number = Number(String(value ?? '').replace(/,/g, ''));
  return Number.isFinite(number) ? new Intl.NumberFormat('es-MX').format(number) : '0';
};

export const getProgress = (value) => {
  const match = String(value ?? '').replace(',', '.').match(/-?\d+(?:\.\d+)?/);
  if (!match) return null;
  return Math.max(0, Math.min(100, Number(match[0])));
};

export const getExplorerImageUrl = (obra) => String(obra.imagen_explorer || obra.imagenExplorer || obra.impo_image_url || '').trim();

const imageDateValue = (obra) => [obra?.fecha_imagen, obra?.fechaImagen, obra?.Fecha_Imagen, obra?.impo_fecha_imagen, obra?.impo_image_date]
  .find((value) => String(value ?? '').trim());

export const withExplorerImageDate = (detail, record) => ({
  ...detail,
  fecha_imagen: imageDateValue(detail) || imageDateValue(record?.source || record) || '',
});

export const getExplorerImageDate = (obra) => {
  const raw = imageDateValue(obra);
  // Nunca usar la publicación de la obra como fecha de captura de su imagen.
  return raw ? formatProjectDate(raw) : 'No disponible';
};

export const getProjectAdditional = (obra) => [
  ['Descripción', obra.descripcion], ['Acabados', obra.acabados],
  ['Observaciones', obra.observaciones], ['Descripción adicional', obra.descripcionextra],
  ['Características', obra.caracteristicas], ['Actualización', obra.actualizacion],
  ['Concurso', obra.concurso],
].filter(([, value]) => String(value || '').trim());
