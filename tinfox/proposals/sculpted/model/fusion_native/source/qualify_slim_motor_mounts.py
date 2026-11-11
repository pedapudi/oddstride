"""Add linked handed mounts and test structural edits independently of vendor fits."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/n).read_text() for n in ['native_documents.py','intent_geometry.py'])+'''
def run(_context: str):
 import json,time,tempfile,os,math
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();assert doc.dataFile.versionNumber==14;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();tick=time.monotonic();parts={key:next(c for c in d.allComponents if c.partNumber=='CANDIDATE_sl_'+key)for key in ['hip_hub','motor_mount_ring']};g=IntentGeometry(d,parts['hip_hub']);definitions={'sm_stator_mount_plane':53.5,'sm_fastener_diametral_compensation':0,'sm_output_hole_diametral_compensation':0,'sm_output_head_diametral_compensation':0,'sm_hub_head_nominal_radius':3.8,'sm_tube_outer_diameter':5,'sm_tube_inner_diameter':3.4,'sm_upper_tube_end_y':61,'sm_lower_tube_start_y':'sm_hub_pad_y+sm_hub_tie_pad_thickness','sm_lower_tube_length':'sm_stator_base_y-sm_lower_tube_start_y','sm_upper_tube_start_y':'sm_stator_pad_y+sm_stator_pad_thickness','sm_upper_tube_length':'sm_upper_tube_end_y-sm_upper_tube_start_y'}
 for name,value in definitions.items():g.parameter(name,value,comment='Independent hardware or structural stack datum. Zero compensation reproduces the reference and is not a manufacturing fit recommendation.')
 bindings={'sm_stator_base_y':'sm_stator_mount_plane-sm_stator_thickness','sm_stator_hole_radius':'lc_carrier_stator_hole+sm_fastener_diametral_compensation/2','sm_tie_hole_radius':'lc_carrier_stator_hole+sm_fastener_diametral_compensation/2','sm_output_hole_radius':'lc_rs02_output_hole_radius+sm_output_hole_diametral_compensation/2','sm_hub_head_radius':'sm_hub_head_nominal_radius+sm_output_head_diametral_compensation/2'}
 for name,expression in bindings.items():
  p=d.userParameters.itemByName(name);old=p.value;p.expression=expression;assert abs(p.value-old)<1e-9,(name,p.value,old)
 for key in list(parts):
  assert not any(c.partNumber=='CANDIDATE_sl_'+key+'_right'for c in d.allComponents);occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name=parts[key].name+' right handed';c.partNumber='CANDIDATE_sl_'+key+'_right';objects=core.ObjectCollection.create();objects.add(parts[key].bRepBodies.item(0));copied=c.features.copyPasteBodies.add(objects);copied.name='Shared native mount definition';assert copied.isParametric;original=copied.bodies.item(0);objects=core.ObjectCollection.create();objects.add(original);inp=c.features.mirrorFeatures.createInput(objects,c.xZConstructionPlane);inp.isCombine=False;c.features.mirrorFeatures.add(inp).name='Right handed mounting interface';c.features.removeFeatures.add(original).name='Keep right handed manufacturing part';parts[key+'_right']=c;occ.isLightBulbOn=False
 def snapshot():
  rows={}
  for key,c in parts.items():
   assert c.bRepBodies.count==1;body=c.bRepBodies.item(0);bb=body.boundingBox;centers=set();expected_radius=g.mm('sm_stator_hole_radius'if key.startswith('motor_mount_ring')else'sm_output_hole_radius');pcd=g.mm('sm_stator_pcd_radius'if key.startswith('motor_mount_ring')else'sm_output_pcd_radius')
   for face in body.faces:
    cylinder=core.Cylinder.cast(face.geometry)
    if cylinder and abs(cylinder.radius*10-expected_radius)<1e-5 and abs(abs(cylinder.axis.y)-1)<1e-6 and abs(math.hypot(cylinder.origin.x,cylinder.origin.z)*10-pcd)<1e-5:centers.add((round(cylinder.origin.x*10,6),round(cylinder.origin.z*10,6)))
   assert len(centers)==(9 if key.startswith('motor_mount_ring')else 6),(key,len(centers));rows[key]={'volume_mm3':body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'bounds_mm':[getattr(p,a)*10 for p in [bb.minPoint,bb.maxPoint] for a in ['x','y','z']],'vendor_centers_xz_mm':sorted(centers),'features':c.features.count,'sketches':c.sketches.count}
  return rows
 assert d.computeAll();before=snapshot();tests=[]
 for name,value in [('sm_tie_radius','44 mm'),('sm_stator_thickness','3.5 mm'),('sm_fastener_diametral_compensation','0.1 mm')]:
  p=d.userParameters.itemByName(name);old=p.expression
  try:
   p.expression=value;assert d.computeAll();changed=snapshot();issues=[(c.partNumber,f.name,f.errorOrWarningMessage)for c in parts.values()for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,issues;assert all(changed[k]['vendor_centers_xz_mm']==before[k]['vendor_centers_xz_mm']for k in parts);tests.append({'parameter':name,'value':value,'native_feature_health_passed':True,'vendor_bolt_centers_fixed':True,'parts':changed,'lower_tube_length_mm':g.mm('sm_lower_tube_length'),'upper_tube_length_mm':g.mm('sm_upper_tube_length')})
  finally:p.expression=old;assert d.computeAll()
 after=snapshot();restored=[]
 for key,a in before.items():
  b=after[key];dv=abs(a['volume_mm3']-b['volume_mm3']);db=max(abs(x-y)for x,y in zip(a['bounds_mm'],b['bounds_mm']));restored.append({'part':key,'volume_error_mm3':dv,'bounds_error_mm':db,'passed':dv<max(.001,1e-7*a['volume_mm3']) and db<.0001})
 paths=[]
 for key,c in parts.items():
  occ=next(o for o in root.occurrences if o.component==c);was=occ.isLightBulbOn;occ.isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','slim-native-'+key+'-restored.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>10000;occ.isLightBulbOn=was;paths.append(path)
 print(json.dumps({'passed':all(r['passed']for r in restored),'saved':False,'bindings':bindings,'tests':tests,'restoration':restored,'parts':after,'exports':paths,'elapsed_seconds':time.monotonic()-tick,'scope':'Four native mount definitions, three real edits/restores, fixed vendor bolt circles and derived tube lengths. Full-leg fits, washer/clamp geometry, standard roll-bearing redesign and load/CNC qualification remain separate gates.'}))
'''
r=rpc(s,'slim-motor-mounts-family-qualification',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/slim-motor-mounts-family-qualification.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k not in ['tests','parts','bindings']},flush=True)
for path in record['exports']:fetch(path,Path(path).name)
