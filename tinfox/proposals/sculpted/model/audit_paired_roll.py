"""Check exported paired-bearing interfaces and the bench assembly sequence."""
import hashlib,itertools,json,math
from functools import cache
import cadquery as cq
import build as b
import paired_roll as design
import service_design as sd
from kinematics import ROOT

OUT=ROOT/'output/paired-roll-work'
raw=(OUT/'model.json').read_bytes();data=json.loads(raw);rows=[]
@cache
def solid(key):
    p=OUT/'step'/(key+'.step')
    if not p.exists():
        for folder in ['output/limb-refinement/step','output/service-design/step','output/step-parts']:
            p=ROOT/folder/(key+'.step')
            if p.exists():break
    return cq.importers.importStep(str(p)).val()
def overlap(a,c):return max(0,sum(s.Volume() for s in a.intersect(c).Solids()))
def fit(label,a,c):
    v=overlap(a,c);rows.append(dict(check=label,overlap_mm3=v,passed=v<.005))
def gap(label,a,c,required):
    d=a.distance(c);rows.append(dict(check=label,gap_mm=d,required_mm=required,passed=d>=required-1e-6))

for front in [1,-1]:
    h=solid(f'roll_cartridge_{front}');ret=solid(f'roll_outer_retainer_{front}')
    back=solid(f'roll_stator_backplate_{front}')
    cup=solid(f'motor_carrier_{front}');closure=solid(f'hip_stator_closure_{front}')
    bearings=[solid(f'roll_bearing_6810_{front}_{i}') for i in [0,1]]
    static=cq.Compound.makeCompound([h,back,ret,*bearings,solid(f'roll_outer_spacer_{front}')])
    moving=cq.Compound.makeCompound([cup,closure,solid(f'roll_inner_backplate_{front}'),solid(f'roll_inner_spacer_{front}')])
    fit(str(front)+' fixed/moving assembly',static,moving)
    hw={key:solid(key+f'_front{front}') for key in design.hardware()}
    for key,s in hw.items():
        fit(str(front)+' hardware / cup '+key,cup,s)
        fit(str(front)+' hardware / closure '+key,closure,s)
        fit(str(front)+' hardware / housing '+key,h,s)
        fit(str(front)+' hardware / rear stator plate '+key,back,s)
        fit(str(front)+' hardware / outer retainer '+key,ret,s)
    motor=b.motor_envelope()
    motor=motor.fuse(*[sd.connector_parts(0,sign)[0] for sign in [-1,1]]).translate((front*design.PARAMETERS['pitch_x_offset'],0,0))
    for dy in [0,.1,.5,1,2,4,8,16,32,48,80]:
        fit(str(front)+' motor and sockets insertion '+str(dy),cup,motor.translate((0,dy,0)))
        fit(str(front)+' closure removal '+str(dy),cup,closure.translate((0,dy,0)))
    # Inner backplate enters the stationary cartridge from the motor side,
    # before the cartridge is attached to the roll actuator.
    for dx in [0,.1,1,4,8,16,32]:
        fit(str(front)+' rear stator plate removal '+str(dx),h,back.translate((-front*dx,0,0)))
        fit(str(front)+' backplate rear insertion '+str(dx),h,
            solid(f'roll_inner_backplate_{front}').translate((-front*dx,0,0)))
        fit(str(front)+' rear bearing front insertion '+str(dx),h,
            bearings[0].translate((front*dx,0,0)))
        fit(str(front)+' front bearing front insertion '+str(dx),h,
            bearings[1].translate((front*dx,0,0)))
        fit(str(front)+' outer spacer insertion '+str(dx),h,
            solid(f'roll_outer_spacer_{front}').translate((front*dx,0,0)))
        pack=cq.Compound.makeCompound([*bearings,solid(f'roll_outer_spacer_{front}')])
        fit(str(front)+' outer-race pack through-bore removal '+str(dx),h,pack.translate((front*dx,0,0)))
    driver=design.annulus_x(32.4,31.6,design.layout()['rear']-12,design.layout()['rear'])
    if front<0:driver=driver.mirror('YZ')
    fit(str(front)+' rear outer-race driver access',h,driver)
    v=overlap(bearings[0],driver.translate((front*.05,0,0)))
    rows.append(dict(check=str(front)+' driver contacts rear outer race',contact_probe_mm3=v,passed=v>1))
    for a in range(0,360,60):
        y,z=design.polar(12,a)
        tool=b.cyl(2.5,120,(design.layout()['end']-2,y,z),(1,0,0))
        if front<0:tool=tool.mirror('YZ')
        fit(str(front)+' roll screw straight driver '+str(a),cup,tool)
    for a in design.CUP_ANGLES:
        x,z=design.polar(47,a)
        for travel in [0,.5,2,5,10,20]:
            dx,dz=design.polar(travel,a)
            fit(str(front)+' closure nut radial insertion '+str(a)+' / '+str(travel),cup,
                hw[f'carrier_closure_nut_{a}'].translate((dx,0,dz)))
        # Small inward probe proves the washer/head reaches structural material.
        washer=hw[f'carrier_closure_washer_{a}']
        v=overlap(closure,washer.translate((0,-.05,0)))
        rows.append(dict(check=str(front)+' closure washer support '+str(a),contact_probe_mm3=v,passed=v>.1))
    # Relative roll does not change moving-component positions inside this group.
    for roll in range(-60,61,2):
        moved=moving.rotate((0,0,0),(1,0,0),roll)
        fit(str(front)+' roll support sweep '+str(roll),static,moved)

report=dict(model_sha256=hashlib.sha256(raw).hexdigest(),checks=rows,passed=all(r['passed'] for r in rows),
    scope='Exported nominal solids and sampled assembly paths. Roll-output drivers checked with hip motor removed. Thread contact with vendor motor internals is not modeled. Fit, preload, deflection and powered-operation strength are unqualified.')
(OUT/'paired-roll-interfaces.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'checks':len(rows),'passed':report['passed'],'failed':[r for r in rows if not r['passed']]}),flush=True)
