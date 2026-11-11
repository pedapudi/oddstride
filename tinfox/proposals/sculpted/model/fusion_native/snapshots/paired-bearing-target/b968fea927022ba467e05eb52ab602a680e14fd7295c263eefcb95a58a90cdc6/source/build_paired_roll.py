"""Export a paired-bearing fit prototype without changing the migration baseline."""
import copy,hashlib,json,shutil
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import build as b
import paired_roll as design
import standard_knee as knee
from export_closed_mesh import closed_mesh
from kinematics import ROOT,LEGS

BASE=ROOT/'output/clamp-seat-work'
OUT=ROOT/'output/paired-roll-work'
OUT.mkdir(exist_ok=True)
for folder in ['step','stl']:
    shutil.copytree(BASE/folder,OUT/folder,dirs_exist_ok=True)
raw=(BASE/'model.json').read_bytes();data=json.loads(raw);exports=[]
data['parts']=[p for p in data['parts'] if not p['name'].endswith('_roll_bearing')]
originals={p['name']:copy.deepcopy(p) for p in data['parts']}

def volume(s):
    p=GProp_GProps();BRepGProp.VolumePropertiesGK_s(s.wrapped,p,1e-9,True,True)
    return p.Mass()

def export(key,s):
    assert s.isValid() and len(s.Solids())==1,key
    v=volume(s);bb=s.BoundingBox()
    step=OUT/'step'/(key+'.step');stl=OUT/'stl'/(key+'.stl')
    cq.exporters.export(s,str(step));cq.exporters.export(s,str(stl),tolerance=.07,angularTolerance=.1)
    m,check=closed_mesh(step,stl,v)
    data['meshes'][key]={'vertices':m.vertices.tolist(),'faces':m.faces.tolist()}
    restored=cq.importers.importStep(str(step)).val()
    error=abs(volume(restored)-v)
    assert restored.isValid() and len(restored.Solids())==1 and error<max(.05,v*1e-5),(key,error)
    exports.append({'part':key,'mesh':check,'volume_mm3':v,'step_volume_error_mm3':error})
    print('Export',key,round(v),flush=True)
    return dict(volume_mm3=v,com_mm=list(s.Center().toTuple()),bounds_mm=[bb.xlen,bb.ylen,bb.zlen])

def install(leg,suffix,key,s,material,group,note,mass=None):
    name=leg+'_'+suffix
    p=next((p for p in data['parts'] if p['name']==name),None)
    if p is None:
        p=copy.deepcopy(originals[leg+'_motor_carrier']);data['parts'].append(p)
    if key not in generated:generated[key]=export(key,s)
    props=generated[key]
    p.update(props,name=name,mesh=key,material=material,color=b.COLORS['plate' if material=='aluminum' else 'metal'],
             group=group,leg=leg,check=True,note=note)
    p['mass_kg']=mass if mass is not None else props['volume_mm3']*b.DENSITY[material]
    p.pop('service_role',None)

generated={}
for leg,(front,side) in LEGS.items():
    hand=lambda s:s if side>0 else s.mirror('XZ')
    keyside='_right' if side<0 else ''
    # The knee's 12 mm bearing journal remains unchanged; M5 retains the axle.
    for key,s in {**knee.parts(),'thigh_inner':knee.thigh_inner(),'thigh_outer':knee.thigh_outer()}.items():
        material='petg' if key.startswith('thigh_') else 'steel'
        install(leg,key,key+keyside,hand(s),material,'thigh',
                'M5 knee-retention fit candidate. A 12 OD x 5.5 ID x 44.6 mm steel axle uses two common 15 x 5.3 x 1.2 mm M5 large washers, an M5 x 55 button-head screw and ordinary 8 AF M5 nut. Accessible washer floors at Y49.4 and Y94.0. Fits, preload and loaded retention remain unqualified.')
    for key,s in design.custom_parts(front).items():
        suffix='roll_cartridge' if key.startswith('roll_cartridge_') else 'motor_carrier' if key.startswith('motor_carrier_') else key
        # Per-leg names remain semantic; front/rear differentiation is in mesh IDs.
        for stem in ['roll_outer_retainer','roll_inner_backplate','roll_inner_spacer','roll_outer_spacer','roll_stator_backplate','hip_stator_closure']:
            if key.startswith(stem+'_'):suffix=stem
        group='mount' if suffix in ['roll_cartridge','roll_outer_retainer','roll_outer_spacer','roll_stator_backplate'] else 'roll'
        material='aluminum'
        note='Paired 6810 support with accessible race-specific retention and a removable registered hip-stator closure. Fit prototype; printed structure, dimensional fits, endplay and loaded operation remain unqualified.'
        install(leg,suffix,key+keyside,hand(s),material,group,note)
    for i in [0,1]:
        s=design.bearing(i);s=s if front>0 else s.mirror('YZ')
        key=f'roll_bearing_6810_{front}_{i}'+keyside
        install(leg,f'roll_bearing_6810_{i}',key,hand(s),'steel','mount',
                '6810-2RS reference envelope, 50 x 65 x 7 mm; two per hip. Brand-specific ratings, grease and actual widths must be verified.',mass=.052)
    for suffix,s in design.hardware().items():
        group='mount' if suffix.startswith(('roll_retainer_','roll_stator_')) else 'roll'
        if front<0 and suffix.startswith('roll_'):s=s.mirror('YZ')
        if suffix.startswith(('carrier_closure_','hip_stator_')):s=s.translate((front*design.PARAMETERS['pitch_x_offset'],0,0))
        key=suffix+f'_front{front}'+keyside
        install(leg,suffix,key,hand(s),'steel',group,
                'Common fastener reference envelope. M3 x 25 retainer and M3 x 30 stator screws; M4 x 16 cup closure screws with ordinary nuts and washers; recessed M4 x 25 flat-head roll-output screws. Vendor blind-hole depth and final head profiles must be verified.')
    # Shift the fixed roll motor and all its connector/cable envelopes together.
    for p in data['parts']:
        if p['leg']!=leg:continue
        roll_ref=p['name']==leg+'_roll_motor' or p['name'].startswith(leg+'_roll_port_')
        hip_ref=p['name']==leg+'_hip_motor' or p['name'].startswith(leg+'_hip_port_')
        if not (roll_ref or hip_ref):continue
        old=p['mesh'];key=old+f'_paired_front{front}';dx=(-6.2 if roll_ref else design.PARAMETERS['pitch_x_offset'])*front
        if key not in data['meshes']:
            m=copy.deepcopy(data['meshes'][old])
            for vertex in m['vertices']:vertex[0]+=dx
            data['meshes'][key]=m
        p['mesh']=key;p['com_mm'][0]+=dx
        for folder in [BASE/'step',ROOT/'output/service-design/step',ROOT/'output/step-parts']:
            f=folder/(old+'.step')
            if f.exists():
                s=cq.importers.importStep(str(f)).val().translate((dx,0,0))
                cq.exporters.export(s,str(OUT/'step'/(key+'.step')))
                break

data['parameters'].update(design.PARAMETERS)
data['parameters'].update(knee.PARAMETERS)
data['status']='Paired 6810 fit prototype with a removable motor flange. Nominal geometry and assembly checks pending; not released for powered or loaded operation.'
data['source_model_sha256']=hashlib.sha256(raw).hexdigest()
used={p['mesh'] for p in data['parts']};data['meshes']={k:v for k,v in data['meshes'].items() if k in used}
encoded=json.dumps(data,separators=(',',':')).encode();stamp=hashlib.sha256(encoded).hexdigest()
(OUT/'model.json').write_bytes(encoded)
(OUT/'step-roundtrip.json').write_text(json.dumps({'model_sha256':stamp,'parts':exports},indent=2))
print('MODEL',stamp,'parts',len(data['parts']),flush=True)
