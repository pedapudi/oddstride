import sys,json,gzip,hashlib
from pathlib import Path
r=Path('/home/sunil/git/oddstride/tinfox/proposals/sculpted/model/fusion_native');sys.path.insert(0,str(r/'source'));from run_native import rpc
from fetch_exports import fetch
oldpath=r/'exports/whole-native-master-63/native-whole-low-profile-canonical.json.gz';old=json.loads(gzip.decompress(oldpath.read_bytes()));inv=json.load(open(r/'audits/dfma-master-adoption.json'));oldmeta={p['name']:p for p in old['parts']};fl=json.loads(gzip.decompress((r/'exports/dfma-socket-fit-v1/dfma-one-leg-preview-socket.json.gz').read_bytes()));flmeta={p['name']:p for p in fl['parts']}
meta={}
for name,row in inv['instances'].items():
 if not row.get('leg'):continue
 p=oldmeta.get(name) or flmeta.get('FL_'+name[3:]) or {};meta[name]={k:p.get(k)for k in ['mesh','material','color','reference_role']}
s=(r/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,gzip,hashlib,os,time

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'master');assert doc.dataFile.versionNumber==64 and not doc.isModified;d=fusion.Design.cast(doc.products.itemByProductType('DesignProductType'));ldoc=authoring_document(app,'leg');assert ldoc.dataFile.versionNumber==39 and not ldoc.isModified;ld=fusion.Design.cast(ldoc.products.itemByProductType('DesignProductType'));cs={c.partNumber:c for c in ld.allComponents};live={};cache={};parts=[];meshes={};t=time.monotonic()
 def walk(o):
  live[o.fullPathName]=o
  for child in o.childOccurrences:walk(child)
 for o in d.rootComponent.occurrences:walk(o)
 for name,row in INVENTORY.items():
  if not row.get('leg'):continue
  occ=live[row['native_path']];world=list(occ.transform2.asArray());assert max(abs(a-b)for a,b in zip(world,row['world_matrix_cm']))<1e-7,name
  frame=core.Matrix3D.create();frame.setWithArray(FRAMES[row['leg']+':'+row['group']]);assert frame.invert();left=list(frame.asArray());transform=[sum(left[i*4+k]*world[k*4+j]for k in range(4))for i in range(4)for j in range(4)]
  if row.get('reference_body_in_frame'):
   bodies=[b for b in occ.component.bRepBodies if b.name==row['native_body_name']];assert len(bodies)==1,name
  else:bodies=list(occ.component.bRepBodies)
  vertices=[];faces=[];bodyrows=[]
  for bi,b in enumerate(bodies):
   assert b.isSolid;key=(occ.component.id,b.entityToken)
   if key not in cache:
    display=b.meshManager.displayMeshes;candidates=[(display.item(i).surfaceTolerance*10,display.item(i),'linked_native_display')for i in range(display.count)]
    if not row.get('reference_body_in_frame'):
     c=cs.get(occ.component.partNumber)
     if c and c.bRepBodies.count==len(bodies):
      sb=c.bRepBodies.item(bi);assert sb.faces.count==b.faces.count;assert max(abs(x-y)for x,y in zip(list(sb.boundingBox.minPoint.asArray())+list(sb.boundingBox.maxPoint.asArray()),list(b.boundingBox.minPoint.asArray())+list(b.boundingBox.maxPoint.asArray())))<1e-7;sd=sb.meshManager.displayMeshes;candidates +=[(sd.item(i).surfaceTolerance*10,sd.item(i),'saved_leg39_native_display')for i in range(sd.count)]
    eligible=[c for c in candidates if 0<c[0]<=.05]
    if eligible:tol,m,origin=max(eligible,key=lambda c:c[0])
    else:
     calc=b.meshManager.createMeshCalculator();calc.surfaceTolerance=.005;calc.maxNormalDeviation=.12;m=calc.calculate();tol=.05;origin='native_bounded_calculator'
    assert m and m.isValid;v=[[p.x,p.y,p.z]for p in m.nodeCoordinates];ix=list(m.nodeIndices);f=[ix[i:i+3]for i in range(0,len(ix),3)];cache[key]=(v,f,{'name':b.name,'faces':b.faces.count,'edges':b.edges.count,'solid':True,'native_display_surface_tolerance_mm':tol,'mesh_source':origin,'display_triangles':len(f)})
   v,f,br=cache[key];offset=len(vertices);vertices.extend([[10*(sum(transform[i*4+j]*p[j]for j in range(3))+transform[i*4+3])for i in range(3)]for p in v]);faces.extend([[x+offset for x in face]for face in f]);bodyrows.append(br)
  meta=META[name];pn=row['native_definition_id'];key=pn if row['kind']!='reference'else name;key=key.replace(' ','_');geom={'vertices':vertices,'faces':faces}
  if key in meshes:
   prior=meshes[key];same=prior['faces']==faces and len(prior['vertices'])==len(vertices)and max(abs(a-b)for p,q in zip(prior['vertices'],vertices)for a,b in zip(p,q))<1e-7
   if not same:key+='__'+name
  meshes[key]=geom;bounds=[min(v[i]for v in vertices)for i in range(3)]+[max(v[i]for v in vertices)for i in range(3)]
  role='vendor_or_standard_reference'if row['kind']=='reference'else'native_cut_stock'if 'TUBE' in pn or row['kind']=='native_cut_stock'else'custom_structure'
  parts.append({'name':name,'mesh':key,'source_mesh_key':meta.get('mesh')or key,'leg':row['leg'],'group':row['group'],'material':meta.get('material'),'color':meta.get('color'),'reference_role':role,'native_definition_id':pn,'native_path':occ.fullPathName,'native_world_matrix_cm':world,'native_group_local_matrix_cm':transform,'native_bodies':bodyrows,'native_visible':True,'bounds_mm':bounds,'com_mm':[(bounds[i]+bounds[i+3])/2 for i in range(3)],'mass_kg':None,'mass_status':'Material and operating mass unqualified.'})
 assert len(parts)==528 and sum(len(p['native_bodies'])for p in parts)==528;result={'parts':parts,'meshes':meshes,'saved_master_version':64,'saved_leg_version':39,'scope':'Actual saved native DFMA leg display meshes; no generated geometry.','seconds':time.monotonic()-t};raw=json.dumps(result,separators=(',',':')).encode();folder=os.path.expanduser('~/Library/Caches/Tinfox/native-whole-master-64');os.makedirs(folder,exist_ok=True);path=os.path.join(folder,'native-dfma-legs-display.json.gz');open(path,'wb').write(gzip.compress(raw,compresslevel=1,mtime=0));assert not doc.isModified and not ldoc.isModified;print(json.dumps({'path':path,'sha256':hashlib.sha256(open(path,'rb').read()).hexdigest(),'model_sha256':hashlib.sha256(raw).hexdigest(),'items':528,'triangles':sum(len(m['faces'])for m in meshes.values()),'seconds':time.monotonic()-t,'saved_master_version':64,'saved_leg_version':39,'modified':False}))
'''
for token,value in [('INVENTORY',inv['instances']),('FRAMES',inv['frames']),('META',meta)]:s=s.replace(token,repr(value))
compile(s,'native-export','exec')
a=rpc(s,'dfma-master64-leg-display-export',timeout=900,read_only=True);assert a[0]['success'],a
v=json.loads(a[0]['message']);(r/'audits/dfma-master64-leg-display-export.json').write_text(json.dumps(v,indent=2));fetch(v['path'],'whole-native-master-64/native-dfma-legs-display.json.gz');print(v)
