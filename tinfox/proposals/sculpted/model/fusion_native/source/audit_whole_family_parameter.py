"""Exercise rear/handed motor-center propagation independently from vendor dimensions."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);comps={c.partNumber:c for c in d.allComponents if c.partNumber.startswith('CANDIDATE_wf_')};assert len(comps)==11;tick=time.monotonic();p=d.userParameters.itemByName('pr_pitch_x_offset');old=p.expression;assert abs(p.value*10-5)<1e-8;nominal={name:d.userParameters.itemByName(name).expression for name in ['pr_bearing_id','pr_bearing_od','pr_bearing_width','pc_motor_bore','pc_motor_screw_radius','pr_stator_pcd_radius']}
 def capture():
  rows={}
  for key,c in comps.items():
   assert c.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);b=c.bRepBodies.item(0);bb=b.boundingBox;row={'faces':b.faces.count,'edges':b.edges.count,'bounds_mm':[v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]],'vertices_mm':sorted([list(v.geometry.asArray())for v in b.vertices]),'volume_mm3':b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000}
   if 'closure'in key or 'motor_carrier'in key:
    expected_radius=d.userParameters.itemByName('pc_closure_bore').value*10 if 'closure'in key else d.userParameters.itemByName('pc_motor_bore').value*5;centers=[]
    for face in b.faces:
     cy=core.Cylinder.cast(face.geometry)
     if cy and abs(abs(cy.axis.y)-1)<1e-7 and abs(cy.radius*10-expected_radius)<1e-5:centers.append(cy.origin.x*10)
    assert centers,key;expected=(-1 if '_-1'in key else 1)*p.value*10;assert all(abs(x-expected)<1e-5 for x in centers),(key,centers,expected);row['motor_axis_x_mm']=centers
   rows[key]=row
  return rows
 before=capture()
 try:
  p.expression='5.25 mm';assert d.computeAll();changed=capture();assert all(d.userParameters.itemByName(k).expression==v for k,v in nominal.items())
 finally:p.expression=old;assert d.computeAll()
 restored=capture();errors={}
 for key,row in before.items():
  final=restored[key];e={'bounds_mm':max(abs(a-b)for a,b in zip(row['bounds_mm'],final['bounds_mm'])),'volume_mm3':abs(row['volume_mm3']-final['volume_mm3']),'vertex_mm':max(max(min(sum((a-b)**2 for a,b in zip(u,v))**.5*10 for v in target)for u in source)for source,target in [(row['vertices_mm'],final['vertices_mm']),(final['vertices_mm'],row['vertices_mm'])])};assert row['faces']==final['faces'] and row['edges']==final['edges'];assert e['bounds_mm']<1e-5 and e['vertex_mm']<1e-5 and e['volume_mm3']<.002,(key,e);errors[key]=e
 print(json.dumps({'passed':True,'parameter':'pr_pitch_x_offset','original_expression':old,'edited_expression':'5.25 mm','before':before,'changed':changed,'restored':restored,'restore_errors':errors,'vendor_dimensions_unchanged':nominal,'saved':False,'elapsed_seconds':time.monotonic()-tick,'scope':'Eleven linked native handed/rear support definitions. Rear closure translates without reversing stator clock. Static bench hardware placements are not claimed to follow this family edit.'}))
'''
compile(s,'whole_family_parameter.py','exec');r=rpc(s,'whole-paired-family-edit-restore',timeout=900);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/whole-paired-family-edit-restore.json').write_text(json.dumps(record,indent=2));print({'passed':True,'parts':len(record['before']),'seconds':record['elapsed_seconds']})
