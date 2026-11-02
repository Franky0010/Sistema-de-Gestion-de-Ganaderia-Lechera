import test from 'node:test';
import assert from 'node:assert/strict';
import { validate, escapeHtml, canManage } from '../src/domain.js';
import { createApi, normalizeError } from '../src/api.js';
import { createDemoApi } from '../src/demo.js';

const animal={arete:'V-100',nombre:null,raza:'Jersey',procedencia:'Compra',fecha_ingreso:'2026-10-01',fecha_nacimiento:'2022-02-01',edad_estimada_meses:null,estado_inicial:'seco'};
test('animal: nacimiento o edad, fechas y estado de salida',()=>{
  assert.deepEqual(validate('animal',animal,'2026-11-02'),{});
  assert.ok(validate('animal',{...animal,edad_estimada_meses:12},'2026-11-02').fecha_nacimiento);
  assert.ok(validate('animal',{...animal,fecha_nacimiento:'2026-10-02'},'2026-11-02').fecha_nacimiento);
  assert.ok(validate('animal',{...animal,fecha_ingreso:'2027-01-01'},'2026-11-02').fecha_ingreso);
  assert.ok(validate('animal',{...animal,estado_inicial:'fuera_del_hato'},'2026-11-02').estado_inicial);
  assert.deepEqual(validate('animal',{...animal,fecha_nacimiento:null,edad_estimada_meses:0},'2026-11-02'),{});
});
test('usuarios: no exigir password al editar y rechazar rol inválido',()=>{
  assert.deepEqual(validate('user',{id:1,nombre:'Ana',email:'ana@test.co',rol:'administrador'}),{});
  assert.ok(validate('user',{nombre:'Ana',email:'ana@test.co',rol:'root',password:'short'}).password);
  assert.equal(canManage({rol:'operario'}),false);
  assert.equal(escapeHtml('<script>"x"</script>'),'&lt;script&gt;&quot;x&quot;&lt;/script&gt;');
});
test('API: escritura obtiene CSRF, envía cookie y no altera contraseña',async()=>{
  const calls=[];
  const api=createApi(async(url,opts)=>{
    calls.push({url,...opts});
    return new Response(JSON.stringify(url.endsWith('csrf')?{csrf_token:'secret'}:{usuario:{id:1}}),{status:200});
  });
  await api.login({email:'ana@test.co',password:' pass word '});
  assert.equal(calls.length,2);
  assert.equal(calls[0].url,'/api/v1/auth/csrf');
  assert.equal(calls[1].headers['X-CSRF-Token'],'secret');
  assert.equal(calls[1].credentials,'same-origin');
  assert.equal(JSON.parse(calls[1].body).password,' pass word ');
});
test('API: falla cerrada sin CSRF y no reintenta una escritura fallida',async()=>{
  let n=0;
  const api=createApi(async()=>{ n++; return new Response('{}',{status:200}); });
  await assert.rejects(api.logout(),{code:'CSRF_AUSENTE'});
  assert.equal(n,1);
  n=0;
  const failing=createApi(async()=>{
    n++; if(n===1) return new Response('{"csrf_token":"x"}',{status:200});
    throw new TypeError('offline');
  });
  await assert.rejects(failing.createAnimal(animal),{code:'CONEXION'});
  assert.equal(n,2);
});
test('API: logout 204 y normalización de errores FastAPI',async()=>{
  const api=createApi(async url=>url.endsWith('csrf')?new Response('{"csrf_token":"x"}'):new Response(null,{status:204}));
  assert.equal(await api.logout(),null);
  assert.equal(normalizeError(422,{detail:[{loc:['body','arete'],msg:'bad'}]}).fields.arete,'Revisa este valor.');
  assert.equal(normalizeError(409,{error:{code:'ARETE_DUPLICADO',message:'Duplicado',fields:{arete:'Otro'}}}).code,'ARETE_DUPLICADO');
});
test('demo: permisos, duplicados y conflicto de versión',async()=>{
  const api=createDemoApi();
  await api.login({email:'operario@demo.local',password:'Demo12345'});
  await assert.rejects(api.createAnimal(animal),{status:403});
  await api.login({email:'admin@demo.local',password:'Demo12345'});
  const created=await api.createAnimal(animal);
  await assert.rejects(api.createAnimal({...animal,arete:' v-100 '}),{code:'ARETE_DUPLICADO'});
  await assert.rejects(api.changeState(created.id,{estado:'en_produccion',fecha_desde:'2026-10-02',motivo:'Cambio',version:0}),{code:'VERSION_OBSOLETA'});
});
