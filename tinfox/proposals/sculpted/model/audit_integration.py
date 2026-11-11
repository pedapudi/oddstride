"""Verify direct structural bearing seats, radial release and captive clamp hardware."""
import json,hashlib,math
import cadquery as cq
from kinematics import ROOT,P
out=ROOT/'output';model=json.loads((out/'model.json').read_text());stamp=hashlib.sha256((out/'model.json').read_bytes()).hexdigest()
old=json.loads((ROOT.parent/'design/iterations/roll-shell-baseline/model.json').read_text())
recent=json.loads((ROOT.parent/'design/iterations/integrated-rocker-baseline/model.json').read_text())
def solid(n):return cq.importers.importStep(str(out/'step-parts'/f'{n}.step')).val()
rear=solid('shin_inner');front=solid('shin_outer');bearings=[solid('bearing_inner'),solid('bearing_outer')]
fits=[]
for a,sa,b,sb in [('rear',rear,'front',front),*[(n,s,f'bearing_{i}',q) for n,s in [('rear',rear),('front',front)] for i,q in enumerate(bearings)]]:
 v=max(0,sa.intersect(sb).Volume());fits.append({'parts':[a,b],'overlap_mm3':v});assert v<1e-4,(a,b,v)
paths=[]
def path(label,shape,obstacles,axis):
 samples=[]
 for d in [0,.05,.2,.5,1,2,4,8,15,25,40]:
  v=sum(max(0,shape.translate(tuple(d*x for x in axis)).intersect(o).Volume()) for o in obstacles)
  samples.append({'distance_mm':d,'overlap_mm3':v})
 result={'name':label,'axis':axis,'samples':samples,'passed':all(v['overlap_mm3']<1e-4 for v in samples)}
 paths.append(result);assert result['passed'],result
path('Open rear structural half after releasing clamps and pivot bolt',rear,[front,*bearings],[-1,0,0])
path('Open front structural half after releasing clamps and pivot bolt',front,[rear,*bearings],[1,0,0])
for i,b in enumerate(bearings):
 path(f'Release bearing {i} from rear semicircular seat',b,[rear],[1,0,0])
 path(f'Release bearing {i} from front semicircular seat',b,[front],[-1,0,0])
retention=[]
assembled=rear.fuse(front)
for i,b in enumerate(bearings):
 for sign in [-1,1]:
  v=max(0,b.translate((0,.5*sign,0)).intersect(assembled).Volume());assert v>1,(i,sign,v)
  retention.append({'bearing':i,'displacement_mm':.5*sign,'retaining_lip_overlap_mm3':v,'retainer':'Integral semicircular shoulder in the structural shells'})
# Standard M4 nuts enter from the open split, then the sleeves capture them.
clamps=[]
for tag in ['37','105']:
 for name in ['nut','sleeve','bolt']:
  item=solid('shin_clamp_'+name+'_'+tag)
  for n,s in [('rear',rear),('front',front)]:
   v=max(0,item.intersect(s).Volume());clamps.append({'part':name+'_'+tag,'shell':n,'overlap_mm3':v});assert v<1e-4,(name,tag,n,v)
 path('Insert M4 nut at '+tag+' mm with sleeve removed',solid('shin_clamp_nut_'+tag),[rear],[1,0,0])
 path('Withdraw captive sleeve at '+tag+' mm from rear half',solid('shin_clamp_sleeve_'+tag),[rear],[1,0,0])
x=22*math.cos(math.radians(P['crank_phase_deg']));z=-22*math.sin(math.radians(P['crank_phase_deg']))
shoulder=cq.Solid.makeCylinder(3,19.8,cq.Vector(x,62.1,z),cq.Vector(0,1,0))
assert max(0,assembled.intersect(shoulder).Volume())<1e-4
# Load the output nut through the open structural split, then close the rear half.
path('Side-load the M5 output pivot nut',solid('output_pivot_nut'),[front],[-1,0,0])
# Axle parts share the thigh frame; translate shin bearing centers to that frame.
thighs=[solid('thigh_inner'),solid('thigh_outer')]
axle=solid('knee_axle');axle_bolt=solid('axle_bolt');axle_nut=solid('axle_nut')
for name,item in [('sleeve',axle),('bolt',axle_bolt),('nut',axle_nut)]:
 for i,t in enumerate(thighs):
  v=max(0,item.intersect(t).Volume());assert v<1e-4,(name,'thigh',i,v)
path('Withdraw axle sleeve outboard with retention removed',axle,thighs,[0,1,0])
path('Withdraw recessed axle bolt inward after removing nut',axle_bolt,thighs,[0,-1,0])
for name in ['knee_axle','knee_inner_spacer']:
 item=solid(name).translate((0,0,170))
 overlap=max(0,item.intersect(assembled).Volume())
 assert overlap<1e-4,(name,'shin passage',overlap)
 fits.append({'parts':[name,'structural shin'],'overlap_mm3':overlap,'nominal_distance_mm':item.distance(assembled)})
 if name=='knee_axle':path('Slide axle out of assembled structural bearing housing',item,[assembled],[0,1,0])
names=[p['name'] for p in model['parts']]
assert not any(n.endswith(('_knee_head','_shoulder_cover')) for n in names)
assert len([n for n in names if '_shin_clamp_bolt_' in n])==8
force=17/(P['crank_radius']/1000*min(abs(math.cos(math.radians(k+P['crank_phase_deg']))) for k in range(-156,-47)))
span=14.2;bending=force*span/4/(math.pi*6**3/32);shear=force/(2*math.pi*6**2/4)
counts={'old_total_instances':len(old['parts']),'new_total_instances':len(model['parts']),'custom_leg_components_removed_net':8,'previous_two_piece_total_instances':len(recent['parts']),'parts_removed_since_two_piece':len(recent['parts'])-len(model['parts']),'main_shell_parts_per_leg':4,'separate_knee_heads':0,'separate_shoulder_covers':0,'shin_clamp_bolts_per_leg':2,'reason':'Two thigh halves and two fore/aft shin halves carry the joint interfaces. The shin halves contain the rocker and split bearing seats; the hip shroud is integral with its carrier.'}
report={'model_sha256':stamp,'counts':counts,'fits':fits,'paths':paths,'bearing_retention':retention,'clamp_fits':clamps,'bearing_center_spacing_mm':20,'pin_screen':{'rod_force_N':force,'support_centroid_span_mm':span,'nominal_bending_MPa':bending,'average_double_shear_MPa':shear,'nominal_vm_MPa':math.sqrt(bending*bending+3*shear*shear),'scope':'Nominal 6 mm shoulder screw, simply supported; excludes fatigue, stress concentration and printed ear compliance.'},'retaining_shoulder_thickness_mm':3,'remaining':['Axle clamp preload and selected bearing fits','Roll-bearing retaining flanges/preload','Motor axial tie stack','Foot retention and cable routing','Printed fork, carrier, clamp creep and fatigue qualification'],'scope':'Exact-solid bench service paths. Opening the structural split replaces blind-pocket pressing; bearings need not be driven through a retaining shoulder. Actual fit, roundness and free running require physical checks.'}
(out/'integration-audit.json').write_text(json.dumps(report,indent=2));print('Integral rocker, split bearing seats, radial service paths and M4 clamp fits passed.')
