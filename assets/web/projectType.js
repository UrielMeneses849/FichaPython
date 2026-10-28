export const INVESTMENT_PROJECT_COLOR = '#278568';
// Azul de inversión exclusivo del mapa; las fichas conservan su paleta.
export const INVESTMENT_MAP_COLOR = '#006080';
export const ROUTE_INVESTMENT_NOTICE = 'Los proyectos de inversión no se incluyen en Crear Ruta.';

const normalize = (value) => String(value ?? '').normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

// El monto de inversión no indica el tipo: también las obras contratadas lo
// tienen. Dar prioridad al catálogo del WS; la clave PP es sólo un respaldo
// para las proyecciones ligeras que todavía no contienen Tipo_Proyecto.
export function isInvestmentProject(project) {
  if (!project || typeof project !== 'object') return false;
  const source = project.source && typeof project.source === 'object' ? project.source : {};
  const type = [project.tipoProyecto, project.Tipo_Proyecto, project.tipo_proyecto,
    project.proy_tipoproyectodescripcion, source.tipoProyecto, source.Tipo_Proyecto,
    source.tipo_proyecto, source.proy_tipoproyectodescripcion]
    .find((value) => value != null && String(value).trim());
  if (type != null) return /(?:^|\s)inversion(?:es)?(?:\s|$)/.test(normalize(type));
  const key = project.clave || project.Clave_Proyecto || project.proy_clave
    || source.clave || source.Clave_Proyecto || source.proy_clave || '';
  return /^PP\d/i.test(String(key).trim());
}
