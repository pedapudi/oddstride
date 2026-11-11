import * as THREE from 'three';
import { OrbitControls } from 'three/addons/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/RoomEnvironment.js';
const data=await fetch('./model.json').then(r=>r.json());
const P=data.parameters, D=Math.PI/180;
const individualParts=new Map();
fetch('../output/parts-catalog.json').then(r=>r.json()).then(r=>r.parts.forEach(p=>individualParts.set(p.id,p)));
fetch('../output/engineering.json').then(r=>r.json()).then(r=>{document.querySelector('#mass-summary').textContent=`Estimated base: ${r.mass.base_kg.toFixed(2)} kg including compact batteries and peripherals. Cargo adds 1 kg. Weight target: 10 kg.`;}).catch(()=>{});
let poses=structuredClone(data.poses.stand), selected='FR', view='exterior', explode=0, open=false, collisionIds=new Set();
let rollDemo=false,demoStart=0,demoLast=0,demoCheck=0;
const viewport=document.querySelector('#viewport'), scene=new THREE.Scene();
scene.background=new THREE.Color('#eeeee7');scene.fog=new THREE.Fog('#eeeee7',1700,4200);
const camera=new THREE.PerspectiveCamera(35,1,1,6000);camera.up.set(0,0,1);
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.shadowMap.enabled=true;renderer.shadowMap.autoUpdate=false;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=.95;
const pmrem=new THREE.PMREMGenerator(renderer);scene.environment=pmrem.fromScene(new RoomEnvironment(),.04).texture;
viewport.append(renderer.domElement);const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.maxPolarAngle=Math.PI*.96;controls.minDistance=150;controls.maxDistance=2500;
scene.add(new THREE.HemisphereLight('#fffdf3','#9baba0',1.3));
function light(color,power,pos){const l=new THREE.DirectionalLight(color,power);l.position.set(...pos);scene.add(l);return l;}
const key=light('#fff3de',2.3,[-200,-500,900]);key.castShadow=true;key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-600,right:600,top:600,bottom:-600,near:1,far:2000});key.shadow.bias=-.0003;key.shadow.normalBias=.5;key.shadow.radius=5;
light('#e5f0ff',1.5,[500,400,500]);light('#fffdf7',1.2,[-500,600,300]);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(8000,8000),new THREE.MeshStandardMaterial({color:'#e1e3d9',roughness:1}));floor.position.z=-320;floor.receiveShadow=true;scene.add(floor);
const rollAxis=new THREE.ArrowHelper(new THREE.Vector3(1,0,0),new THREE.Vector3(),105,0x249ed2,10,5);
const pitchAxis=new THREE.ArrowHelper(new THREE.Vector3(0,1,0),new THREE.Vector3(),105,0xf37735,10,5);
scene.add(rollAxis,pitchAxis);
const robot=new THREE.Group();scene.add(robot);const geometries={},objects=[];
for(const [id,m] of Object.entries(data.meshes)){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(m.vertices.flat(),3));g.setIndex(m.faces.flat());g.computeVertexNormals();geometries[id]=g;}
for(const part of data.parts){const metal=['aluminum','steel'].includes(part.material);const mat=new THREE.MeshStandardMaterial({color:part.color,metalness:metal?.55:.07,roughness:metal?.36:.54});const mesh=new THREE.Mesh(geometries[part.mesh],mat);mesh.castShadow=true;mesh.receiveShadow=true;mesh.matrixAutoUpdate=false;mesh.userData=part;objects.push(mesh);robot.add(mesh);}
// Small graphics on the shell retain the quiet hierarchy of the exterior study.
function label(text,w,h){const c=document.createElement('canvas');c.width=1024;c.height=256;const ctx=c.getContext('2d');ctx.clearRect(0,0,1024,256);ctx.fillStyle='#414b3e';ctx.font='100px Arial';ctx.fillText(text,30,155);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({map:t,transparent:true,depthWrite:false,side:THREE.DoubleSide}));}
const brand=label('tinfox      01',145,36);brand.rotation.x=Math.PI/2;brand.position.set(0,-P.body_width/2-.3,14);
const discLabels=[];
function T(x=0,y=0,z=0){return new THREE.Matrix4().makeTranslation(x,y,z)}
function R(axis,a){return axis==='x'?new THREE.Matrix4().makeRotationX(a*D):new THREE.Matrix4().makeRotationY(a*D)}
function frames(leg){const side=leg.endsWith('L')?1:-1,front=leg.startsWith('F')?1:-1,[r,h,k]=poses[leg];const roll=T(front*P.hip_x,side*P.roll_y,0).multiply(R('x',side*r));const thigh=roll.clone().multiply(T(0,side*P.pitch_offset,0)).multiply(R('y',h));const knee=thigh.clone().multiply(T(0,0,-P.thigh)).multiply(R('y',k));const a=(k+P.crank_phase_deg)*D;return{mount:T(front*P.hip_x,side*P.roll_y,0),roll,thigh,knee,crank:thigh.clone().multiply(R('y',k+P.crank_phase_deg)),rod:thigh.clone().multiply(T(P.crank_radius*Math.cos(a),0,-P.crank_radius*Math.sin(a)))};}
function update(){const fs=Object.fromEntries(Object.keys(poses).map(l=>[l,frames(l)]));let low=Infinity;
for(const obj of objects){const p=obj.userData;obj.matrix.copy(p.leg?fs[p.leg][p.group]:new THREE.Matrix4());
 const side=p.leg?.endsWith('L')?1:-1;const focus=p.leg===selected;const hide=focus&&open&&(p.name.includes('thigh_outer')||p.name.includes('hip_disc'));
 obj.visible=!hide&&(view!=='section'||!p.leg||focus);if(view==='section'&&!p.leg)obj.visible=false;
 if(p.material==='fabric'&&Object.values(poses).some(q=>Math.abs(q[0])>5))obj.visible=false;
 if(focus&&explode>0){let delta=0;if(p.name.includes('thigh_outer')||p.name.includes('hip_disc'))delta=explode*1.15;if(p.name.includes('thigh_inner'))delta=-explode*.5;if(p.name.includes('shin_outer'))delta=explode*.4;obj.matrix.multiply(T(0,side*delta,0));}
 obj.material.color.set(collisionIds.has(p.name)?'#d95928':p.color);obj.material.emissive.set(collisionIds.has(p.name)?'#3c1305':'#000000');obj.matrixWorldNeedsUpdate=true;
 if(p.name.endsWith('_foot')){const pos=new THREE.Vector3(0,side*P.shin_y,-P.shank_to_foot_center).applyMatrix4(fs[p.leg].knee);low=Math.min(low,pos.z-P.foot_radius);}}
 for(const {leg,side,mesh} of discLabels){mesh.matrix.copy(fs[leg].thigh).multiply(T(0,side*(P.cap_y+.15+(leg===selected?explode*1.15:0)),0)).multiply(R('x',-side*90));mesh.visible=(view!=='section'||leg===selected)&&!(open&&leg===selected);mesh.matrixWorldNeedsUpdate=true;}
 const origin=new THREE.Vector3().setFromMatrixPosition(fs[selected].roll);
 rollAxis.position.copy(origin);pitchAxis.position.copy(origin);
 const side=selected.endsWith('L')?1:-1;pitchAxis.setDirection(new THREE.Vector3(0,side,0).transformDirection(fs[selected].roll));
 rollAxis.visible=pitchAxis.visible=document.querySelector('#show-axes').checked;
 floor.position.z=low-.3;brand.visible=view!=='section';renderer.shadowMap.needsUpdate=true;syncControls();}
function cameraHome(){if(view==='section'){const front=selected.startsWith('F')?1:-1,side=selected.endsWith('L')?1:-1;controls.target.set(front*P.hip_x,side*P.roll_y,-95);camera.position.set(front*P.hip_x+280,side*650,130);}else if(view==='underside'){controls.target.set(0,0,-30);camera.position.set(600,-700,-430);floor.visible=false;}else{controls.target.set(0,0,-95);camera.position.set(650,-1000,310);floor.visible=true;}controls.update();}
const names=['Hip roll','Hip pitch','Knee pitch'];const controlNode=document.querySelector('#joint-controls');
for(let i=0;i<3;i++){const div=document.createElement('div');div.className='joint';div.innerHTML=`<label>${names[i]}<output id="q${i}-value"></output></label><input aria-label="${names[i]}" id="q${i}" type="range" step="1"><div class="bounds"><span id="q${i}-min"></span><span id="q${i}-max"></span></div>`;controlNode.append(div);div.querySelector('input').addEventListener('input',e=>{stopDemo();const value=Number(e.target.value);for(const leg of document.querySelector('#all-legs').checked?Object.keys(poses):[selected]){const lim=P.joint_limits_deg[i===0?'roll':i===2?'knee':leg.startsWith('F')?'hip_front':'hip_rear'];poses[leg][i]=Math.max(lim[0],Math.min(lim[1],value));}document.querySelector('#pose').value='';update();scheduleCheck();});}
function syncControls(){const lim=P.joint_limits_deg;const limits=[lim.roll,selected.startsWith('F')?lim.hip_front:lim.hip_rear,lim.knee];for(let i=0;i<3;i++){const input=document.querySelector(`#q${i}`);input.min=limits[i][0];input.max=limits[i][1];input.value=poses[selected][i];document.querySelector(`#q${i}-value`).textContent=poses[selected][i]+'°';document.querySelector(`#q${i}-min`).textContent=limits[i][0]+'°';document.querySelector(`#q${i}-max`).textContent=limits[i][1]+'°';}}
let timer,request=0;function scheduleCheck(){request++;clearTimeout(timer);timer=setTimeout(check,160);}
async function check(){const n=++request;const status=document.querySelector('#collision');try{const r=await fetch('/api/collision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({poses})}).then(r=>{if(!r.ok)throw Error(r.status);return r.json()});if(n!==request)return;collisionIds=new Set(r.pairs.flat());status.classList.toggle('bad',r.collision);status.querySelector('strong').textContent=r.collision?`${r.pairs.length} interference pair${r.pairs.length===1?'':'s'}`:'No rigid-mesh intersections';status.querySelector('p').textContent=r.collision?'Adjust the pose; highlighted parts intersect.':'This pose only. Clearances and loads need separate checks.';document.querySelector('#pairs').textContent=r.pairs.slice(0,8).map(p=>p.join(' ↔ ')).join('\n');window.lastCollision=r;update();}catch(e){status.classList.add('bad');status.querySelector('strong').textContent='Collision service unavailable';status.querySelector('p').textContent='Run the supplied local review server.';}}
document.querySelectorAll('[data-leg]').forEach(b=>b.addEventListener('click',()=>{stopDemo();selected=b.dataset.leg;document.querySelectorAll('[data-leg]').forEach(x=>x.classList.toggle('active',x===b));document.querySelector('#leglabel').textContent={FR:'RIGHT FRONT',FL:'LEFT FRONT',RR:'RIGHT REAR',RL:'LEFT REAR'}[selected];update();if(view==='section')cameraHome();}));
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{view=b.dataset.view;open=view==='section';document.querySelector('#open-shell').checked=open;document.querySelectorAll('[data-view]').forEach(x=>x.classList.toggle('active',x===b));update();cameraHome();}));
document.querySelector('#pose').addEventListener('change',e=>{stopDemo();poses=structuredClone(data.poses[e.target.value]);update();check();});
document.querySelector('#open-shell').addEventListener('change',e=>{open=e.target.checked;update();});
document.querySelector('#explode').addEventListener('input',e=>{explode=Number(e.target.value);document.querySelector('#explode-value').textContent=explode+'%';update();});
function stopDemo(){rollDemo=false;document.querySelector('#roll-demo').classList.remove('active');document.querySelector('#roll-demo').textContent='Demonstrate hip roll';}
document.querySelector('#show-axes').addEventListener('change',update);
document.querySelector('#roll-demo').addEventListener('click',()=>{if(rollDemo){stopDemo();check();return;}poses=structuredClone(data.poses.stand);rollDemo=true;demoStart=performance.now();demoLast=demoCheck=0;document.querySelector('#show-axes').checked=true;document.querySelector('#roll-demo').classList.add('active');document.querySelector('#roll-demo').textContent='Stop hip roll demonstration';document.querySelector('#pose').value='';update();});
document.querySelector('#reset-camera').addEventListener('click',cameraHome);
const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();let down;renderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>4)return;const rect=renderer.domElement.getBoundingClientRect();mouse.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(mouse,camera);const hit=ray.intersectObjects(objects.filter(x=>x.visible))[0];if(!hit)return;const p=hit.object.userData;document.querySelector('#selection').textContent=p.name.replaceAll('_',' ');const info=document.querySelector('#part-info');info.hidden=false;info.textContent=`${p.name.replaceAll('_',' ')} · ${p.material} · ${(p.mass_kg*1000).toFixed(0)} g${p.note?' · '+p.note:''}`;const part=individualParts.get(p.mesh);if(part){info.append(document.createElement('br'));for(const [label,url] of [['Inspect this part',`parts.html#${encodeURIComponent(p.mesh)}`],['Download STEP',`../output/${part.step}`]]){const a=document.createElement('a');a.textContent=label;a.href=url;a.target='_blank';a.style.marginRight='16px';info.append(a);}}});
function resize(){const w=viewport.clientWidth,h=viewport.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();}new ResizeObserver(resize).observe(viewport);
update();cameraHome();resize();check();document.querySelector('#loading').remove();
window.tinfox={data,get poses(){return poses},setPose(q){poses=structuredClone(q);update();return check();},setView(v){document.querySelector(`[data-view="${v}"]`).click();},renderer,scene,camera,objects};
function tick(){requestAnimationFrame(tick);const now=performance.now();if(rollDemo&&now-demoLast>65){poses[selected][0]=Math.round(20*Math.sin((now-demoStart)/1300));demoLast=now;update();if(now-demoCheck>1000){demoCheck=now;check();}}controls.update();renderer.render(scene,camera);}tick();
