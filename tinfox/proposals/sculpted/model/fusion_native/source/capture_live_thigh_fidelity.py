"""Compare source boundary witnesses to native trimmed faces and export native meshes."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
probes=json.loads((ROOT/'snapshots/slim-thigh-live-source-probes.json').read_text())
s='import adsk.core as core,adsk.fusion as fusion,json,os,tempfile,math,time,gzip\nPROBES='+repr(probes)+'''
def run(_context: str):
 app=core.Application.get();d=fusion.Design.cast(app.activeProduct);assert 'Leg module' in d.parentDocument.name;tick=time.monotonic();records={};temporary=fusion.TemporaryBRepManager.get()
 for key,row in PROBES.items():
  c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_sl_'+key);assert c.bRepBodies.count==1;body=c.bRepBodies.item(0);faces=list(body.faces);sheets=[temporary.copy(f)for f in faces];bounds=[(f.boundingBox.minPoint.asArray(),f.boundingBox.maxPoint.asArray())for f in faces];distances=[];worst=None
  for xyz in row['points']:
   v=[x/10 for x in xyz];q=core.Point3D.create(*v);lower=[math.sqrt(sum(max(lo-x,0,x-hi)**2 for x,lo,hi in zip(v,a,b)))for a,b in bounds];minimum=min(lower);candidates=[i for i,b in enumerate(lower)if b<=minimum+.02];measure=min((app.measureManager.measureMinimumDistance(q,sheets[i])for i in candidates),key=lambda m:m.value);error=measure.value*10;distances.append(error)
   if worst is None or error>worst['distance_mm']:worst={'point_mm':xyz,'distance_mm':error,'closest_native_point_mm':[v*10 for v in measure.positionTwo.asArray()]}
  calculator=body.meshManager.createMeshCalculator();calculator.surfaceTolerance=.0005;calculator.maxNormalDeviation=.03;mesh=calculator.calculate();vertices=[[p.x*10,p.y*10,p.z*10]for p in mesh.nodeCoordinates];indices=list(mesh.nodeIndices);assert len(indices)%3==0 and indices;triangles=[indices[i:i+3]for i in range(0,len(indices),3)];records[key]={'source_sha256':row['source_sha256'],'source_faces_sampled':row['source_face_count'],'source_samples':len(distances),'maximum_source_to_native_mm':max(distances),'worst_source_sample':worst,'vertices':vertices,'triangles':triangles,'native_faces':len(faces),'native_features':c.features.count,'native_sketches':c.sketches.count,'feature_health':[(f.name,int(f.healthState))for f in c.features]}
 record={'document':d.parentDocument.name,'saved_version':d.parentDocument.dataFile.versionNumber,'working_modified':d.parentDocument.isModified,'mesh_surface_tolerance_mm':.005,'mesh_normal_tolerance_rad':.03,'source_boundary_measurement':'Exact distance to copied native trimmed face sheets; never distance to a containing solid.','parts':records,'elapsed_seconds':time.monotonic()-tick};path=os.path.join(tempfile.gettempdir(),'tinfox-native','slim-thigh-live-fidelity.json.gz');open(path,'wb').write(gzip.compress(json.dumps(record).encode()));print(json.dumps({'path':path,'elapsed_seconds':record['elapsed_seconds'],'parts':{k:{'source_to_native_mm':r['maximum_source_to_native_mm'],'samples':r['source_samples'],'triangles':len(r['triangles'])}for k,r in records.items()}}))
'''
r=rpc(s,'slim-thigh-live-fidelity',timeout=600,read_only=True);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/slim-thigh-live-fidelity-capture.json').write_text(json.dumps(record,indent=2));print(record,flush=True);fetch(record['path'],Path(record['path']).name)
