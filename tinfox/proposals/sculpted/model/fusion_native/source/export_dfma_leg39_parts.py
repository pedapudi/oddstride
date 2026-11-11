import sys,json,hashlib
from pathlib import Path
r=Path('/home/sunil/git/oddstride/tinfox/proposals/sculpted/model/fusion_native');sys.path.insert(0,str(r/'source'));from run_native import rpc
from fetch_exports import fetch
rows=json.loads((r/'audits/dfma-handed-native-families.json').read_text())['parts']+[{'part_number':'DFMA_REAR_LOADED_CUP_FR','source':'DFMA_REAR_LOADED_CUP_FL','plane':'XZ'},{'part_number':'DFMA_STATOR_TUBE_34'},{'part_number':'DFMA_CLAMP_TUBE_31'}]
s=(r/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,os,hashlib,time

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc.dataFile.versionNumber==39 and not doc.isModified;d=fusion.Design.cast(doc.products.itemByProductType('DesignProductType'));cs={c.partNumber:c for c in d.allComponents};folder=os.path.expanduser('~/Library/Caches/Tinfox/dfma-whole-leg39-complete');os.makedirs(folder,exist_ok=True);out=[];t=time.monotonic()
 for row in ROWS:
  c=cs[row['part_number']];assert c.bRepBodies.count==1 and c.bRepBodies.item(0).isSolid;body=c.bRepBodies.item(0);b=body.boundingBox;record=dict(row);record.update(bounds_mm=[10*x for x in list(b.minPoint.asArray())+list(b.maxPoint.asArray())],faces=body.faces.count,edges=body.edges.count,features=c.features.count,saved_version=39)
  if row.get('source'):
   source=cs[row['source']].bRepBodies.item(0);axis=0 if row['plane']=='YZ'else1;expected=sorted(tuple(round((-1 if i==axis else 1)*v.geometry.asArray()[i],7)for i in range(3))for v in source.vertices);actual=sorted(tuple(round(x,7)for x in v.geometry.asArray())for v in body.vertices);assert expected==actual,(row['part_number'],'mirror vertex mismatch');assert source.faces.count==body.faces.count;record['linked_native_mirror_verified']=True
  path=os.path.join(folder,c.partNumber+'.step');o=d.exportManager.createSTEPExportOptions(path,c);o.isIncludingInvisibleBodies=True;o.isIncludingInvisibleComponents=True;assert os.path.exists(path) or d.exportManager.execute(o);assert any(tag in open(path).read() for tag in ['MANIFOLD_SOLID_BREP','BREP_WITH_VOIDS']),(path,os.path.getsize(path));record.update(path=path,bytes=os.path.getsize(path),sha256=hashlib.sha256(open(path,'rb').read()).hexdigest());out.append(record)
 assert not doc.isModified;print(json.dumps({'passed':True,'parts':out,'saved_version':39,'modified':doc.isModified,'seconds':time.monotonic()-t}))
'''
s=s.replace('ROWS',repr(rows)).replace("else1","else 1")
a=rpc(s,'dfma-leg39-handed-stock-export',timeout=600,read_only=True);assert a[0]['success'],a
v=json.loads(a[0]['message']);(r/'audits/dfma-leg39-handed-stock-export.json').write_text(json.dumps(v,indent=2))
for p in v['parts']:fetch(p['path'],'dfma-whole-leg39/'+Path(p['path']).name)
print(json.dumps(v,indent=2))
