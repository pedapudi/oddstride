"""Export the already-authored DFMA bearing parts, independently of construction."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion

def run(_context:str):
 import os,json,time,hashlib
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);d.activateRootComponent();root=d.rootComponent;tick=time.monotonic();folder=os.path.join(os.path.expanduser('~'),'Library','Caches','Tinfox','dfma-architecture-v1');rows=[]
 for pn in ['DFMA_SHARED_ROLL_CAP_FL','DFMA_ROLL_HOUSING_FL','DFMA_ROLL_BACKPLATE_FL']:
  c=next(c for c in d.allComponents if c.partNumber==pn);assert c.bRepBodies.count==1;body=c.bRepBodies.item(0);original=next(o for o in root.occurrences if o.component.partNumber==pn);before=original.isLightBulbOn;original.isLightBulbOn=True;body.isLightBulbOn=True;path=os.path.join(folder,pn.lower()+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));original.isLightBulbOn=before;bb=body.boundingBox;rows.append({'part_number':pn,'features':c.features.count,'sketches':c.sketches.count,'faces':body.faces.count,'edges':body.edges.count,'bounds_mm':[v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]],'volume_mm3':body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'path':path,'sha256':hashlib.sha256(open(path,'rb').read()).hexdigest(),'bytes':os.path.getsize(path)})
 print(json.dumps({'parts':rows,'saved':False,'saved_baseline_leg_version':doc.dataFile.versionNumber,'seconds':time.monotonic()-tick,'scope':'Direct native component STEP exports of isolated, unqualified DFMA parts; no authoring or source promotion.'}))
'''
if __name__=='__main__':
 r=rpc(script,'dfma-shared-cap-exports',timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/dfma-shared-cap-exports.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
 for row in record['parts']:fetch(row['path'],'dfma-architecture-v1/'+Path(row['path']).name)
