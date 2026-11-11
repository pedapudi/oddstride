"""Build the functional V0 support around the native hull construction."""
import json,sys
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1];stage=sys.argv[1]
shared=(ROOT/'source/intent_geometry.py').read_text()+(ROOT/'source/nose_intent.py').read_text()
start='''
def run(_context: str):
 import os,tempfile,json
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent
 occ=next(o for o in root.occurrences if o.component.partNumber=='CANDIDATE_body_nose_surround');c=occ.component;g=IntentGeometry(d,c);n=NoseIntent(g)
'''
if stage=='inner':
 body=''' assert c.features.count==2
 inner=n.hull('nose_wall','Nose inner');inner.name='Inner hull construction'
 print(json.dumps({'stage':'inner','features':c.features.count,'sketches':c.sketches.count,'bodies':[(b.name,b.faces.count,b.edges.count) for b in c.bRepBodies],'saved':False}))
'''
elif stage=='support':
 body=''' assert c.features.count==4
 outer=next(b for b in c.bRepBodies if b.name=='Outer hull construction');inner=next(b for b in c.bRepBodies if b.name=='Inner hull construction')
 for key,value in {'nose_bridge_width':44,'nose_bridge_depth':38,'nose_mount_lap_width':48,'nose_mount_lap_thickness':3.5,'nose_mount_lap_top':46.3,'nose_tab_half_y':94,'nose_post_half_y':89,'nose_post_half_z':27,'nose_post_radius':3.5,'nose_post_pilot_radius':1.25,'nose_fascia_thickness':2.1}.items():g.parameter(key,value,comment='V0 functional head interface dimension')
 stock=g.box('70 mm','280 mm','150 mm','nose_end_start_x + 35 mm','0 mm','0 mm','End shell stock');end=g.combine(stock,[outer],fusion.FeatureOperations.IntersectFeatureOperation,'Match fuselage envelope',True);end=g.combine(end,[inner],fusion.FeatureOperations.CutFeatureOperation,'Hollow end shell')
 tab=g.box('3.8 mm','17 mm','3.2 mm','nose_end_start_x - .2 mm','-nose_tab_half_y','-nose_post_half_z','Fascia mounting tab');tab=g.round_edges(tab,'.6 mm','Mount tab edge rounds');tabs=g.pattern_yz(tab,'2*nose_tab_half_y','2*nose_post_half_z','Four fascia tabs');assert len(tabs)==4
 end=g.combine(end,tabs,fusion.FeatureOperations.JoinFeatureOperation,'Unite tabs with end shell');end=g.combine(end,[outer],fusion.FeatureOperations.IntersectFeatureOperation,'Trim tabs to fuselage',True)
 limit=g.box('70 mm','280 mm','150 mm','nose_end_start_x + 35 mm','0 mm','0 mm','End shell boundary');end=g.combine(end,[limit],fusion.FeatureOperations.IntersectFeatureOperation,'Trim tabs at rear seam')
 chin=g.box('12 mm','220 mm','12 mm','nose_end_start_x + 6 mm','0 mm','-39 mm','Lower front return');chin=g.combine(chin,[outer],fusion.FeatureOperations.IntersectFeatureOperation,'Shape lower front return',True)
 stations=[('nose_mount_x + 5 mm','nose_mount_lap_width','10 mm','body_mid_roof_z - 5.5 mm'),('body_hip_x - 43 mm','nose_bridge_width','nose_bridge_depth - 8 mm','body_mid_roof_z - .5 mm'),('body_hip_x - 20 mm','nose_bridge_width','nose_bridge_depth','body_mid_roof_z - .5 mm'),('body_hip_x + 10 mm','nose_bridge_width','nose_bridge_depth','body_mid_roof_z - .5 mm'),('body_hip_x + 35 mm','nose_bridge_width','nose_bridge_depth - 6 mm','body_mid_roof_z - 2.5 mm'),('nose_end_start_x + 1 mm','80 mm','12 mm','body_mid_roof_z - 6.5 mm')]
 profiles=[g.yz_contour(x,w,h,'2 mm',z,'Bridge section '+str(i+1)) for i,(x,w,h,z) in enumerate(stations)];bridge=g.loft(profiles,'Continuous mounting bridge')
 relief=g.box('20 mm','100 mm','100 mm','nose_mount_x - 3 mm','0 mm','nose_mount_lap_top - nose_mount_lap_thickness - 50 mm','Mount underside relief');bridge=g.combine(bridge,[relief],fusion.FeatureOperations.CutFeatureOperation,'Open mount underside')
 lap=g.box('26 mm','nose_mount_lap_width','nose_mount_lap_thickness','nose_mount_x + 6 mm','0 mm','nose_mount_lap_top - nose_mount_lap_thickness/2','Chassis mounting lap');lap=g.round_edges(lap,'.5 mm','Lap edge rounds')
 roof=g.box('6 mm','50 mm','2.8 mm','nose_mount_x + 8 mm','0 mm','body_mid_roof_z - 1.4 mm','Existing roof interface')
 end=g.combine(end,[chin,bridge,lap,roof],fusion.FeatureOperations.JoinFeatureOperation,'Unite bridge and chassis interface');end.name='Nose support before clearances'
 g.remove(outer,'Retire outer construction body')
 print(json.dumps({'stage':'support','features':c.features.count,'sketches':c.sketches.count,'bodies':[(b.name,b.faces.count,b.edges.count) for b in c.bRepBodies],'saved':False}))
'''
elif stage=='clearances':
 body=''' support=next(b for b in c.bRepBodies if b.name=='Nose support before clearances');assert c.bRepBodies.count==1
 facebody=g.face_sweep('nose_fascia_thickness','Fascia seating datum');faces=[f for f in facebody.faces if f.boundingBox.minPoint.x>22];assert len(faces)==1
 sk=g.circle_grid_yz('nose_end_start_x','nose_post_half_y','nose_post_half_z','nose_post_radius','0 mm','Four fascia bosses');posts=g.extrude_to_face(sk,faces[0],'Bosses up to compound seating face');assert posts.bodies.count==4
 support=g.combine(support,[b for b in posts.bodies],fusion.FeatureOperations.JoinFeatureOperation,'Integral fascia bosses');g.remove(facebody,'Retire seating construction body')
 shoulder=n.shoulder();entities=core.ObjectCollection.create();entities.add(shoulder);before=[b for b in c.bRepBodies];inp=c.features.mirrorFeatures.createInput(entities,c.xZConstructionPlane);inp.isCombine=False;mir=c.features.mirrorFeatures.add(inp);mir.name='Opposite shoulder clearance';mirrored=[b for b in c.bRepBodies if b not in before];assert len(mirrored)==1
 support=g.combine(support,[shoulder,mirrored[0]],fusion.FeatureOperations.CutFeatureOperation,'Clear both hip roll sweeps')
 aperture=g.yz_contour('226 mm','168 mm','44 mm','8 mm','4 mm','Sensor access aperture');g.extrude(aperture,'36 mm','Open sensor access',fusion.FeatureOperations.CutFeatureOperation,[support]);support=c.bRepBodies.item(0)
 plane=g.plane(c.xYConstructionPlane,'nose_mount_lap_top','Mount screw datum');sk=c.sketches.add(plane);sk.name='Two chassis attachment centers';points=core.ObjectCollection.create();p0=g.skeleton_point(sk,'nose_mount_x','-nose_mount_half_spacing');g.point_dimensions(sk,p0,'nose_mount_x','-nose_mount_half_spacing');p1=g.skeleton_point(sk,'nose_mount_x','nose_mount_half_spacing');g.point_dimensions(sk,p1,None,'nose_mount_half_spacing');sk.geometricConstraints.addVerticalPoints(p0,p1);points.add(p0);points.add(p1)
 inp=c.features.holeFeatures.createCountersinkInput(g.value('nose_mount_clearance_diameter'),g.value('6 mm'),g.value('90 deg'));assert inp.setPositionBySketchPoints(points);assert inp.setDistanceExtent(g.value('11.3 mm'));inp.participantBodies=[support];feature=c.features.holeFeatures.add(inp);feature.name='Two countersunk chassis attachment holes';sk.isVisible=False
 pilots=g.circle_grid_yz('238.5 mm','nose_post_half_y','nose_post_half_z','nose_post_pilot_radius','0 mm','Fascia screw pilots');g.extrude_all(pilots,'30 mm','Four fascia screw pilot bores',fusion.FeatureOperations.CutFeatureOperation,[support]);support=c.bRepBodies.item(0);support.name='Nose support awaiting fascia fit'
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','nose-support-intent.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c))
 print(json.dumps({'stage':'clearances','features':c.features.count,'sketches':c.sketches.count,'bodies':[(b.name,b.faces.count,b.edges.count) for b in c.bRepBodies],'path':path,'saved':False}))
'''
else:raise ValueError(stage)
r=rpc(shared+start+body,'nose-intent-'+stage,timeout=180);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/f'audits/nose-intent-{stage}.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
if record.get('path'):fetch(record['path'],Path(record['path']).name)
