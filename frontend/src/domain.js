export const roles = { administrador: 'Administrador', operario: 'Operario', propietario: 'Propietario' };
export const states = { en_produccion: 'En producción', seco: 'Seco', no_productivo: 'No productivo', fuera_del_hato: 'Fuera del hato' };
export const canManage = user => user?.rol === 'administrador';
export const today = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Bogota', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
export const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
export const dateLabel = value => value ? new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T12:00:00Z`)) : 'Sin fecha';

export function validate(kind, data, now = today()) {
  const errors = {};
  const required = (key, label, max) => {
    if (!String(data[key] ?? '').trim()) errors[key] = `Ingresa ${label}.`;
    else if (max && String(data[key]).length > max) errors[key] = `Usa máximo ${max} caracteres.`;
  };
  if (kind === 'login' || kind === 'user') {
    required('email', 'el correo electrónico', 254);
    if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) errors.email = 'Escribe un correo electrónico válido.';
    if (kind === 'login' || !data.id) required('password', 'la contraseña');
    if (kind === 'user') {
      required('nombre', 'el nombre completo', 120);
      if (!roles[data.rol]) errors.rol = 'Selecciona un rol.';
      if (!data.id && (data.password?.length < 8 || data.password?.length > 128)) errors.password = 'Usa entre 8 y 128 caracteres.';
    }
  }
  if (kind === 'animal') {
    required('arete', 'el arete', 40); required('raza', 'la raza', 80); required('procedencia', 'la procedencia', 160);
    if (data.nombre?.length > 120) errors.nombre = 'Usa máximo 120 caracteres.';
    required('fecha_ingreso', 'la fecha de ingreso');
    if (data.fecha_ingreso > now) errors.fecha_ingreso = 'La fecha de ingreso no puede ser futura.';
    if (Boolean(data.fecha_nacimiento) === (data.edad_estimada_meses !== null)) errors.fecha_nacimiento = 'Indica nacimiento o edad estimada, solo uno de los dos.';
    if (data.fecha_nacimiento && (data.fecha_nacimiento > now || data.fecha_nacimiento > data.fecha_ingreso)) errors.fecha_nacimiento = 'El nacimiento debe ser anterior o igual al ingreso.';
    if (data.edad_estimada_meses !== null && (!Number.isInteger(data.edad_estimada_meses) || data.edad_estimada_meses < 0)) errors.edad_estimada_meses = 'Ingresa una edad válida en meses completos.';
    if (!['en_produccion', 'seco', 'no_productivo'].includes(data.estado_inicial)) errors.estado_inicial = 'Selecciona un estado inicial válido.';
  }
  if (kind === 'state') {
    required('motivo', 'el motivo del cambio', 500); required('fecha_desde', 'la fecha efectiva');
    if (!['en_produccion', 'seco', 'no_productivo'].includes(data.estado)) errors.estado = 'Selecciona un estado productivo.';
    if (data.fecha_desde > now) errors.fecha_desde = 'La fecha efectiva no puede ser futura.';
  }
  return errors;
}
