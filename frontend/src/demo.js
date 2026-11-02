// Solo se incluye en modo `demo`. Datos sintéticos en memoria; recargar los reinicia.
import { ApiError } from './api.js';
import { today, validate } from './domain.js';

export function createDemoApi() {
  let current = null;
  const users = [
    { id: 1, nombre: 'Ana Martínez', email: 'admin@demo.local', rol: 'administrador', activo: true },
    { id: 2, nombre: 'Carlos Restrepo', email: 'operario@demo.local', rol: 'operario', activo: true },
    { id: 3, nombre: 'María López', email: 'propietario@demo.local', rol: 'propietario', activo: true },
    { id: 4, nombre: 'Luis Torres', email: 'inactivo@demo.local', rol: 'operario', activo: false },
  ];
  const passwords = new Map(users.map(user => [user.id, 'Demo12345']));
  const animals = [
    ['V-001','Luna','Holstein','en_produccion'], ['V-002','Estrella','Jersey','seco'],
    ['V-003','Lucero','Holstein','en_produccion'], ['V-004','Aurora','Normando','en_produccion'],
    ['V-005','Almendra','Jersey','no_productivo'], ['V-006','Brisa','Holstein','seco'],
    ['V-007','Canela','Jersey','en_produccion'], ['V-008','Oliva','Normando','fuera_del_hato'],
  ].map(([arete,nombre,raza,estado_actual], i) => ({ id: i+1, arete,nombre,raza,estado_actual,procedencia:'Nacimiento en finca',fecha_ingreso:'2022-06-15',fecha_nacimiento:'2021-09-10',edad_estimada_meses:null,estado_desde:'2025-09-01',version:1 }));
  const dates = new Map(animals.map(a => [a.id, new Set([a.fecha_ingreso,a.estado_desde])]));
  const fail = (status, code, message, fields) => { throw new ApiError(status, code, message, fields); };
  const ensure = (admin = false) => {
    if (!current || !users.find(u => u.id === current.id)?.activo) fail(401,'SESION_EXPIRADA','Tu sesión terminó. Vuelve a ingresar.');
    current = users.find(u => u.id === current.id);
    if (admin && current.rol !== 'administrador') fail(403,'SIN_PERMISO','Esta acción está reservada al administrador.');
  };
  const check = (kind,data) => { const fields=validate(kind,data); if(Object.keys(fields).length) fail(422,'VALIDACION','Revisa los campos indicados.',fields); };
  const find = (list,id) => list.find(item => item.id === Number(id)) || fail(404,'NO_ENCONTRADO','No encontramos este registro.');
  const list = (rows, {search='', estado='',page=1,page_size=20}={}) => {
    const filtered = rows.filter(row => (!estado || row.estado_actual === estado) && `${row.arete || ''} ${row.nombre} ${row.email || ''}`.toLowerCase().includes(search.toLowerCase()));
    return {items:structuredClone(filtered.slice((page-1)*page_size,page*page_size)),total:filtered.length,page:Number(page),page_size:Number(page_size)};
  };
  const api = {
    session() { ensure(); return {usuario:{...current}}; },
    login(data) {
      const user=users.find(u => u.email === data.email.trim().toLowerCase());
      if (!user || passwords.get(user.id) !== data.password) fail(401,'CREDENCIALES_INVALIDAS','Correo o contraseña incorrectos.');
      if (!user.activo) fail(403,'CUENTA_INACTIVA','Tu cuenta está inactiva. Contacta al administrador.');
      current=user; return {usuario:{...user}};
    },
    logout() { current=null; return null; },
    animals(params) { ensure(); return list(animals,params); },
    animal(id) { ensure(); return {...find(animals,id)}; },
    users(params) { ensure(true); return list(users,params); },
    user(id) { ensure(true); return {...find(users,id)}; },
    createUser(data) {
      ensure(true); check('user',data);
      if(users.some(u=>u.email.toLowerCase()===data.email.toLowerCase())) fail(409,'EMAIL_DUPLICADO','Ese correo ya está registrado.',{email:'Usa otro correo.'});
      const user={id:Math.max(...users.map(u=>u.id))+1,nombre:data.nombre,email:data.email,rol:data.rol,activo:true};
      users.push(user); passwords.set(user.id,data.password); return {...user};
    },
    updateUser(id,data) {
      ensure(true); const user=find(users,id); check('user',{...user,...data});
      if(data.email && users.some(u=>u.id!==user.id && u.email.toLowerCase()===data.email.toLowerCase())) fail(409,'EMAIL_DUPLICADO','Ese correo ya está registrado.',{email:'Usa otro correo.'});
      Object.assign(user,data); return {...user};
    },
    createAnimal(data) {
      ensure(true); check('animal',data);
      const arete=data.arete.trim().toUpperCase();
      if(animals.some(a=>a.arete===arete)) fail(409,'ARETE_DUPLICADO','Ese arete ya está registrado.',{arete:'El arete no se puede repetir ni reutilizar.'});
      const {estado_inicial,...rest}=data;
      const animal={...rest,id:Math.max(0,...animals.map(a=>a.id))+1,arete,estado_actual:estado_inicial,estado_desde:data.fecha_ingreso,version:1};
      animals.push(animal); dates.set(animal.id,new Set([data.fecha_ingreso])); return {...animal};
    },
    changeState(id,data) {
      ensure(true); check('state',data); const animal=find(animals,id);
      if(data.version!==animal.version) fail(409,'VERSION_OBSOLETA','El registro cambió. Vuelve a abrir el formulario.');
      if(animal.estado_actual==='fuera_del_hato') fail(409,'ESTADO_INCOMPATIBLE','Este animal ya salió del hato.');
      if(data.fecha_desde<animal.fecha_ingreso) fail(422,'VALIDACION','Revisa la fecha.',{fecha_desde:'No puede ser anterior al ingreso.'});
      if(dates.get(animal.id).has(data.fecha_desde)) fail(409,'CAMBIO_DIARIO_DUPLICADO','Ya existe un cambio en esa fecha.',{fecha_desde:'Selecciona otra fecha.'});
      if(data.estado===animal.estado_actual && data.fecha_desde>=animal.estado_desde) fail(409,'ESTADO_INCOMPATIBLE','El animal ya tiene ese estado.',{estado:'Selecciona un estado distinto.'});
      dates.get(animal.id).add(data.fecha_desde);
      if(data.fecha_desde>=animal.estado_desde) { animal.estado_actual=data.estado; animal.estado_desde=data.fecha_desde; }
      animal.version++; return {animal:{...animal},estado:{...data,animal_id:animal.id,id:animal.version,responsable_id:current.id}};
    },
  };
  return Object.fromEntries(Object.entries(api).map(([key,fn])=>[key,async(...args)=>{
    await new Promise(resolve=>setTimeout(resolve,180));
    return fn(...args);
  }]));
}
