"""Closed rearward thigh and rail-mounted camera candidate on rounded V0."""
import hashlib
import inspect
import json
import math
import time
from functools import cache
from pathlib import Path

import cadquery as cq
import numpy as np
from scipy.spatial import ConvexHull

import build as b
import service_design as sd
from body_caps import shoulder_sweep
from rounded_design import oval_loft
from kinematics import ROOT

BASE=ROOT/'output/v0-rounded-body'
OUT=ROOT/'output/integrated-candidate'
for directory in ['', 'step','stl','cache']:(OUT/directory).mkdir(exist_ok=True)
RADIUS=28.0
PHASE=math.radians(-78)
PIN=(RADIUS*math.cos(PHASE),-RADIUS*math.sin(PHASE))
box,cyl,ring=b.box,b.cyl,b.ring
TIMINGS=[]

@cache
def source(key):
    for folder in [BASE/'step',ROOT/'output/service-design/step',ROOT/'output/step-parts']:
        path=folder/f'{key}.step'
        if path.exists():return cq.importers.importStep(str(path)).val()
    raise FileNotFoundError(key)

@cache
def channel_wall():
    # One smooth envelope broadens gradually into both knee cheeks.
    sections=[(-53,-5,69,70,52),(-66,-11,69,60,40),(-92,-19,69,42,34),
              (-112,-21,69,42,42),(-130,-17,73,50,56),(-150,-6,73,54,56),
              (-170,0,73,46,56),(-184,0,73,36,50),(-194,0,73,18,40)]
    outer=oval_loft(sections)
    cavity=oval_loft([(-50,-5,69,62,44),(-66,-11,69,52,32),(-92,-19,69,34,26),
                     (-112,-21,69,34,34),(-125,-20,69,34,34),(-138,-18,69,34,30)])
    # Circular lower contour blends into the axle surround.
    lower=cyl(23,140,(0,0,-170)).fuse(box(180,180,300,(0,69,-20)))
    wall=outer.intersect(lower).cut(cavity)
    return wall.cut(cyl(53,40.5,(0,50.5,-170))).cut(box(180,90,100,(0,0,-160)))

def thigh(outer):
    old=source('thigh_outer' if outer else 'thigh_inner')
    split=box(180,90,300,(0,114 if outer else 24,-100))
    # Retain the motor interface and the integral bearing stops; replace the
    # entire lower external structure with a continuous, flared shell.
    hip=old.intersect(box(180,180,180,(0,69,26)))
    stop=old.intersect(cyl(16,140,(0,0,-170)))
    s=hip.fuse(channel_wall().intersect(split),stop)
    # Outboard nut and standard shoulder-screw thread sweep inside the cheek.
    s=s.cut(ring(36,20,11.5,79.8,-170))
    if outer:s=s.cut(cyl(9.2,12,(0,94.3,-170)))
    else:s=s.cut(cyl(7.2,12,(0,37.4,-170)))
    s=s.cut(cyl(6.1,140,(0,0,-170)))
    s=s.cut(cyl(7,38,(-34,50,-43)))
    s=s.fuse(cyl(4.1,6,(-34,88 if outer else 44,-43)))
    s=s.cut(box(21,9,44,(-22.2,70,-42)))
    boss=ring(7.5,4.1,28,55,-70,-40).intersect(split)
    s=s.fuse(boss).cut(cyl(4.1,18,(-40,58,-70))).cut(cyl(2.2,40,(-40,50,-70)))
    if outer:s=s.cut(b.hex_nut(7.2,12,-40,76,-70,.01))
    else:s=s.cut(cyl(4.1,8,(-40,50,-70)))
    if outer:s=s.cut(cyl(40.2,37.7,(0,53.5,0)))
    cleaned=s.clean()
    return cleaned if cleaned.isValid() else s

def input_crank():
    # Build the arm at its actual radius; no scaled mounting interfaces.
    base=ring(18,5,7.4,54.4)
    plate=box(RADIUS,4.8,16,(RADIUS/2,63.4,0)).fuse(cyl(8,4.8,(RADIUS,61,0)))
    a,c=b.pivot_ears(RADIUS,0)
    a=a.translate((0,-16,0));c=c.translate((0,-16,0))
    bridge=box(14,22.2,4.8,(RADIUS-1,70.9,-10.3),.7)
    for yy,depth in [(62.8,6),(78.1,7.8)]:
        bridge=bridge.fuse(box(14,depth,5.2,(RADIUS-1,yy,-7.7),.8))
    s=base.fuse(plate,a,c,bridge,cyl(10.5,11.8,(RADIUS,74.2,0)))
    for angle in range(0,360,60):
        x,z=12*math.cos(math.radians(angle)),12*math.sin(math.radians(angle))
        s=s.cut(cyl(2.2,12,(x,54,z))).cut(cyl(4,4,(x,61,z)))
    s=s.cut(cyl(5.3,6,(RADIUS,54,0))).cut(cyl(3.05,20,(RADIUS,60,0)))
    s=s.cut(cyl(6.3,8.4,(RADIUS,65.8,0))).cut(b.hex_nut(8.2,12,RADIUS,80,0,.01)).cut(cyl(2.7,12,(RADIUS,79.9,0)))
    return s.clean()

@cache
def shin_rod_space():
    points=[]
    for knee in range(-156,-47,2):
        a=math.radians(knee-78);t=math.radians(-knee)
        for end in [0,-170]:
            x=RADIUS*math.cos(a);z=170-RADIUS*math.sin(a)+end
            xx=math.cos(t)*x+math.sin(t)*z;zz=-math.sin(t)*x+math.cos(t)*z
            for u in range(0,360,30):points.append((xx+9*math.cos(math.radians(u)),zz+9*math.sin(math.radians(u))))
    points=np.array(points);outline=points[ConvexHull(points).vertices].tolist()
    plane=cq.Plane(origin=(0,65.8,0),xDir=(1,0,0),normal=(0,-1,0))
    return cq.Workplane(plane).polyline(outline).close().extrude(-8.4).val()

def shin(outer):
    old=source('shin_outer' if outer else 'shin_inner')
    # Remove the old fork above the bearing housing, then restore the complete
    # bearing wall and join the new fork with a broad radial web.
    s=old.cut(box(150,150,80,(0,67,56)))
    x,z=PIN
    yy=74.2 if outer else 55.8;depth=11.8 if outer else 10
    seat=ring(19.4,14,11,74 if outer else 51)
    web=box(16,depth,z,(x/2,yy+depth/2,z/2),1.8)
    ear=cyl(10.5,depth,(x,yy,z))
    s=s.fuse(seat,web,ear)
    # Restore the original opposing shoulders and clearance around the axle.
    s=s.fuse(ring(19.4,8.2,3,71 if outer else 62))
    s=s.cut(cyl(14,12,(0,74 if outer else 50,0))).cut(cyl(8.2,48,(0,44,0)))
    s=s.cut(cyl(5.3,6,(x,54,z))).cut(cyl(3.05,20,(x,60,z)))
    s=s.cut(cyl(6.3,8.4,(x,65.8,z))).cut(b.hex_nut(8.2,12,x,80,z,.01)).cut(cyl(2.7,12,(x,79.9,z)))
    s=s.cut(shin_rod_space())
    # Reverse the M4 clamps: low heads face the body, captured nuts face out.
    for zz in [-30,-105]:
        if outer:s=s.cut(b.hex_nut(7.2,12,2,76,zz,.01))
        else:s=s.cut(cyl(4.1,8,(2,50,zz)))
    for xx in [-12.7,12.7]:s=s.cut(cyl(1.3,16,(xx,61,0)))
    return s.clean()

def pivot_pin(x,z):
    # Conventional 6 x 20 shoulder, M5 x 9.75 thread, 10 x 4.5 head.
    s=cyl(5,4.5,(x,55.5,z)).fuse(cyl(3,20,(x,60,z)),cyl(2.5,9.75,(x,80,z)))
    socket=cq.Workplane(cq.Plane(origin=(x,55.4,z),xDir=(1,0,0),normal=(0,1,0))).polygon(6,3/(3**.5/2)).extrude(3).val()
    return s.cut(socket)

NECK_STATIONS=[(126,60,55,38,47),(142,60,82,55,68),(170,64,88,58,72),
               (200,64,88,58,72),(228,74,72,45,60),(234,90,62,38,52),(246,174,47,35,39)]

@cache
def neck_shell(include_cavity=True):
    outer=[];inner=[]
    for x,w,top,bottom,split in NECK_STATIONS:
        q=cq.Workplane('YZ',origin=(x,0,(top+bottom)/2)).rect(w,top-bottom).val()
        outer.append(q.fillet2D(min(6,(top-bottom)/2-1),q.Vertices()))
        q=cq.Workplane('YZ',origin=(x,0,(top+bottom)/2)).rect(w-10,top-bottom-10).val()
        inner.append(q.fillet2D(min(2,(top-bottom-10)/2-.2),q.Vertices()))
    solid=cq.Solid.makeLoft(outer,ruled=True)
    if include_cavity:solid=solid.cut(cq.Solid.makeLoft(inner,ruled=True))
    for side in [-1,1]:solid=solid.cut(shoulder_sweep(1,side))
    return solid

@cache
def neck_lower_region():
    wires=[]
    for x,w,top,bottom,split in NECK_STATIONS:
        wires.append(cq.Workplane('YZ',origin=(x,0,split-150)).rect(400,300).val())
    return cq.Solid.makeLoft(wires,ruled=True)

@cache
def neck_keel():
    wires=[];cavity=[]
    for x,w,top,bottom,split in NECK_STATIONS:
        ww=max(28,w-28)
        q=cq.Workplane('YZ',origin=(x,0,(split+bottom)/2)).rect(ww,split-bottom).val()
        wires.append(q.fillet2D(min(2,(split-bottom)/2-.2),q.Vertices()))
        cavity.append(cq.Workplane('YZ',origin=(x,0,(split+2+bottom+5)/2)).rect(18,max(2,split+2-bottom-5)).val())
    return cq.Solid.makeLoft(wires,ruled=True).cut(cq.Solid.makeLoft(cavity,ruled=True))

@cache
def camera_hood():
    skin=neck_shell().cut(neck_lower_region())
    face=source('front_fascia')
    s=skin.fuse(face,face.translate((-.8,0,0)),source('sensor_bezel'))
    for y in [-16,16]:
        s=s.fuse(cyl(5.5,42,(136,y,47),(0,0,1)).intersect(neck_shell(False)))
        s=s.cut(cyl(1.7,40,(136,y,40),(0,0,1))).cut(cyl(3.1,30,(136,y,55),(0,0,1)))
    return s.clean()

def camera_cradle():
    old=source('body_nose_surround')
    s=old.intersect(box(80,300,200,(281,0,0)))
    s=s.fuse(neck_shell().intersect(neck_lower_region()),neck_keel())
    # Broad saddle follows the metal crossmember and reaches both rail joints.
    yz=[(-101,36),(-97,36),(-90,43),(90,43),(97,36),(101,36),
        (101,40),(97,40),(90,47),(-90,47),(-97,40),(-101,40)]
    saddle=cq.Workplane('YZ',origin=(114,0,0)).polyline(yz).close().extrude(16).val()
    root=box(18,48,15,(132,0,44.5),1)
    s=s.fuse(saddle,root)
    # Open cable channel, with a full-width root bulkhead for hood attachment.
    # Cable cavity is formed by neck_shell().
    for side in [-1,1]:s=s.cut(shoulder_sweep(1,side))
    for x in [118,124]:
        for y in [-99,99]:
            s=s.cut(cyl(1.7,20,(x,y,27),(0,0,1))).cut(cyl(3.1,7,(x,y,38),(0,0,1)))
    for y in [-16,16]:
        s=s.cut(cyl(1.7,20,(136,y,35),(0,0,1)))
        nut=b.hex_nut(5.8,2.7,0,0,0,.01).rotate((0,0,0),(1,0,0),90).translate((136,y,41.65))
        s=s.cut(nut).cut(box(28,6,2.7,(126,y,43)))
    # A designed seam keeps hood and cradle independent for assembly.
    s=s.cut(camera_hood()).cut(source('chassis_crossmember_121')).clean()
    # Socket carving can detach tiny edge remnants; retain the connected cradle.
    pieces=sorted(s.Solids(),key=lambda q:q.Volume(),reverse=True)
    assert pieces[0].Volume()/sum(q.Volume() for q in pieces)>.995 and all(q.Volume()<100 for q in pieces[1:])
    return pieces[0]

def cached(key,make,signature):
    digest=hashlib.sha256(signature.encode()).hexdigest()
    path=OUT/'step'/f'{key}.step';meta=OUT/'cache'/f'{key}.json'
    start=time.perf_counter()
    if path.exists() and meta.exists() and json.loads(meta.read_text())['signature']==digest:
        shape=cq.importers.importStep(str(path)).val();hit=True
    else:
        shape=make();hit=False
        assert shape.isValid() and len(shape.Solids())==1,(key,shape.isValid(),len(shape.Solids()))
        cq.exporters.export(shape,str(path));cq.exporters.export(shape,str(OUT/'stl'/f'{key}.stl'),tolerance=.12,angularTolerance=.12)
        v,f=shape.tessellate(.12,.12)
        (OUT/'cache'/f'{key}-mesh.json').write_text(json.dumps({'vertices':[list(q.toTuple()) for q in v],'faces':[list(q) for q in f]},separators=(',',':')))
        meta.write_text(json.dumps({'signature':digest}))
    TIMINGS.append({'part':key,'cache_hit':hit,'seconds':time.perf_counter()-start})
    print(key,'cached' if hit else 'built',round(TIMINGS[-1]['seconds'],2),flush=True)
    return shape

def relieved_body_cover():
    trimmed=source('body_center_0').cut(box(18,204,18,(122,0,44))).cut(box(24,62,70,(138,0,60))).clean()
    # Remove the four disconnected front lip remnants left by the saddle relief.
    # Lateral chassis mounting lands remain on the main shell.
    pieces=sorted(trimmed.Solids(),key=lambda q:q.Volume(),reverse=True)
    assert pieces[0].Volume()/sum(q.Volume() for q in pieces)>.99
    return pieces[0]

def build():
    started=time.perf_counter();raw=(BASE/'model.json').read_bytes();model=json.loads(raw)
    model['parameters']['crank_radius']=RADIUS
    changed=[]
    def replace(key,fn,signature,note):
        shape=cached(key,fn,signature);changed.append(key)
        model['meshes'][key]=json.loads((OUT/'cache'/f'{key}-mesh.json').read_text())
        bb=shape.BoundingBox()
        for p in model['parts']:
            if p['mesh']==key:p.update(volume_mm3=shape.Volume(),mass_kg=shape.Volume()*b.DENSITY[p['material']],
                com_mm=list(shape.Center().toTuple()),bounds_mm=[bb.xlen,bb.ylen,bb.zlen],note=note)
        return shape
    source_stamp=hashlib.sha256(raw).hexdigest()
    def sig(*functions):return source_stamp+''.join(inspect.getsource(f) for f in functions)+str(RADIUS)
    def pair(key,fn,signature,note):
        shape=replace(key,fn,signature,note)
        replace(key+'_right',lambda:shape.mirror('XZ'),signature+'mirror-XZ',note)
    for outer in [False,True]:
        key='thigh_outer' if outer else 'thigh_inner'
        pair(key,lambda outer=outer:thigh(outer),sig(thigh,channel_wall)+str(outer),
             'Rearward closed structural thigh half with an internal pushrod channel. Hip and knee interfaces retained; larger knee fork and full assembly clearance require the candidate audit.')
        key='shin_outer' if outer else 'shin_inner'
        pair(key,lambda outer=outer:shin(outer),sig(shin,shin_rod_space)+str(outer),
             'Two-piece structural shin with integral 28 mm crank fork, complete bearing seats and reversed M4 clamps. Bearing extraction holes retained; no separate knee head.')
    pair('input_crank',input_crank,sig(input_crank),'Integrated 28 mm input crank; motor bolt pattern retained. Structural and fatigue qualification pending.')
    pair('input_pin',lambda:pivot_pin(RADIUS,0),sig(pivot_pin)+'input','Conventional 6 x 20 mm shoulder screw, M5 x 9.75 thread, 10 x 4.5 mm head facing inward. Bolt Depot 14232 dimensional envelope. Install before crank mounting; outboard captured nut. Stock quantity and strength remain unverified.')
    pair('output_pin',lambda:pivot_pin(*PIN),sig(pivot_pin)+'output','Conventional shoulder screw at the integral shin fork; recessed head faces inward and M5 nut faces outward.')
    delta=(6*math.cos(PHASE),24.2,-6*math.sin(PHASE))
    pair('output_pivot_nut',lambda:source('output_pivot_nut').translate(delta),source_stamp+str(delta),'M5 captured nut in the outer shin fork; accessible before closing the thigh.')
    for leg in ['FL','FR','RL','RR']:
        p=dict(next(p for p in model['parts'] if p['name']==leg+'_input_pin'))
        p.update(name=leg+'_input_pivot_nut',mesh='input_pivot_nut'+('_right' if leg.endswith('R') else ''),check=True)
        model['parts'].append(p)
    pair('input_pivot_nut',lambda:b.hex_nut(8,4,RADIUS,80,0,2.5),source_stamp+'conventional-pivot-nut',
         'Standard M5 nut captured in the outer input-crank ear; installed before mounting the crank to the motor.')
    pair('axle_bolt',lambda:cyl(4,55,(0,49.4,-170)).fuse(cyl(7,4.4,(0,45,-170))),source_stamp+'M8x55',
         'M8 x 55 ISO 7380 button-head screw, 14 x 4.4 mm head. Nominal thread projection 1.9 mm beyond the existing full-height nut; axle sleeve and bearing stack unchanged.')
    for suffix,z in [('37',-30),('105',-105)]:
        pair('shin_clamp_bolt_'+suffix,lambda z=z:cyl(2,25,(2,58,z)).fuse(cyl(3.8,2.2,(2,55.8,z))),source_stamp+'reverse-M4x25'+str(z),
             'M4 x 25 ISO 7380 button-head envelope, 7.6 x 2.2 mm head facing inward. Threaded tip retained within the outboard pocket; metal sleeve unchanged.')
        pair('shin_clamp_nut_'+suffix,lambda z=z:b.hex_nut(7,3.2,2,76,z,2),source_stamp+'reverse-M4nut'+str(z),
             'M4 nut captured in an outboard hex pocket, bearing directly against the existing compression sleeve.')
    pair('sleeve_0',lambda:ring(4,2.15,18,58,-70,-40),source_stamp+'rear-clamp-sleeve-18',
         '18 mm compression sleeve shared with the shin clamp specification; rear thigh clamp moved clear of the rod path.')
    pair('bolt_0',lambda:cyl(2,25,(-40,58,-70)).fuse(cyl(3.8,2.2,(-40,55.8,-70))),source_stamp+'rear-clamp-M4x25',
         'M4 x 25 button-head screw in the relocated rear thigh clamp. Low head faces inward; thread end remains inside the outer nut pocket.')
    for leg in ['FL','FR','RL','RR']:
        p=dict(next(p for p in model['parts'] if p['name']==leg+'_bolt_0'))
        p.update(name=leg+'_thigh_clamp_nut_0',mesh='thigh_clamp_nut_0'+('_right' if leg.endswith('R') else ''),check=True)
        model['parts'].append(p)
    pair('thigh_clamp_nut_0',lambda:b.hex_nut(7,3.2,-40,76,-70,2),source_stamp+'rear-clamp-M4nut',
         'M4 captured nut closes the relocated thigh clamp against its compression sleeve; installed before closing the two structural halves.')
    replace('front_fascia',camera_hood,sig(camera_hood,neck_shell,neck_lower_region)+str(NECK_STATIONS),
            'Removable curved camera hood, face and bezel form one housing part. Root screws are accessible from above; front screws retain the face against the lower cradle.')
    replace('body_nose_surround',camera_cradle,sig(camera_cradle,camera_hood,neck_shell,neck_lower_region,neck_keel)+str(NECK_STATIONS),
            'Open-top camera cradle with a broad saddle across both chassis rails. Uses the four front rail-joint locations; the metal frame tie remains installed.')
    replace('body_center_0',relieved_body_cover,
            sig(relieved_body_cover),
            'Rounded body cover with front relief for the rail-mounted camera saddle. Nominal separation at the saddle prevents the removable cover from being clamped by camera mounting bolts.')
    # The bezel is integrated into the hood; the original central head lap is gone.
    remove={'sensor_bezel','end_cap_screw_1_-18','end_cap_screw_1_18','end_cap_nut_1_-18','end_cap_nut_1_18'}
    model['parts']=[p for p in model['parts'] if p['name'] not in remove]
    template=next(p for p in model['parts'] if p['name']=='front_fascia_screw_-89_-27')
    def hardware(name,shape,note):
        p=dict(template);p.update(name=name,mesh=name,note=note,material='steel',group='body',leg=None,check=True)
        model['parts'].append(p);replace(name,lambda:shape,name+note,note)
    for y in [-16,16]:
        hardware(f'camera_hood_screw_{y}',cyl(1.5,16,(136,y,39),(0,0,1)).fuse(cyl(2.85,1.65,(136,y,55),(0,0,1))),
                 'M3 x 16 button-head hood screw envelope. Integral hood boss bears on the cradle; screw tip stays within its bulkhead.')
        hardware(f'camera_hood_nut_{y}',b.hex_nut(5.5,2.4,0,0,0,1.5).rotate((0,0,0),(1,0,0),90).translate((136,y,41.8)),
                 'M3 captured nut below the cradle clamping land. Insert from the rear access slot before attaching the cradle to the frame.')
    # Extend the existing four rail-joint fasteners upward by the saddle stack.
    for p in list(model['parts']):
        if p['name'].startswith('chassis_tie_bolt_121_'):
            points=np.asarray(model['meshes'][p['mesh']]['vertices']);cx,cy=((points.min(axis=0)+points.max(axis=0))/2)[:2]
            replace(p['mesh'],lambda cx=cx,cy=cy:cyl(1.5,10,(cx,cy,28),(0,0,1)).fuse(cyl(2.85,1.65,(cx,cy,38),(0,0,1))),
                    source_stamp+p['name']+'M3x10', 'M3 x 10 button-head screw through camera saddle and original frame tie. Existing rail nut retained.')
    model['status']='CAD candidate: rounded V0 body, closed rearward thigh, 28 mm linkage and rail-mounted camera module. Full motion and fixed-interface audit required; not a manufacturing release.'
    model['source_model_sha256']=source_stamp
    encoded=json.dumps(model,separators=(',',':')).encode();(OUT/'model.json').write_bytes(encoded)
    (OUT/'build-report.json').write_text(json.dumps({'model_sha256':hashlib.sha256(encoded).hexdigest(),'changed_parts':changed,
        'removed_parts':sorted(remove),'timings':TIMINGS,'total_seconds':time.perf_counter()-started,'scope':model['status']},indent=2))
    print('CANDIDATE',len(model['parts']),'components',len(changed),'changed meshes',flush=True)

if __name__=='__main__':build()
