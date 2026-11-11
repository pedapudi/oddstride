"""Create a native revision, preserving the saved static-fit release and its parent."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py','cohesive_limb_intent.py','slim_mount_intent.py','knee_stator_seat_intent.py'])+'''
def run(_context:str):
 import json,os,tempfile,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;tick=time.monotonic()
 assert not any(c.partNumber=='CANDIDATE_ks_motor_mount_ring'for c in d.allComponents)
 old=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_sl_motor_mount_ring');oldstate=(old.features.count,old.bRepBodies.item(0).faces.count,old.bRepBodies.item(0).volume)
 crank=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_mc_input_crank').bRepBodies.item(0)
 screw=next(c for c in d.allComponents if c.attributes.itemByName('Tinfox','BenchReferenceName') and c.attributes.itemByName('Tinfox','BenchReferenceName').value=='Knee stator M3x8 140').bRepBodies.item(0)
 tm=fusion.TemporaryBRepManager.get();a=tm.copy(crank);b=tm.copy(screw);m=core.Matrix3D.create();m.setToRotation(math.radians(-138),core.Vector3D.create(0,1,0),core.Point3D.create(0,0,0));assert tm.transform(a,m);assert tm.booleanOperation(a,b,fusion.BooleanTypes.IntersectionBooleanType);oldoverlap=abs(a.volume)*1000;assert oldoverlap>1,oldoverlap
 o=root.occurrences.addNewComponent(core.Matrix3D.create());o.isLightBulbOn=False;c=o.component;c.name='Knee stator plate with open countersunk seats';c.partNumber='CANDIDATE_ks_motor_mount_ring';body=KneeStatorSeatIntent(IntentGeometry(d,c)).stator();body.name=c.name;assert c.bRepBodies.count==1
 assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features)
 objects=core.ObjectCollection.create();objects.add(body);ro=root.occurrences.addNewComponent(core.Matrix3D.create());ro.isLightBulbOn=False;rc=ro.component;rc.name='Right knee stator plate with open countersunk seats';rc.partNumber='CANDIDATE_ks_motor_mount_ring_right';copied=rc.features.copyPasteBodies.add(objects);copied.name='Linked final left plate including countersinks';seed=copied.bodies.item(0);collection=core.ObjectCollection.create();collection.add(seed);before={b.entityToken for b in rc.bRepBodies};mi=rc.features.mirrorFeatures.createInput(collection,rc.xZConstructionPlane);mf=rc.features.mirrorFeatures.add(mi);mf.name='Right-hand final plate';new=[b for b in rc.bRepBodies if b.entityToken not in before];assert len(new)==1;rc.features.removeFeatures.add(seed).name='Remove unhanded construction copy';assert rc.bRepBodies.count==1
 exports=[]
 for key,component,occ in [('motor_mount_ring',c,o),('motor_mount_ring_right',rc,ro)]:
  body=component.bRepBodies.item(0);cones=[f for f in body.faces if f.geometry.objectType==core.Cone.classType()];assert len(cones)==9,(key,len(cones));assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in component.features);occ.isLightBulbOn=True;body.isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','knee-seated-native-'+key+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,component));assert os.path.getsize(path)>15000;occ.isLightBulbOn=False;exports.append({'part':key,'path':path,'features':component.features.count,'sketches':component.sketches.count,'faces':body.faces.count,'cones':len(cones),'volume_mm3':body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000})
 assert oldstate==(old.features.count,old.bRepBodies.item(0).faces.count,old.bRepBodies.item(0).volume)
 print(json.dumps({'saved_version':doc.dataFile.versionNumber,'working_modified':doc.isModified,'candidate_only':True,'old_static_plate_unchanged':True,'old_native_stand_interference_mm3':oldoverlap,'exports':exports,'elapsed_seconds':time.monotonic()-tick,'hardware_override':{'item':'Knee stator to plate','specification':'M3 x 8 DIN7991, 90 degree head, nominal 5.9 mm head diameter','quantity':9,'head_top_y_mm':53.5,'seat_bottom_y_mm':52.25,'tip_y_mm':45.5,'nominal_motor_penetration_mm':4.9,'lower_plate_web_mm':1.75,'minimum_edge_land_mm':1.05,'status':'Native candidate. Exact export seating and crank sweeps pending; polymer preload and operating strength unqualified.'}}))
'''
r=rpc(s,'knee-stator-seats-native',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/knee-stator-seats-native.json').write_text(json.dumps(record,indent=2))
for row in record['exports']:fetch(row['path'],Path(row['path']).name)
print(record)
