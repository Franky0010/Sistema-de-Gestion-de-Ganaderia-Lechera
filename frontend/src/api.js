export class ApiError extends Error {
  constructor(status, code, message, fields = {}) {
    super(message); this.status = status; this.code = code; this.fields = fields;
  }
}

export function normalizeError(status, body) {
  if (body?.error) return new ApiError(status, body.error.code, body.error.message || 'No se pudo completar la operación.', body.error.fields || {});
  if (Array.isArray(body?.detail)) {
    const fields = {};
    for (const item of body.detail) fields[item.loc?.at(-1)] = 'Revisa este valor.';
    return new ApiError(status, 'VALIDACION', 'Revisa los campos indicados.', fields);
  }
  const fallback = status === 401 ? 'La sesión terminó. Inicia sesión de nuevo.' : status === 403 ? 'No tienes permiso para realizar esta acción.' : status === 404 ? 'No se encontró el recurso. Si estás integrando la API, verifica que la ruta esté implementada.' : status === 429 ? 'Demasiados intentos. Espera un momento antes de volver a intentar.' : 'No se pudo completar la operación. Intenta de nuevo.';
  return new ApiError(status, 'HTTP_ERROR', typeof body?.detail === 'string' ? body.detail : fallback);
}

export function createApi(fetcher = fetch) {
  async function request(path, method = 'GET', data, csrf) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const headers = { Accept: 'application/json' };
      if (data !== undefined) headers['Content-Type'] = 'application/json';
      if (csrf) headers['X-CSRF-Token'] = csrf;
      const response = await fetcher(`/api/v1${path}`, { method, headers, credentials: 'same-origin', cache: 'no-store', signal: controller.signal, ...(data === undefined ? {} : { body: JSON.stringify(data) }) });
      if (response.status === 204) return null;
      const body = await response.json().catch(() => null);
      if (!response.ok) throw normalizeError(response.status, body);
      if (!body) throw new ApiError(502, 'RESPUESTA_INVALIDA', 'El servidor devolvió una respuesta inesperada.');
      return body;
    } catch (error) {
      if (error instanceof ApiError) throw error;
      throw new ApiError(0, 'CONEXION', method === 'GET' ? 'No pudimos conectar con el servidor. Comprueba tu conexión e intenta de nuevo.' : 'No recibimos confirmación del servidor. Comprueba el registro antes de repetir para evitar duplicados.');
    } finally { clearTimeout(timeout); }
  }
  async function write(path, method, data) {
    const { csrf_token } = await request('/auth/csrf');
    if (!csrf_token) throw new ApiError(502, 'CSRF_AUSENTE', 'No se pudo preparar una solicitud segura. Vuelve a intentar.');
    return request(path, method, data, csrf_token);
  }
  const query = values => new URLSearchParams(Object.entries(values).filter(([,v]) => v !== '' && v != null)).toString();
  return {
    session: () => request('/auth/session'),
    login: data => write('/auth/login', 'POST', data),
    logout: () => write('/auth/logout', 'POST'),
    animals: params => request(`/animales?${query(params)}`),
    animal: id => request(`/animales/${id}`),
    createAnimal: data => write('/animales', 'POST', data),
    changeState: (id, data) => write(`/animales/${id}/estados`, 'POST', data),
    users: params => request(`/usuarios?${query(params)}`),
    user: id => request(`/usuarios/${id}`),
    createUser: data => write('/usuarios', 'POST', data),
    updateUser: (id, data) => write(`/usuarios/${id}`, 'PATCH', data),
  };
}
