"""Build the compact four-curve thigh outline as native editable geometry."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
fit=json.loads((ROOT/'snapshots/latest-leg/slim-thigh-spline-skeleton.json').read_text())
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py','native_nonuniform_spline.py','cohesive_limb_intent.py','cohesive_thigh_intent.py','slim_thigh_intent.py'])+'''
def run(_context: str):
 import json,os,tempfile,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();assert not any(c.partNumber=='CANDIDATE_sl_thigh_master'for c in d.allComponents);tick=time.monotonic();o=root.occurrences.addNewComponent(core.Matrix3D.create());c=o.component;c.name='Closed thigh shared structural master';c.partNumber='CANDIDATE_sl_thigh_master';g=IntentGeometry(d,c);builder=SlimThighIntent(g);sk=builder.slim_outline(FIT);body=g.extrude_all(sk,'st_cap_y-st_root_y','Shared elliptical and flowing thigh stock').bodies.item(0);assert c.bRepBodies.count==1;path=os.path.join(tempfile.gettempdir(),'tinfox-native','slim-thigh-outline-stock.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));o.isLightBulbOn=False;assert os.path.getsize(path)>5000;print(json.dumps({'saved':False,'path':path,'sketches':c.sketches.count,'features':c.features.count,'outline_curves':sk.sketchCurves.count,'side_spline_count':sk.sketchCurves.sketchControlPointSplines.count,'side_control_poles':[len(x.controlPoints)for x in sk.sketchCurves.sketchControlPointSplines],'faces':body.faces.count,'edges':body.edges.count,'elapsed_seconds':time.monotonic()-tick,'scope':'Shared four-curve stock only. Structural pockets, motor interfaces and clamp seats are not yet added.'}))
'''.replace('FIT',repr(fit))
r=rpc(s,'slim-thigh-outline-stock',timeout=360);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/slim-thigh-outline-stock.json').write_text(json.dumps(record,indent=2));print(record,flush=True);fetch(record['path'],Path(record['path']).name)
