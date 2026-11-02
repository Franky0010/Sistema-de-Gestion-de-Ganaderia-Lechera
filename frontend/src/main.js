import './styles.css';
import { createApi } from './api.js';
import { canManage, escapeHtml as e, validate } from './domain.js';
import { shell, loginView, listView, animalForm, userForm, stateForm, heading } from './views.js';

const demo = __DEMO__;
const api = demo ? (await import('./demo.js')).createDemoApi() : createApi();
const app = document.querySelector('#app');
document.querySelector('.skip-link').addEventListener('click', event => {
  event.preventDefault();
  const main = document.querySelector('#main');
  main.setAttribute('tabindex', '-1');
  main.focus();
  main.scrollIntoView({ block: 'start' });
});
let user = null;
let revision = 0;
let noticeTimer;
let loginMessage = '';

function notify(message) {
  const el = document.querySelector('#notice');
  clearTimeout(noticeTimer); el.textContent = message; el.hidden = false;
  noticeTimer = setTimeout(() => { el.hidden = true; }, 6000);
}
function go(route) {
  if (location.hash === `#/${route}`) render(); else location.hash = `#/${route}`;
}
function login(message = '') {
  user = null; loginMessage = message;
  document.querySelector('dialog')?.remove();
  document.querySelector('#notice').hidden = true;
  go('login');
}
function showErrors(form, error) {
  form.querySelectorAll('[aria-invalid]').forEach(el => el.removeAttribute('aria-invalid'));
  form.querySelectorAll('.field-error').forEach(el => { el.hidden = true; el.textContent = ''; });
  const alert = document.querySelector('#form-error');
  alert.textContent = error.message || 'Revisa los campos indicados.';
  alert.hidden = false;
  for (const [name,message] of Object.entries(error.fields || {})) {
    const input = form.elements.namedItem(name);
    const hint = document.getElementById(`${name}-error`);
    if (input && !input.disabled) input.setAttribute('aria-invalid','true');
    if (hint) { hint.textContent = message; hint.hidden = false; }
  }
  const first = form.querySelector('[aria-invalid="true"]');
  (first || alert).focus();
}
function privateError(error) {
  if (error.status === 401) {
    login('Tu sesión terminó. Inicia sesión de nuevo para continuar.'); return true;
  }
  return false;
}
function bindForm(id, kind, read, save, done) {
  const form = document.getElementById(id);
  const owner = revision;
  let sending = false;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if(sending) return;
    const values = read(new FormData(form));
    const fields = validate(kind,values);
    if(Object.keys(fields).length) { showErrors(form,{fields}); return; }
    const button = form.querySelector('[type="submit"]');
    const label = button.textContent;
    sending = true; button.disabled = true; button.textContent = 'Guardando…';
    form.setAttribute('aria-busy','true');
    document.querySelector('#form-error').hidden = true;
    try {
      const result = await save(values);
      if(owner === revision) await done(result);
    } catch(error) {
      if(owner === revision && (kind==='login' || !privateError(error))) showErrors(form,error);
    } finally {
      sending = false;
      if(form.isConnected) { button.disabled=false; button.textContent=label; form.removeAttribute('aria-busy'); }
    }
  });
}
const text = (form,key) => String(form.get(key) ?? '').trim();

function bindLogin() {
  document.querySelector('#show-password').addEventListener('click',event=>{
    const field=document.querySelector('#password');
    const visible=field.type === 'password'; field.type=visible?'text':'password';
    event.currentTarget.textContent=visible?'Ocultar':'Mostrar';
    event.currentTarget.setAttribute('aria-pressed',String(visible));
  });
  document.querySelectorAll('[data-demo]').forEach(button=>button.addEventListener('click',()=>{
    document.querySelector('#email').value=`${button.dataset.demo}@demo.local`;
    document.querySelector('#password').value='Demo12345';
    document.querySelector('#login-form [type="submit"]').focus();
  }));
  bindForm('login-form','login',form=>({email:text(form,'email').toLowerCase(),password:String(form.get('password') || '')}),api.login, result=>{
    user=result.usuario; document.querySelector('#password').value=''; loginMessage=''; go('animales');
  });
}

async function deactivate(id,name) {
  const owner=revision;
  const dialog=document.createElement('dialog');
  dialog.setAttribute('aria-labelledby','confirm-title');
  dialog.innerHTML=`<h2 id="confirm-title">¿Desactivar esta cuenta?</h2><p>${e(name)} ya no podrá iniciar sesión. Su historial se conservará.</p><div class="alert" id="dialog-error" role="alert" hidden></div><div class="dialog-actions"><button class="btn btn-secondary" id="cancel-deactivate" autofocus>Cancelar</button><button class="btn btn-danger" id="confirm-deactivate">Desactivar cuenta</button></div>`;
  document.body.append(dialog); dialog.showModal();
  let busy=false;
  dialog.addEventListener('cancel',event=>{ if(busy) event.preventDefault(); });
  dialog.addEventListener('close',()=>dialog.remove());
  dialog.querySelector('#cancel-deactivate').onclick=()=>dialog.close();
  dialog.querySelector('#confirm-deactivate').onclick=async()=>{
    if(busy) return; busy=true;
    dialog.querySelectorAll('button').forEach(b=>b.disabled=true);
    try {
      await api.updateUser(id,{activo:false});
      if(owner!==revision) return;
      dialog.close();
      if(Number(id)===user.id) { login('Tu cuenta fue desactivada. Contacta al administrador.'); return; }
      notify('Cuenta desactivada. El historial se conserva.'); await render();
    } catch(error) {
      if(owner===revision && !privateError(error)) { const alert=dialog.querySelector('#dialog-error'); alert.textContent=error.message; alert.hidden=false; }
    } finally { busy=false; dialog.querySelectorAll('button').forEach(b=>b.disabled=false); }
  };
}

async function render() {
  const owner=++revision;
  document.querySelector('dialog')?.remove();
  const full=location.hash.replace(/^#\/?/,'') || 'animales';
  const [route,query='']=full.split('?');
  if(!user || route==='login') {
    if(user) { go('animales'); return; }
    app.innerHTML=loginView(demo,loginMessage); document.title='Acceder · Ganadería lechera'; bindLogin(); return;
  }
  app.innerHTML=shell(user,route,demo);
  document.querySelector('#logout').onclick=async event=>{
    const button=event.currentTarget; button.disabled=true;
    try { await api.logout(); login('Sesión cerrada correctamente.'); }
    catch(error) { if(!privateError(error)) notify(error.message); }
    finally { if(button.isConnected) button.disabled=false; }
  };
  const main=document.querySelector('#main');
  const adminRoute=route.startsWith('usuarios') || route==='animales/nuevo' || /^animales\/\d+\/estado$/.test(route);
  if(adminRoute && !canManage(user)) {
    main.innerHTML=`${heading('Acceso restringido','Esta función está disponible para el administrador.')}<a class="btn btn-secondary" href="#/animales">Volver a animales</a>`;
    return;
  }
  try {
    if(route==='animales' || route==='usuarios') {
      const q=new URLSearchParams(query);
      const params={search:q.get('search') || '',estado:q.get('estado') || '',page:Math.max(1,Number.parseInt(q.get('page'),10)||1),page_size:20};
      const data=await (route==='animales'?api.animals(params):api.users(params));
      if(owner!==revision) return;
      main.innerHTML=listView(route,data,params,user);
      const navigate = values => go(`${route}?${new URLSearchParams(values)}`);
      document.querySelector('#filters').onsubmit=event=>{ event.preventDefault(); const form=new FormData(event.currentTarget); navigate({search:text(form,'search'),estado:text(form,'estado'),page:1}); };
      document.querySelector('#filter-state')?.addEventListener('change',()=>document.querySelector('#filters').requestSubmit());
      document.querySelectorAll('[data-page]').forEach(button=>button.onclick=()=>navigate({...params,page:button.dataset.page}));
      document.querySelectorAll('[data-deactivate]').forEach(button=>button.onclick=()=>deactivate(button.dataset.deactivate,button.dataset.name));
    } else if(route==='animales/nuevo') {
      main.innerHTML=animalForm();
      document.querySelector('#age-mode').onchange=event=>{
        const byDate=event.target.value==='fecha';
        document.querySelector('#birth-field').hidden=!byDate;
        document.querySelector('#age-field').hidden=byDate;
        document.querySelector('#fecha_nacimiento').disabled=!byDate;
        document.querySelector('#edad_estimada_meses').disabled=byDate;
      };
      bindForm('animal-form','animal',form=>({arete:text(form,'arete').toUpperCase(),nombre:text(form,'nombre')||null,raza:text(form,'raza'),procedencia:text(form,'procedencia'),fecha_ingreso:text(form,'fecha_ingreso'),fecha_nacimiento:form.get('age-mode')==='fecha'?text(form,'fecha_nacimiento')||null:null,edad_estimada_meses:form.get('age-mode')==='edad'?(text(form,'edad_estimada_meses')===''?NaN:Number(form.get('edad_estimada_meses'))):null,estado_inicial:text(form,'estado_inicial')}),api.createAnimal,result=>{ notify(`${result.arete} se registró correctamente.`); go('animales'); });
    } else if(route==='usuarios/nuevo' || /^usuarios\/\d+\/editar$/.test(route)) {
      const record=route==='usuarios/nuevo'?null:await api.user(Number(route.split('/')[1]));
      if(owner!==revision) return;
      main.innerHTML=userForm(record);
      bindForm('user-form','user',form=>({...(record?{id:record.id}:{}),nombre:text(form,'nombre'),email:text(form,'email').toLowerCase(),rol:text(form,'rol'),...(!record?{password:String(form.get('password')||'')}:{})}),values=>{
        const {id,...payload}=values; return record?api.updateUser(id,payload):api.createUser(payload);
      },result=>{
        if(record?.id===user.id) { user=result; }
        notify(record?'Los datos del usuario se actualizaron.':'Usuario creado correctamente.'); go(canManage(user)?'usuarios':'animales');
      });
    } else if(/^animales\/\d+\/estado$/.test(route)) {
      const animal=await api.animal(Number(route.split('/')[1]));
      if(owner!==revision) return;
      if(animal.estado_actual==='fuera_del_hato') {
        main.innerHTML=`${heading('Animal fuera del hato','Su historial se conserva. No puedes modificar su estado productivo.')}<a class="btn btn-secondary" href="#/animales">Volver a animales</a>`; return;
      }
      main.innerHTML=stateForm(animal);
      bindForm('state-form','state',form=>({estado:text(form,'estado'),fecha_desde:text(form,'fecha_desde'),motivo:text(form,'motivo'),version:animal.version}),values=>api.changeState(animal.id,values),()=>{ notify(`El cambio de estado de ${animal.arete} se guardó.`); go('animales'); });
    } else {
      main.innerHTML=`${heading('Esta página no existe','Regresa al listado para continuar.')}<a class="btn btn-secondary" href="#/animales">Volver a animales</a>`;
    }
    document.title=`${main.querySelector('h1')?.textContent || 'Gestión'} · Ganadería lechera`;
    main.querySelector('h1')?.focus({preventScroll:true});
  } catch(error) {
    if(owner!==revision || privateError(error)) return;
    main.innerHTML=`<div class="empty"><h1>No pudimos cargar la información</h1><p class="mt-4" role="alert">${e(error.message)}</p><button class="btn btn-secondary" id="retry">Volver a intentar</button><a class="btn btn-quiet" href="#/animales">Volver a animales</a></div>`;
    document.querySelector('#retry').onclick=render;
  }
}

window.addEventListener('hashchange',render);
try { user=(await api.session()).usuario; }
catch(error) { if(error.status!==401) loginMessage=error.message; }
await render();
