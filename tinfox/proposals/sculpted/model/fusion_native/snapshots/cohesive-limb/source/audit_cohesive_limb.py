"""Exact-solid clamshell interfaces and bearing withdrawal, separate from motion."""
import hashlib,json,sys,math
from functools import cache
from pathlib import Path
import cadquery as cq
from kinematics import ROOT
import build as b
folder=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'output/cohesive-limb-work'
raw=(folder/'model.json').read_bytes();data=json.loads(raw)
params=data['parameters']
inner_y=params.get('knee_bearing_inner_y',54)
outer_y=params.get('knee_bearing_outer_y',74)
bearing_width=params.get('knee_bearing_width',8)
channel=params.get('knee_shaft_channel_y',[65.8,74.2])
@cache
def solid(key):
    if key=='knee_motor':return b.motor_envelope((0,54.4,0))
    if key.startswith('rod_bush_output_'):
        a=math.radians(-78);x,z=28*math.cos(a),-28*math.sin(a)
        return b.rod_bush(-170,key.endswith('_1')).translate((x,-16,z+170))
    for p in [folder/'step'/f'{key}.step',ROOT/'output/integrated-candidate/step'/f'{key}.step',ROOT/'output/v0-rounded-body/step'/f'{key}.step',ROOT/'output/service-design/step'/f'{key}.step',ROOT/'output/step-parts'/f'{key}.step']:
        if p.exists():
            shape=cq.importers.importStep(str(p)).val()
            expected_solids=2 if key.startswith('pod_sleeve_') else 1
            assert shape.isValid() and len(shape.Solids())==expected_solids,('Interface input must contain the expected closed STEP solids',key,shape.ShapeType(),len(shape.Solids()))
            return shape
    raise FileNotFoundError(key)
def overlap(a,c):return max(0,sum(s.Volume() for s in a.intersect(c).Solids()))
rows=[]
def fit(label,a,c):
    v=overlap(a,c);rows.append({'interface':label,'overlap_mm3':v,'passed':v<.001});return v
for kind in ['thigh','shin']:
    fit(kind+' structural halves',solid(kind+'_inner'),solid(kind+'_outer'))
for side in ['inner','outer']:
    thigh=solid('thigh_'+side);shin=solid('shin_'+side)
    for key in ['hip_hub','knee_motor','motor_mount_ring','pod_sleeve_90','pod_sleeve_210','pod_sleeve_330','pod_tie_90','pod_tie_210','pod_tie_330','sleeve_0','sleeve_1','bolt_0','bolt_1','thigh_clamp_nut_0','knee_axle','axle_bolt','axle_nut','knee_inner_spacer']:
        fit('thigh '+side+' / '+key,thigh,solid(key))
    for key in ['bearing_inner','bearing_outer','shin_clamp_bolt_37','shin_clamp_bolt_105','shin_clamp_nut_37','shin_clamp_nut_105','shin_clamp_sleeve_37','shin_clamp_sleeve_105','output_pin','output_pivot_nut','rod_bush_output_0','rod_bush_output_1']:
        fit('shin '+side+' / '+key,shin,solid(key))
    bearing=solid('bearing_'+side);direction=-1 if side=='inner' else 1
    bearing_y=inner_y if side=='inner' else outer_y
    for travel in [0,.1,.5,1,2,4,8,12,20,35]:
        fit(side+' bearing extraction '+str(travel)+' mm',shin,bearing.translate((0,direction*travel,0)))
    for xx in [-12.7,12.7]:
        fit(side+' extraction tool '+str(xx),shin,b.cyl(1,16,(xx,61,0)))
    probe=b.ring(14.8,14.2,1,57.5 if side=='inner' else 77.5)
    coverage=overlap(shin,probe)/probe.Volume()
    rows.append({'interface':side+' complete bearing wall','coverage_fraction':coverage,'passed':coverage>.999})
    # Check the entire occupied axial width, not just one favorable section.
    full_wall=b.ring(14.8,14.2,bearing_width,bearing_y)
    coverage=overlap(shin,full_wall)/full_wall.Volume()
    rows.append({'interface':side+' full-width bearing wall','coverage_fraction':coverage,'passed':coverage>.999})
    shoulder_y=inner_y+bearing_width if side=='inner' else channel[1]
    shoulder_thickness=channel[0]-shoulder_y if side=='inner' else outer_y-channel[1]
    shoulder=b.ring(13.8,12.8,shoulder_thickness,shoulder_y)
    for xx in [-12.7,12.7]:shoulder=shoulder.cut(b.cyl(1.3,16,(xx,61,0)))
    coverage=overlap(shin,shoulder)/shoulder.Volume()
    rows.append({'interface':side+' continuous axial bearing shoulder','coverage_fraction':coverage,'thickness_mm':shoulder_thickness,'permitted_openings':'Two modeled outer-race extraction holes are excluded from the required support area.','passed':coverage>.999 and shoulder_thickness>=3})
    surround=b.ring(19.4,14.001,bearing_width,bearing_y)
    coverage=overlap(shin,surround)/surround.Volume()
    rows.append({'interface':side+' minimum radial bearing surround','required_wall_mm':5.4,'coverage_fraction':coverage,'passed':coverage>.999})
    backup=thigh.translate((0,0,170))
    gap=backup.distance(bearing)
    retained=overlap(backup,bearing.translate((0,direction*.5,0)))
    rows.append({'interface':side+' thigh bearing backup','gap_mm':gap,'retained_after_half_mm_travel_mm3':retained,'passed':gap>.25 and retained>1})
    for travel in [.1,1,5,15,40,70]:
        fit(side+' shin half removal '+str(travel),shin.translate((0,direction*travel,0)),solid('shin_outer' if side=='inner' else 'shin_inner'))
# A full turn is stronger than testing only the nominal hip angle. Roll does
# not change relative carrier/tie geometry, and rear carriers are also tested.
from trimesh.collision import CollisionManager
import trimesh,numpy as np
from kinematics import rotation
for front in [1,-1]:
    carrier=solid('motor_carrier_'+str(front));vv,ff=carrier.tessellate(.08,.1)
    manager=CollisionManager();manager.add_object('carrier',trimesh.Trimesh(vertices=[v.toTuple() for v in vv],faces=ff,process=False))
    gaps=[];hits=[]
    for angle in b.POD_TIE_ANGLES:
        tie=solid('pod_tie_'+str(angle));vv,ff=tie.tessellate(.08,.1);mesh=trimesh.Trimesh(vertices=[v.toTuple() for v in vv],faces=ff,process=False)
        for hip in range(-180,181):
            m=rotation('y',hip)
            if manager.in_collision_single(mesh,transform=m):hits.append([angle,hip])
            gaps.append(float(manager.min_distance_single(mesh,transform=m)))
    rows.append({'interface':str(front)+' carrier / rotating pod ties','sample_step_deg':1,'minimum_mesh_gap_mm':min(gaps),'collision_samples':hits,'passed':not hits})
report={'model_sha256':hashlib.sha256(raw).hexdigest(),'checks':rows,'passed':all(r['passed'] for r in rows),'scope':'Nominal exact-solid interfaces, complete bearing-seat walls and sampled withdrawal paths. Carrier/tie clearance uses rigid meshes through a full hip revolution at one-degree steps. No material-strength, tolerance-stack, fastener-preload or loaded-motion qualification.'}
(folder/'limb-interfaces.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'passed':report['passed'],'failed':[r for r in rows if not r['passed']],'checks':len(rows)},indent=2))
