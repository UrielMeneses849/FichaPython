// Generado por scripts/sync_web_renderer.py. No editar a mano.
(() => {
const { PDFDocument, PDFName, PDFRawStream, PDFString, rgb } = PDFLib;
const PROJECT_PROGRESS_DISCLAIMER = 'NOTA: El porcentaje de avance reportado corresponde al tiempo transcurrido desde la fecha estimada de inicio del proyecto hasta la fecha de publicación, tomando como referencia del 100% la fecha de término estimada del proyecto.';

function formatProjectCoordinate(value, axis) {
  const raw = String(value ?? '').trim();
  if (!raw) return 'Desconocido';
  const coordinate = Number(raw.replace(',', '.'));
  const limit = axis === 'latitude' ? 90 : 180;
  if (!Number.isFinite(coordinate) || Math.abs(coordinate) > limit) return 'Desconocido';
  return `${coordinate.toFixed(6)}°`;
}
const valueOrUnknown = (value) => String(value || '').trim() || 'Desconocido';

const dateFormatter = new Intl.DateTimeFormat('es-MX', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  timeZone: 'UTC',
});

const formatProjectDate = (value) => {
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

const cleanDisplayValue = (value) => {
  const cleaned = String(value || '')
    .trim()
    .replace(/^[,;:\s]+/, '')
    .replace(/\s+/g, ' ');
  return cleaned || 'Desconocido';
};

const formatProjectLocation = (obra) => {
  const values = [obra.esta_descripcion, obra.muni_descripcion, obra.proy_localizacion]
    .map((value) => String(value || '').trim())
    .filter((value) => value && value.toLowerCase() !== 'desconocido');

  return [...new Set(values)].join(', ') || 'Desconocido';
};

const formatNumber = (value) => {
  const number = Number(String(value ?? '').replace(/,/g, ''));
  return Number.isFinite(number) ? new Intl.NumberFormat('es-MX').format(number) : '0';
};

const getProgress = (value) => {
  const match = String(value ?? '').replace(',', '.').match(/-?\d+(?:\.\d+)?/);
  if (!match) return null;
  return Math.max(0, Math.min(100, Number(match[0])));
};

const getExplorerImageUrl = (obra) => String(obra.imagen_explorer || obra.imagenExplorer || obra.impo_image_url || '').trim();

const imageDateValue = (obra) => [obra?.fecha_imagen, obra?.fechaImagen, obra?.Fecha_Imagen, obra?.impo_fecha_imagen, obra?.impo_image_date]
  .find((value) => String(value ?? '').trim());

const withExplorerImageDate = (detail, record) => ({
  ...detail,
  fecha_imagen: imageDateValue(detail) || imageDateValue(record?.source || record) || '',
});

const getExplorerImageDate = (obra) => {
  const raw = imageDateValue(obra);
  // Nunca usar la publicación de la obra como fecha de captura de su imagen.
  return raw ? formatProjectDate(raw) : 'No disponible';
};

const getProjectAdditional = (obra) => [
  ['Descripción', obra.descripcion], ['Acabados', obra.acabados],
  ['Observaciones', obra.observaciones], ['Descripción adicional', obra.descripcionextra],
  ['Características', obra.caracteristicas], ['Actualización', obra.actualizacion],
  ['Concurso', obra.concurso],
].filter(([, value]) => String(value || '').trim());

const INVESTMENT_PROJECT_COLOR = '#278568';
// Azul de inversión exclusivo del mapa; las fichas conservan su paleta.
const INVESTMENT_MAP_COLOR = '#006080';
const ROUTE_INVESTMENT_NOTICE = 'Los proyectos de inversión no se incluyen en Crear Ruta.';

const normalize = (value) => String(value ?? '').normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

// El monto de inversión no indica el tipo: también las obras contratadas lo
// tienen. Dar prioridad al catálogo del WS; la clave PP es sólo un respaldo
// para las proyecciones ligeras que todavía no contienen Tipo_Proyecto.
function isInvestmentProject(project) {
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


const COLORS = {
  ink: '#313A4A', muted: '#687386', border: '#E5E7EB',
  surface: '#F7F8FA', chip: '#E9ECF1', accent: '#D95B27', tag: '#B9471E', white: '#FFFFFF',
};
const color = (hex) => rgb(...hex.slice(1).match(/../g).map((channel) => parseInt(channel, 16) / 255));
// A3 conserva las columnas de la ficha web y una imagen satelital legible.
const PAGE = [842, 1191];
const MARGIN = 28;
const WIDTH = PAGE[0] - MARGIN * 2;

// Banda vectorial que sigue las esquinas del contenedor, como border-left
// sobre border-radius en la ficha web (no una línea recta con extremos redondos).
function curvedFichaAccentPath(height, radius = 16, thickness = 3.5) {
  const r = Math.min(radius, height / 2);
  const t = Math.min(thickness, r);
  const c = 0.5522847498;
  return `M ${r} 0 C ${r * (1 - c)} 0 0 ${r * (1 - c)} 0 ${r} L 0 ${height - r} C 0 ${height - r * (1 - c)} ${r * (1 - c)} ${height} ${r} ${height} C ${r - (r - t) * c} ${height - t * 0.35} ${t} ${height - r + (r - t) * c} ${t} ${height - r} L ${t} ${r} C ${t} ${r - (r - t) * c} ${r - (r - t) * c} ${t * 0.35} ${r} 0 Z`;
}

const downloadedAt = (date = new Date()) => new Intl.DateTimeFormat('es-MX', {
  day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false,
}).format(date);

// Las imágenes de bimsareports.com no habilitan CORS. El PDF autorizado del
// servicio sí las incluye: recuperamos sólo el JPEG satelital de mayor área.
async function extraerImagenSatelitalPdf(bytes) {
  const source = await PDFDocument.load(bytes);
  const images = source.context.enumerateIndirectObjects()
    .map(([, object]) => object)
    .filter((object) => object instanceof PDFRawStream
      && object.dict.get(PDFName.of('Subtype'))?.toString() === '/Image'
      && object.dict.get(PDFName.of('Filter'))?.toString() === '/DCTDecode')
    .map((object) => ({
      object,
      width: Number(object.dict.get(PDFName.of('Width'))?.toString()),
      height: Number(object.dict.get(PDFName.of('Height'))?.toString()),
    }))
    .filter(({ width, height }) => width >= 300 && height >= 200)
    .sort((a, b) => b.width * b.height - a.width * a.height);
  if (!images.length) throw new Error('El servicio no incluyó una imagen satelital válida para la ficha.');
  return images[0].object.contents.slice();
}

function wrap(text, font, size, width) {
  const lines = [];
  for (const paragraph of String(text ?? '').split(/\r?\n/)) {
    let line = '';
    for (const word of paragraph.split(/\s+/).filter(Boolean)) {
      if (font.widthOfTextAtSize(word, size) > width + 0.01) {
        if (line) lines.push(line);
        line = '';
        for (const letter of word) {
          if (line && font.widthOfTextAtSize(line + letter, size) > width + 0.01) {
            lines.push(line);
            line = '';
          }
          line += letter;
        }
      } else {
        const next = line ? `${line} ${word}` : word;
        if (line && font.widthOfTextAtSize(next, size) > width + 0.01) {
          lines.push(line);
          line = word;
        } else line = next;
      }
    }
    lines.push(line);
  }
  return lines;
}

const documentResources = new WeakMap();

// Texto vectorial seleccionable. Formatos compartidos con la ficha web.
async function generarDocumentoFicha(obra, { regularBytes, mediumBytes, semiBoldBytes, logoPng, satelliteBytes, generatedAt, targetDocument } = {}, empresa) {
  if (empresa ? !empresa.name : !obra?.proy_clave) throw new Error('Es necesario cargar la ficha antes de descargarla.');
  const pdf = targetDocument || await PDFDocument.create();
  let resources = documentResources.get(pdf);
  if (!resources) {
    pdf.registerFontkit(fontkit);
    const [regular, medium, semiBold, logo] = await Promise.all([
      pdf.embedFont(regularBytes, { subset: true }),
      pdf.embedFont(mediumBytes, { subset: true }),
      pdf.embedFont(semiBoldBytes, { subset: true }),
      pdf.embedPng(logoPng),
    ]);
    resources = { fonts: { regular, medium, semiBold }, logo };
    documentResources.set(pdf, resources);
  }
  const { fonts, logo } = resources;
  const isExplorer = obra.origen === 'explorer' || Boolean(getExplorerImageUrl(obra));
  let satellite;
  if (isExplorer && getExplorerImageUrl(obra)) {
    if (!satelliteBytes) throw new Error('No fue posible cargar la imagen satelital para el PDF.');
    const bytes = new Uint8Array(satelliteBytes);
    satellite = bytes[0] === 0x89 ? await pdf.embedPng(bytes) : await pdf.embedJpg(bytes);
  }
  let page;
  let top;
  const rect = (x, y, w, h, fill, radius = 8, stroke) => {
    const r = Math.max(0, Math.min(radius, w / 2, h / 2));
    const path = `M ${r} 0 L ${w - r} 0 Q ${w} 0 ${w} ${r} L ${w} ${h - r} Q ${w} ${h} ${w - r} ${h} L ${r} ${h} Q 0 ${h} 0 ${h - r} L 0 ${r} Q 0 0 ${r} 0 Z`;
    page.drawSvgPath(path, {
      x, y: PAGE[1] - y,
      color: color(fill), borderColor: stroke ? color(stroke) : undefined,
      borderWidth: stroke ? 0.7 : 0,
    });
  };
  const text = (value, x, y, width, { size = 9.5, weight = 'regular', ink = COLORS.ink, align = 'left', noWrap = false } = {}) => {
    const font = fonts[weight];
    const lines = noWrap ? [String(value)] : wrap(value, font, size, width);
    const lineHeight = size * 1.55;
    lines.forEach((line, index) => {
      const lineWidth = font.widthOfTextAtSize(line, size);
      const offset = align === 'right' ? width - lineWidth : align === 'center' ? (width - lineWidth) / 2 : 0;
      page.drawText(line, { x: x + offset, y: PAGE[1] - y - size - index * lineHeight, size, font, color: color(ink) });
    });
    return lines.length * lineHeight;
  };
  const textHeight = (value, width, size = 9.5, weight = 'regular') => wrap(value, fonts[weight], size, width).length * size * 1.55;
  const tagWidth = (value, size = 9) => Math.ceil(fonts.semiBold.widthOfTextAtSize(value, size)) + 22;
  const tag = (value, x, y, available, { fill = COLORS.white, ink = COLORS.tag, border = COLORS.accent, size = 9, noWrap = false } = {}) => {
    const w = Math.min(available, tagWidth(value, size));
    const fittedSize = noWrap ? Math.min(size, size * (w - 20) / fonts.semiBold.widthOfTextAtSize(value, size)) : size;
    const h = noWrap ? fittedSize * 1.55 + 10 : textHeight(value, w - 20, size, 'semiBold') + 10;
    rect(x, y, w, h, fill, 12, border);
    text(value, x + 10, y + 5, w - 20, { size: fittedSize, weight: 'semiBold', ink, align: 'center', noWrap });
    return { w, h };
  };
  const addPage = () => { page = pdf.addPage(PAGE); top = MARGIN; };
  const ensure = (height) => { if (top + height > PAGE[1] - MARGIN) addPage(); };
  const section = (title, height, accent = false, compact = false) => {
    ensure(height);
    const y = top;
    rect(MARGIN, y, WIDTH, height, COLORS.white, 16, COLORS.border);
    if (accent) page.drawSvgPath(curvedFichaAccentPath(height), {
      x: MARGIN, y: PAGE[1] - y, color: color(COLORS.accent),
    });
    text(title, MARGIN + 18, y + (compact ? 11 : 18), WIDTH - 36, { size: compact ? 12 : 16, weight: compact ? 'medium' : 'regular' });
    top += height + 10;
    return y;
  };
  const flowSection = (title, blocks, { accent = false, compact = false } = {}) => {
    const headerHeight = compact ? 36 : 48;
    const bottomPadding = compact ? 8 : 16;
    // Reserva adicional para que los visores PDF no recorten el borde inferior.
    const pageBottom = PAGE[1] - MARGIN - 28;
    let index = 0;
    let pageIndex = 0;

    while (index < blocks.length) {
      if (pageIndex) addPage();
      let available = pageBottom - top - headerHeight - bottomPadding;
      // El espacio mínimo depende de la siguiente tarjeta: las de proyectos
      // pueden ser más altas que el hueco restante tras los contactos.
      if (available < Math.max(80, blocks[index].height) && top > MARGIN) {
        addPage();
        available = pageBottom - top - headerHeight - bottomPadding;
      }

      const start = index;
      let contentHeight = 0;
      while (index < blocks.length && contentHeight + blocks[index].height <= available) {
        contentHeight += blocks[index].height;
        index += 1;
      }
      if (index === start) {
        throw new Error(`El bloque "${title}" excede el alto disponible de la ficha.`);
      }

      const chunk = blocks.slice(start, index);
      while (chunk.length > 1 && chunk.at(-1).spacer) {
        contentHeight -= chunk.pop().height;
        index -= 1;
      }
      const y = section(pageIndex ? `${title} · continuación` : title,
        headerHeight + contentHeight + bottomPadding, accent, compact);
      let contentY = y + headerHeight;
      chunk.forEach((block) => {
        block.draw(contentY);
        contentY += block.height;
      });
      pageIndex += 1;
    }
  };
  const cardHeight = (value, width) => 36 + textHeight(value, width - 24, 10, 'medium');
  const card = (label, value, x, y, width, height) => {
    rect(x, y, width, height, COLORS.surface);
    text(label, x + 12, y + 12, width - 24, { size: 8.5, ink: COLORS.muted });
    text(value, x + 12, y + 29, width - 24, { size: 10, weight: 'medium' });
  };

  addPage();
  // La imagen PNG está embebida en el mismo SVG usado por la ficha web.
  const logoWidth = 224;
  const logoHeight = logoWidth * logo.height / logo.width;
  page.drawImage(logo, { x: MARGIN, y: PAGE[1] - top - logoHeight, width: logoWidth, height: logoHeight });
  // El PNG del logo incluye margen transparente; alinear con su marca visible.
  text(`Descarga: ${downloadedAt(generatedAt)}`, MARGIN + 16, top + logoHeight - 10, logoWidth - 32, { size: 8, ink: COLORS.muted });
  if (empresa) {
    text('Ficha Técnica de la Empresa', 370, top, PAGE[0] - MARGIN - 370, { size: 17, weight: 'medium', align: 'right' });
    const companyKey = valueOrUnknown(empresa.clave);
    const companyKeyW = Math.min(220, tagWidth(companyKey));
    tag(companyKey, PAGE[0] - MARGIN - companyKeyW, top + 53, companyKeyW,
      { fill: COLORS.chip, ink: COLORS.ink, border: COLORS.chip, noWrap: true });
    top += 82;
    const inner = WIDTH - 36;
    const leftX = MARGIN + 18;
    const field = (label, value, x, y, width, size = 9, weight = 'medium') => {
      text(label, x, y, width, { size: 7.5, ink: COLORS.muted });
      text(value, x, y + 13, width, { size, weight });
    };
    const details = [];
    const addDetailsRow = (fields) => {
      const present = fields.filter(([, value]) => String(value ?? '').trim());
      if (!present.length) return;
      const width = (inner - (present.length - 1) * 18) / present.length;
      const cells = present.map(([label, value]) => ({ label, lines: wrap(value, fonts.medium, 9, width) }));
      const chunks = Math.ceil(Math.max(...cells.map(({ lines }) => lines.length)) / 12);
      for (let index = 0; index < chunks; index += 1) {
        const row = cells.map(({ label, lines }) => ({ label, chunk: lines.slice(index * 12, (index + 1) * 12).join('\n') }));
        const height = 13 + Math.max(...row.map(({ chunk }) => textHeight(chunk, width, 9, 'medium'))) + 12;
        details.push({ height, draw: (y) => row.forEach(({ label, chunk }, column) => {
          if (chunk) field(index ? `${label} · continuación` : label, chunk, leftX + column * (width + 18), y, width);
        }) });
      }
    };
    addDetailsRow([['Nombre de la empresa', empresa.name], ['Participación', empresa.roles?.join(' · ')], ['RFC', empresa.rfc]]);
    const addresses = empresa.addresses || [];
    for (let i = 0; i < addresses.length; i += 2) {
      addDetailsRow(addresses.slice(i, i + 2).map((address, index) => [i + index ? `Domicilio ${i + index + 1}` : 'Domicilio', address.formatted || address]));
    }
    addDetailsRow([['Teléfonos', empresa.phones?.join(' · ')], ['Sitio web', empresa.websites?.join('\n')], ['Correo', empresa.emails?.join(' · ')]]);
    const metrics = [
      ['Proyectos incluidos', String(empresa.projects?.length || 0)],
      ['Inversión identificada', `MXN $${formatNumber(empresa.projects?.reduce((sum, project) => sum + (Number(project.inversion) || 0), 0))}`],
      ['Estados', String(new Set(empresa.projects?.map((project) => project.estado).filter(Boolean)).size)],
    ];
    const metricWidth = (inner - 16) / 3;
    const metricHeight = 42;
    details.push({ height: metricHeight, draw: (y) => metrics.forEach(([label, value], index) => {
      const x = leftX + index * (metricWidth + 8);
      rect(x, y, metricWidth, metricHeight, COLORS.surface, 6);
      field(label, value, x + 10, y + 7, metricWidth - 20, 10);
    }) });
    flowSection('Información General', details, { accent: true, compact: true });

    const contactBlocks = [];
    const contacts = [...(empresa.datasetContacts || []), ...(empresa.linkedinContacts || []).map((contact) => ({ ...contact, sourceLabel: 'LinkedIn' }))];
    const contactWidth = (inner - 16) / 3;
    const safeLinkedIn = (value) => {
      try {
        const url = new URL(value);
        return /(^|\.)linkedin\.com$/i.test(url.hostname) && ['http:', 'https:'].includes(url.protocol) ? url.href : null;
      } catch { return null; }
    };
    const clippedText = (value, width, size, weight = 'regular', maxLines = 1) => {
      const lines = wrap(value || '', fonts[weight], size, width);
      if (lines.length <= maxLines) return lines.join('\n');
      const visible = lines.slice(0, maxLines);
      let last = visible.at(-1).trimEnd();
      while (last && fonts[weight].widthOfTextAtSize(`${last}...`, size) > width) last = last.slice(0, -1).trimEnd();
      visible[maxLines - 1] = `${last}...`;
      return visible.join('\n');
    };
    const contactHeight = 56;
    for (let index = 0; index < contacts.length; index += 3) {
      const row = contacts.slice(index, index + 3);
      contactBlocks.push({ height: contactHeight + 6, draw: (y) => row.forEach((contact, column) => {
        const linkedIn = safeLinkedIn(contact.url);
        const width = contactWidth - 16 - (linkedIn ? 18 : 0);
        const x = leftX + column * (contactWidth + 8);
        rect(x, y, contactWidth, contactHeight, COLORS.surface, 6);
        const name = clippedText(contact.name || 'Contacto registrado', width, 9, 'medium', 1);
        const nameHeight = Math.max(linkedIn ? 12 : 0, textHeight(name, width, 9, 'medium'));
        text(name, x + 8 + (linkedIn ? 18 : 0), y + 6, width, {
          size: 9, weight: 'medium', ink: linkedIn ? '#0A66C2' : COLORS.ink,
        });
        // Posiciones constantes: el puesto no mueve las filas ni los contactos siguientes.
        const detailWidth = contactWidth - 16;
        text(clippedText(contact.role, detailWidth, 8), x + 8, y + 21, detailWidth, { size: 8, ink: COLORS.muted });
        text(clippedText(contact.email, detailWidth, 8), x + 8, y + 32, detailWidth, { size: 8, ink: COLORS.muted });
        const phone = [contact.phone, contact.extension && `Ext. ${contact.extension}`].filter(Boolean).join(' · ');
        text(clippedText(phone, detailWidth, 8), x + 8, y + 43, detailWidth, { size: 8, ink: COLORS.muted });
        if (linkedIn) {
          const iconX = x + 8;
          rect(iconX, y + 6, 12, 12, '#0A66C2', 2);
          text('in', iconX + 1.5, y + 6, 9, { size: 8, weight: 'semiBold', ink: COLORS.white, noWrap: true });
          page.node.addAnnot(pdf.context.register(pdf.context.obj({
            Type: 'Annot', Subtype: 'Link', Rect: [x + 8, PAGE[1] - y - 6 - nameHeight, x + contactWidth - 8, PAGE[1] - y - 6],
            Contents: PDFString.of([contact.name, contact.role].filter(Boolean).join(' · ')),
            Border: [0, 0, 0], A: { Type: 'Action', S: 'URI', URI: PDFString.of(linkedIn) },
          })));
        }
      }) });
    }
    if (!contacts.length) contactBlocks.push({ height: 20, draw: (y) => text('Sin contactos registrados', leftX, y, inner, { size: 8, ink: COLORS.muted }) });
    flowSection('Contactos', contactBlocks, { compact: true });

    const projectBlocks = [];
    (empresa.projects || []).forEach((project) => {
      const contentWidth = inner - 24;
      const mainWidth = (contentWidth - 20) * 0.59;
      const contextWidth = contentWidth - mainWidth - 20;
      const investmentWidth = contentWidth * 0.28;
      const roleWidth = contentWidth * 0.34 - 20;
      const dateWidth = contentWidth * 0.19 - 20;
      const lines = [
        { value: project.clave || 'Proyecto', size: 7, weight: 'semiBold', ink: COLORS.tag, gap: 4 },
        { value: valueOrUnknown(project.proyecto), size: 10.25, weight: 'medium', ink: COLORS.ink, gap: 4 },
      ].filter((line) => line.value).flatMap((line) => {
        const wrapped = wrap(line.value, fonts[line.weight || 'regular'], line.size, mainWidth);
        return wrapped.map((value, index) => ({ ...line, value, gap: index === wrapped.length - 1 ? line.gap : 0 }));
      });
      const contextLines = [
        [project.tipoProyecto, project.sector, project.estado].filter(Boolean).join(' · '),
        project.localizacion,
      ].filter(Boolean).flatMap((value, index) => {
        const size = index === 0 ? 8 : 7.5;
        const weight = index === 0 ? 'medium' : 'regular';
        const wrapped = wrap(value, fonts[weight], size, contextWidth);
        return wrapped.map((line, lineIndex) => ({ value: line, size, weight, gap: index === 0 && lineIndex === wrapped.length - 1 ? 5 : 0 }));
      });
      const roles = wrap(project.roles?.join(' · ') || 'Sin especificar', fonts.regular, 8, roleWidth);
      const chunkCount = Math.max(Math.ceil(lines.length / 24), Math.ceil(contextLines.length / 24), Math.ceil(roles.length / 12));
      for (let part = 0; part < chunkCount; part += 1) {
        const chunk = lines.slice(part * 24, (part + 1) * 24);
        const roleChunk = roles.slice(part * 12, (part + 1) * 12).join('\n');
        const contextChunk = contextLines.slice(part * 24, (part + 1) * 24);
        const bodyHeight = Math.max(20,
          chunk.reduce((sum, line) => sum + line.size * 1.55 + line.gap, 0),
          contextChunk.reduce((sum, line) => sum + line.size * 1.55 + line.gap, 0));
        const footerHeight = 13 + Math.max(textHeight(roleChunk, roleWidth, 8, 'regular'), 17.05);
        const height = 12 + bodyHeight + 7 + footerHeight + 16 + 10;
        projectBlocks.push({ height: height + 8, draw: (y) => {
          rect(leftX, y, inner, height, COLORS.white, 8, COLORS.border);
          let valueY = y + 12;
          chunk.forEach((line) => {
            text(line.value, leftX + 12, valueY, mainWidth, { size: line.size, weight: line.weight || 'regular', noWrap: true, ink: line.ink });
            valueY += line.size * 1.55 + line.gap;
          });
          let contextY = y + 12;
          contextChunk.forEach((line) => {
            text(line.value, leftX + 12 + mainWidth + 20, contextY, contextWidth, { size: line.size, weight: line.weight, ink: COLORS.muted, align: 'right', noWrap: true });
            contextY += line.size * 1.55 + line.gap;
          });
          const footerY = y + 12 + bodyHeight + 7;
          // Un único bloque de datos evita el hueco entre la inversión y el texto.
          rect(leftX + 12, footerY, contentWidth, footerHeight + 16, COLORS.surface, 6);
          const dataY = footerY + 8;
          const investmentX = leftX + 22;
          field('Inversión · MXN', `$${formatNumber(project.inversion)}`, investmentX, dataY, investmentWidth - 20, 11, 'semiBold');
          field(part ? 'Participación · continuación' : 'Participación', roleChunk, leftX + 22 + investmentWidth, dataY, roleWidth, 8, 'regular');
          field('Publicación', formatProjectDate(project.fechaPublicacion), leftX + 22 + contentWidth * 0.62, dataY, dateWidth, 8, 'regular');
          field('Inicio probable', formatProjectDate(project.fechaInicio), leftX + 22 + contentWidth * 0.81, dataY, dateWidth, 8, 'regular');
        } });
      }
    });
    if (!projectBlocks.length) projectBlocks.push({ height: 20, draw: (y) => text('Sin proyectos asociados en esta selección', leftX, y, inner, { size: 8, ink: COLORS.muted }) });
    flowSection('Proyectos', projectBlocks, { compact: true });
    pdf.setTitle(`Ficha técnica de empresa ${companyKey} ${empresa.name}`);
    pdf.setAuthor('Bimsa Construleads');
    return targetDocument ? pdf : pdf.save();
  }
  text('Ficha Técnica del Proyecto', 400, top, PAGE[0] - MARGIN - 400, { size: 17, weight: 'medium', align: 'right' });
  text(`Fecha de publicación: ${formatProjectDate(obra.proy_fechacierre)}`, 400, top + 29, PAGE[0] - MARGIN - 400, { size: 10, ink: COLORS.muted, align: 'right' });
  const key = valueOrUnknown(obra.proy_clave);
  const projectType = cleanDisplayValue(obra.proy_tipoproyectodescripcion);
  const keyW = Math.min(150, tagWidth(key));
  const typeW = Math.min(260, tagWidth(projectType));
  tag(key, PAGE[0] - MARGIN - keyW, top + 53, keyW, { fill: COLORS.chip, ink: COLORS.ink, border: COLORS.chip, noWrap: true });
  tag(projectType, PAGE[0] - MARGIN - keyW - 8 - typeW, top + 53, typeW, {
    fill: isInvestmentProject(obra) ? INVESTMENT_PROJECT_COLOR : COLORS.accent,
    ink: COLORS.white,
    border: isInvestmentProject(obra) ? INVESTMENT_PROJECT_COLOR : COLORS.accent,
  });
  top += 100;

  const inner = WIDTH - 36;
  const leftW = (inner - 10) * 2 / 3;
  const rightW = inner - leftW - 10;
  const leftX = MARGIN + 18;
  const rightX = leftX + leftW + 10;
  const name = valueOrUnknown(obra.proy_nombre);
  const nameH = cardHeight(name, leftW);
  const dates = [
    [isExplorer ? 'Fecha estimada de Inicio' : 'Fecha inicio probable', formatProjectDate(obra.proy_fecha_inicio)],
    [isExplorer ? 'Fecha estimada de Termino' : 'Fecha término probable', formatProjectDate(obra.proy_fecha_fin)],
  ];
  const datesW = (leftW - 20) * 0.5;
  const datesValueW = Math.min((datesW - 36) * 0.44,
    Math.ceil(Math.max(...dates.map(([, value]) => fonts.medium.widthOfTextAtSize(value, 9.5)))) + 2);
  const datesLabelW = datesW - 36 - datesValueW;
  const dateRowHeights = dates.map(([label, value]) => Math.max(textHeight(label, datesLabelW, 8), textHeight(value, datesValueW, 9.5, 'medium')));
  const dateRowsH = dateRowHeights.reduce((sum, height) => sum + height, 6);
  const genreW = (leftW - 20 - datesW) / 2;
  const genreH = Math.max(60, dateRowsH + 20,
    26 + textHeight(valueOrUnknown(obra.genero), genreW - 40, 8.5, 'semiBold') + 20,
    26 + textHeight(valueOrUnknown(obra.subgenero), genreW - 40, 8.5, 'semiBold') + 20);
  const locations = isExplorer ? [
    ['Estado', valueOrUnknown(obra.esta_descripcion)], ['Municipio', valueOrUnknown(obra.muni_descripcion)],
    ['Latitud', formatProjectCoordinate(obra.latitud, 'latitude')], ['Longitud', formatProjectCoordinate(obra.longitud, 'longitude')],
  ] : [['Ubicación', formatProjectLocation(obra)]];
  const locationW = (leftW - (locations.length - 1) * 10) / locations.length;
  const locationH = Math.max(...locations.map(([, value]) => cardHeight(value, locationW)));
  const progress = getProgress(obra.porcentaje_avance ?? obra.PorcentajeAvance ?? obra.porcentajeAvance);
  const summary = [
    [isExplorer ? 'Inversión estimada' : 'Inversión', `MXN $${formatNumber(obra.proy_inversion)}`],
    [isExplorer ? 'Superficie de terreno estimada' : 'Superficie construida', Number(obra.superficie) ? `${formatNumber(obra.superficie)} m²` : 'Desconocido'],
    [isExplorer ? 'Avance de obra estimado' : 'Avance de obra', progress === null ? 'Desconocido' : `${progress.toLocaleString('es-MX')} %`],
    ['Sector', valueOrUnknown(obra.sector)], ['Tipo de obra', valueOrUnknown(obra.tipo_obra)], ['Tipo de desarrollo', valueOrUnknown(obra.desa_descripcion)],
  ];
  const labelW = (rightW - 28) * 0.44;
  const valueW = rightW - 36 - labelW;
  const summaryMetrics = summary.map(([label, value], i) => {
    const valueSize = i === 0 || i === 2 ? 9.2 : 8.7;
    const labelHeight = textHeight(label, labelW, 8.2);
    const valueHeight = textHeight(value, valueW, valueSize, 'medium');
    return { labelHeight, valueHeight, valueSize, baseHeight: Math.max(labelHeight, valueHeight) + 12 + (i === 2 ? 15 : 0) };
  });
  const leftBodyH = nameH + 10 + genreH + 10 + locationH;
  const summaryBaseH = summaryMetrics.reduce((sum, metric) => sum + metric.baseHeight, 0);
  const bodyH = Math.max(leftBodyH, summaryBaseH + 12);
  const summaryExtra = Math.max(0, bodyH - 12 - summaryBaseH) / summary.length;
  const stage = `Etapa: ${cleanDisplayValue(obra.proy_etapa)}`;
  const stageW = Math.min(350, tagWidth(stage));
  const headingH = Math.max(52, textHeight(stage, stageW - 20, 9, 'semiBold') + 38);
  const sectionY = section('Información General', headingH + bodyH + 18, true);
  tag(stage, PAGE[0] - MARGIN - 18 - stageW, sectionY + 18, stageW);
  const bodyY = sectionY + headingH;
  card('Nombre del proyecto', name, leftX, bodyY, leftW, nameH);
  const datesY = bodyY + nameH + 10;
  rect(leftX, datesY, datesW, genreH, COLORS.surface);
  let dateY = datesY + (genreH - dateRowsH) / 2;
  dates.forEach(([label, value], index) => {
    // Etiqueta y valor comparten línea base; columnas constantes en ambas filas.
    text(label, leftX + 12, dateY + 1.5, datesLabelW, { size: 8, ink: COLORS.muted });
    text(value, leftX + datesW - 12 - datesValueW, dateY, datesValueW, { size: 9.5, weight: 'medium', align: 'right' });
    dateY += dateRowHeights[index] + 6;
  });
  [['Género', obra.genero], ['Subgénero', obra.subgenero]].forEach(([label, value], index) => {
    const x = leftX + datesW + 10 + index * (genreW + 10);
    rect(x, datesY, genreW, genreH, COLORS.surface);
    text(label, x + 10, datesY + 10, genreW - 20, { size: 8.5, ink: COLORS.muted, align: 'center' });
    const content = valueOrUnknown(value);
    const width = Math.min(genreW - 20, tagWidth(content, 8.5));
    tag(content, x + (genreW - width) / 2, datesY + 26, width, { size: 8.5 });
  });
  locations.forEach(([label, value], index) => card(label, value, leftX + index * (locationW + 10), datesY + genreH + 10, locationW, locationH));
  rect(rightX, bodyY, rightW, bodyH, COLORS.surface, 12);
  let summaryY = bodyY + 6;
  summary.forEach(([label, value], index) => {
    const metric = summaryMetrics[index];
    const rowHeight = metric.baseHeight + summaryExtra;
    const rowTextY = summaryY + 8;
    text(label, rightX + 14, rowTextY, labelW, { size: 8.2, ink: COLORS.muted });
    text(value, rightX + 22 + labelW, rowTextY, valueW, { size: metric.valueSize, weight: 'medium', align: 'right' });
    if (index === 2) {
      const y = summaryY + rowHeight - 11;
      rect(rightX + 14, y, rightW - 28, 5, COLORS.border, 2.5);
      if (progress > 0) rect(rightX + 14, y, (rightW - 28) * progress / 100, 5, COLORS.accent, 2.5);
    }
    summaryY += rowHeight;
  });

  if (isExplorer) {
    const imageHeading = (y) => {
      text('Fecha de la imagen', MARGIN + WIDTH - 220, y + 15, 202, { size: 8.5, ink: COLORS.muted, align: 'right' });
      text(getExplorerImageDate(obra), MARGIN + WIDTH - 220, y + 29, 202, { size: 10, weight: 'medium', align: 'right' });
    };
    if (satellite) {
      const dimensions = satellite.scaleToFit(WIDTH - 36, 520);
      const y = section('Imagen Satelital', dimensions.height + 70);
      imageHeading(y);
      rect(leftX, y + 49, WIDTH - 36, dimensions.height + 6, COLORS.surface, 12, COLORS.border);
      page.drawImage(satellite, { x: MARGIN + (WIDTH - dimensions.width) / 2, y: PAGE[1] - y - 52 - dimensions.height, ...dimensions });
    } else {
      const y = section('Imagen Satelital', 90);
      imageHeading(y);
      text('Sin imagen disponible.', leftX, y + 52, inner, { ink: COLORS.muted });
    }
  } else {
    const companyRows = obra.cias_normalizadas || [];
    const companyBlocks = [];
    if (!companyRows.length) companyBlocks.push({
      height: 28,
      draw: (y) => text('Sin empresas registradas', leftX, y, inner, { ink: COLORS.muted }),
    });
    companyRows.forEach((company, companyIndex) => {
      if (companyIndex) companyBlocks.push({ height: 18, spacer: true, draw: () => {} });
      const companyName = valueOrUnknown(company.nombre);
      wrap(companyName, fonts.semiBold, 11, inner).forEach((line) => companyBlocks.push({
        height: 18,
        draw: (y) => text(line, leftX, y, inner, { size: 11, weight: 'semiBold', noWrap: true }),
      }));
      companyBlocks.push({ height: 8, spacer: true, draw: () => {} });
      const rows = [
        ['Rol', valueOrUnknown(company.rol)], ['Dirección', valueOrUnknown(company.direccion)],
        ...[company.telefono1, company.telefono2, company.telefono3].filter(Boolean).map((phone, i) => [i ? `Teléfono ${i + 1}` : 'Teléfono', phone]),
      ];
      const companyLabelW = 82;
      rows.forEach(([label, value]) => {
        wrap(value, fonts.regular, 9, inner - companyLabelW - 10).forEach((line, lineIndex) => companyBlocks.push({
          height: 15,
          draw: (y) => {
            if (!lineIndex) text(label, leftX, y, companyLabelW, { size: 9, ink: COLORS.muted, noWrap: true });
            text(line, leftX + companyLabelW + 10, y, inner - companyLabelW - 10, { size: 9, noWrap: true });
          },
        }));
        companyBlocks.push({ height: 5, spacer: true, draw: () => {} });
      });
      const contacts = company.contactos || [];
      companyBlocks.push({
        height: 24,
        draw: (y) => text('Contactos', leftX, y, inner, { size: 9, ink: COLORS.muted }),
      });
      if (!contacts.length) companyBlocks.push({
        height: 25,
        draw: (y) => text('Sin contactos registrados', leftX, y, inner, { ink: COLORS.muted }),
      });
      const contactW = (inner - 10) / 2;
      for (let i = 0; i < contacts.length; i += 2) {
        const row = contacts.slice(i, i + 2).map((contact) => {
          const values = [valueOrUnknown(contact.puesto), valueOrUnknown(contact.nombre), contact.email].filter(Boolean);
          return {
            values,
            height: 24 + values.reduce((sum, value, index) => sum + textHeight(value, contactW - 24, 9, index === 0 ? 'semiBold' : 'regular'), 0),
          };
        });
        const h = Math.max(...row.map((c) => c.height));
        companyBlocks.push({
          height: h + 10,
          draw: (y) => row.forEach(({ values }, column) => {
            const x = leftX + column * (contactW + 10);
            rect(x, y, contactW, h, COLORS.surface);
            let valueY = y + 12;
            values.forEach((value, index) => {
              valueY += text(value, x + 12, valueY, contactW - 24, { size: 9, weight: index === 0 ? 'semiBold' : 'regular', ink: index === 2 ? COLORS.muted : COLORS.ink });
            });
          }),
        });
      }
    });
    flowSection('Empresas', companyBlocks);
  }
  const additional = getProjectAdditional(obra);
  if (additional.length) {
    const additionalBlocks = [];
    additional.forEach(([label, value], fieldIndex) => {
      if (fieldIndex) additionalBlocks.push({ height: 10, spacer: true, draw: () => {} });
      additionalBlocks.push({
        height: 24,
        draw: (y) => text(label, leftX, y, inner, { size: 10, weight: 'semiBold' }),
      });
      wrap(value, fonts.regular, 9.5, inner).forEach((line) => additionalBlocks.push({
        height: 16,
        draw: (y) => text(line, leftX, y, inner, { ink: COLORS.muted, noWrap: true }),
      }));
    });
    flowSection('Información Adicional', additionalBlocks);
  }
  ensure(textHeight(PROJECT_PROGRESS_DISCLAIMER, WIDTH, 8.2) + 28);
  page.drawLine({ start: { x: MARGIN, y: PAGE[1] - top - 5 }, end: { x: PAGE[0] - MARGIN, y: PAGE[1] - top - 5 }, thickness: 0.7, color: color(COLORS.border) });
  text(PROJECT_PROGRESS_DISCLAIMER, MARGIN, top + 18, WIDTH, { size: 8.2, ink: COLORS.muted });
  pdf.setTitle(`Ficha técnica ${obra.proy_clave} ${name}`);
  pdf.setAuthor('Bimsa Construleads');
  return targetDocument ? pdf : pdf.save();
}

function generarFichaPdf(obra, resources) {
  return generarDocumentoFicha(obra, resources);
}

function generarFichaEmpresaPdf(empresa, resources) {
  return generarDocumentoFicha({}, resources, empresa);
}

globalThis.FichaPdf = { generarFichaPdf };
})();
