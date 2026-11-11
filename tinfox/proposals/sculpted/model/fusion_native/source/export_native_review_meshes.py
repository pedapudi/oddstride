"""Export local component meshes directly from the native Fusion kernel."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1];target=json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low'];keys=sorted(p['key'] for p in target['custom_parts'])
s='''import adsk.core as core,adsk.fusion as fusion,json,gzip,os,tempfile,time

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:7_ejr6qRQtezEex5HEj7xw';d=fusion.Design.cast(app.activeProduct);tick=time.monotonic();meshes={};failures=[];cache=os.path.join(tempfile.gettempdir(),'tinfox-native','review-mesh-cache','chassis12-leg13-head22');os.makedirs(cache,exist_ok=True)
 for key in KEYS:
  cached=os.path.join(cache,key+'.json.gz')
  if os.path.exists(cached):meshes[key]=json.loads(gzip.decompress(open(cached,'rb').read()));continue
  matches=[c for c in d.allComponents if c.partNumber==key and c.bRepBodies.count];assert len(matches)==1,(key,len(matches));c=matches[0];assert c.bRepBodies.count==1,(key,c.bRepBodies.count);b=c.bRepBodies.item(0);calc=b.meshManager.createMeshCalculator();calc.surfaceTolerance=.002;calc.maxNormalDeviation=.04;mesh=calc.calculate();vertices=[[p.x*10,p.y*10,p.z*10] for p in mesh.nodeCoordinates];indices=list(mesh.nodeIndices);assert len(indices)%3==0,(key,'indices',len(indices))
  if not indices:
   failures.append({'part':key,'reason':'Native mesh calculator returned zero triangles','native_faces':b.faces.count,'native_volume_cm3':b.volume});continue
  faces=[indices[i:i+3] for i in range(0,len(indices),3)];meshes[key]={'vertices':vertices,'faces':faces,'features':c.features.count,'sketches':c.sketches.count,'native_faces':b.faces.count};open(cached,'wb').write(gzip.compress(json.dumps(meshes[key],separators=(',',':')).encode()))
 refs=[{'role':o.attributes.itemByName('Tinfox','Subsystem').value,'version':o.documentReference.version} for o in d.rootComponent.occurrences];record={'source':'Native Fusion meshManager on authored component BReps; local millimetre coordinates','surface_tolerance_mm':.02,'maximum_normal_deviation_rad':.04,'subsystems':refs,'meshes':meshes,'failures':failures,'complete':not failures};path=os.path.join(tempfile.gettempdir(),'tinfox-native','current-native-review-meshes.json.gz');open(path,'wb').write(gzip.compress(json.dumps(record,separators=(',',':')).encode()));print(json.dumps({'path':path,'parts':len(meshes),'triangles':sum(len(m['faces']) for m in meshes.values()),'bytes':os.path.getsize(path),'elapsed_seconds':time.monotonic()-tick,'modified':doc.isModified,'subsystems':refs,'failures':failures,'complete':not failures}))
'''.replace('KEYS',repr(keys))
r=rpc(s,'native-review-mesh-export',timeout=300,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/native-review-mesh-export.json').write_text(json.dumps(record,indent=2));print(record);fetch(record['path'],Path(record['path']).name)
