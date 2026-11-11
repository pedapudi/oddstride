"""Offset the native outer loop once to define the structural sidewall."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py'])+'''
def run(_context: str):
 import json,time,tempfile,os
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_sl_thigh_master');assert c.features.count==1 and c.bRepBodies.count==1;g=IntentGeometry(d,c);body=c.bRepBodies.item(0);tick=time.monotonic();g.parameter('st_cavity_floor_y','lc_thigh_inner_y+st_inner_face');g.parameter('st_cavity_top_y','st_cap_y-4 mm');plane=g.plane(c.xZConstructionPlane,'st_cavity_floor_y','Six millimeter inboard structural face');sk=c.sketches.add(plane);sk.name='Linked eight millimeter structural sidewall';face=next(f for f in body.faces if abs(f.boundingBox.minPoint.y-g.mm('st_root_y')/10)<1e-7 and abs(f.boundingBox.maxPoint.y-g.mm('st_root_y')/10)<1e-7);assert face.edges.count==4;curves=[]
 for edge in face.edges:
  result=sk.project2([edge],True);assert len(result)==1;curves.append(result[0])
 inp=sk.geometricConstraints.createOffsetInput(curves,g.value('-st_wall'));offset=sk.geometricConstraints.addOffset2(inp);assert offset
 for curve in curves:curve.isConstruction=True
 assert sk.profiles.count==1,sk.profiles.count;cavity=g.extrude(sk,'st_cavity_top_y-st_cavity_floor_y','Structural cavity before roof clipping').bodies.item(0);cavity.name='Construction cavity with eight millimeter sidewall';assert c.bRepBodies.count==2;box=cavity.boundingBox;assert box.maxPoint.x<4.4 and box.minPoint.x>-4.5,'Offset must run inward'
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','slim-thigh-offset-cavity.step');o=next(o for o in root.occurrences if o.component==c);light=o.isLightBulbOn;stock_light=body.isLightBulbOn;o.isLightBulbOn=True;body.isLightBulbOn=False;cavity.isLightBulbOn=True;assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));o.isLightBulbOn=light;body.isLightBulbOn=stock_light;cavity.isLightBulbOn=False;assert os.path.getsize(path)>5000;print(json.dumps({'saved':False,'path':path,'projected_boundary_edges':len(curves),'features':c.features.count,'sketches':c.sketches.count,'cavity_volume_mm3':cavity.volume*1000,'elapsed_seconds':time.monotonic()-tick,'scope':'Linked native wall offset and flat inboard floor; outer and inner roof operations follow.'}))
'''
r=rpc(s,'slim-thigh-offset-cavity',timeout=300);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/slim-thigh-offset-cavity.json').write_text(json.dumps(record,indent=2));print(record,flush=True);fetch(record['path'],Path(record['path']).name)
