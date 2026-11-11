"""Direct native exports for the two small reviewed DFMA refinements."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,os,hashlib

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);d.activateRootComponent();folder=os.path.join(os.path.expanduser('~'),'Library','Caches','Tinfox','dfma-architecture-v1');rows=[]
 for pn,filename in [('DFMA_SHARED_ROLL_CAP_FL','dfma_shared_roll_cap_fl-3p8.step'),('DFMA_REAR_LOADED_CUP_FL','dfma-rear-loaded-cup-rounded-ports.step')]:
  c=next(c for c in d.allComponents if c.partNumber==pn);assert c.bRepBodies.count==1;body=c.bRepBodies.item(0);body.isLightBulbOn=True;roots=[o for o in d.rootComponent.occurrences if o.component.partNumber==pn];states=[o.isLightBulbOn for o in roots]
  for o in roots:o.isLightBulbOn=True
  path=os.path.join(folder,filename);assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c))
  for o,visible in zip(roots,states):o.isLightBulbOn=visible
  assert os.path.getsize(path)>5000;bb=body.boundingBox;rows.append({'part_number':pn,'path':path,'sha256':hashlib.sha256(open(path,'rb').read()).hexdigest(),'features':c.features.count,'sketches':c.sketches.count,'bounds_mm':[v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]],'native_volume_mm3':body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000})
 camera=app.activeViewport.camera;camera.eye=core.Point3D.create(18,-22,17);camera.target=core.Point3D.create(-2,-2,0);camera.upVector=core.Vector3D.create(0,0,1);camera.isSmoothTransition=False;app.activeViewport.camera=camera;app.activeViewport.fit();app.activeViewport.refresh();png=os.path.join(folder,'dfma-bearing-cup-proposal.png');assert app.activeViewport.saveAsImageFile(png,1400,1000);print(json.dumps({'parts':rows,'image':{'path':png,'sha256':hashlib.sha256(open(png,'rb').read()).hexdigest()},'saved_version':doc.dataFile.versionNumber,'save_complete':doc.dataFile.isComplete,'modified':doc.isModified,'native_source_of_truth':False,'scope':'Isolated native DFMA proposal only. Published baseline and prototype packages unchanged.'}))
'''
if __name__=='__main__':
 r=rpc(s,'dfma-refined-exports',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/dfma-refined-exports.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
 for row in record['parts']+[record['image']]:fetch(row['path'],'dfma-architecture-v1/'+Path(row['path']).name)
