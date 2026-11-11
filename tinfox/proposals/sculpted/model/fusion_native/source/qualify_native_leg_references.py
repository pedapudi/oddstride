"""Verify imported reference geometry and all native frame placements."""
import gzip,json,sys
from pathlib import Path
import cadquery as cq
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent));import kinematics as k
ref=json.loads((ROOT/'manifests/current-exact-hardware-references.json').read_text());model=json.loads(gzip.decompress((ROOT/'snapshots/current-hardware'/ref['source_model_sha256']/'reference-geometry.json.gz').read_bytes()));bykey={p['key']:p for p in ref['parts']};physical=[p for p in model['parts'] if p.get('leg')];geometry={}
for key in {p['mesh'] for p in physical}:
 shape=cq.importers.importStep(str(ROOT/bykey[key]['path'])).val();bb=shape.BoundingBox();geometry[key]={'volume_mm3':shape.Volume(),'bounds_mm':[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax],'faces':len(shape.Faces())}
expected={p['name']:dict(geometry[p['mesh']],leg=p['leg'],group=p['group']) for p in physical};k.P.update(model['parameters']);cases=[{'name':name,'pose':pose,'frames':{leg:{name:m.tolist() for name,m in k.frames(leg,pose[leg]).items()} for leg in k.LEGS}} for name,pose in model['poses'].items()]
s='''import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;parts=[];started=time.monotonic();modules=[]
 def leaves(occ,leg,group):
  if occ.component.bRepBodies.count:parts.append((leg,group,occ))
  for child in occ.childOccurrences:leaves(child,leg,group)
 for leg in root.occurrences:
  if not leg.component.partNumber.startswith('ASSEMBLY_'):continue
  modules.append(leg)
  for frame in leg.childOccurrences:
   attr=frame.component.attributes.itemByName('Tinfox','KinematicFrame')
   if not attr:continue
   lname,group=attr.value.split(':')
   for child in frame.childOccurrences:
    if child.component.partNumber.startswith('REFERENCE_'):leaves(child,lname,group)
 assert len(parts)==248;assert sorted(o.component.name for _,_,o in parts)==sorted(EXPECTED);shape_checks=[]
 for leg,group,occ in parts:
  name=occ.component.name;e=EXPECTED[name];assert e['leg']==leg and e['group']==group;assert occ.component.bRepBodies.count==1;b=occ.component.bRepBodies.item(0);volume=b.volume*1000;relative=abs(volume-e['volume_mm3'])/e['volume_mm3'];bb=b.boundingBox;bounds=[v*10 for v in bb.minPoint.asArray()+bb.maxPoint.asArray()];error=max(abs(a-b) for a,b in zip(bounds,e['bounds_mm']));assert relative<.0001,(name,'volume',relative);assert error<.05,(name,'bounds',error);shape_checks.append({'part':name,'relative_volume_error':relative,'bounds_error_mm':error,'native_faces':b.faces.count,'source_faces':e['faces']})
 parameters={f'pose_{leg}_{axis}':d.userParameters.itemByName(f'pose_{leg}_{axis}').expression for leg in ['FL','FR','RL','RR'] for axis in ['roll','hip','knee']};rows=[]
 def matrix(values):
  m=core.Matrix3D.create();assert m.setWithArray([v*(.1 if j==3 and i<3 else 1) for i,row in enumerate(values) for j,v in enumerate(row)]);return m
 try:
  for case in CASES:
   for leg,pose in case['pose'].items():
    for axis,value in zip(['roll','hip','knee'],pose):d.userParameters.itemByName('pose_'+leg+'_'+axis).expression=str(value)+' deg'
   assert d.computeAll();worst=0;vworst=0
   for leg,group,part in parts:
    expected=matrix(case['frames'][leg][group]);actual=part.transform2;error=max(abs(a-b) for a,b in zip(expected.asArray(),actual.asArray()));worst=max(worst,error);assert error<1e-7,(case['name'],part.fullPathName,error);body=part.component.bRepBodies.item(0);point=body.vertices.item(0).geometry.copy();point.transformBy(expected);actual_point=body.createForAssemblyContext(part).vertices.item(0).geometry;delta=point.distanceTo(actual_point);vworst=max(vworst,delta);assert delta<1e-7,(case['name'],part.fullPathName,delta)
   for leg in modules:assert all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for j in leg.component.joints),leg.name
   rows.append({'pose':case['name'],'physical_references':248,'maximum_matrix_error_cm':worst,'maximum_vertex_error_cm':vworst})
 finally:
  for name,expression in parameters.items():d.userParameters.itemByName(name).expression=expression
  assert d.computeAll()
 print(json.dumps({'passed':True,'saved':False,'shape_checks':shape_checks,'pose_checks':rows,'elapsed_seconds':time.monotonic()-started,'scope':'Reference STEP volume/bounds and 248 actual occurrences across eight native driven poses. Supplier specifications and all-pose collision freedom remain unqualified.'}))
'''.replace('EXPECTED',repr(expected)).replace('CASES',repr(cases))
r=rpc(s,'native-leg-reference-qualification',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/native-leg-reference-qualification.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'parts':len(record['shape_checks']),'poses':len(record['pose_checks']),'seconds':record['elapsed_seconds']})
