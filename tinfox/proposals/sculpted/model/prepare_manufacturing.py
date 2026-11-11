"""Create oriented, unsliced part files and a measured fabrication inventory."""
import csv,hashlib,json,math,zipfile,html
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation
from kinematics import ROOT,P
from cad_authority import require_generated_authority
require_generated_authority(ROOT)
OUT=ROOT/'output';DEST=OUT/'manufacturing';DEST.mkdir(exist_ok=True)
for d in ['printed-stl','printed-step','cnc-step','fit-only-stl','plates']:
 (DEST/d).mkdir(exist_ok=True)
 for old in (DEST/d).iterdir():
  if old.is_file():old.unlink()
model=json.loads((OUT/'model.json').read_text());stamp=hashlib.sha256((OUT/'model.json').read_bytes()).hexdigest()
catalog=json.loads((OUT/'parts-catalog.json').read_text());assert catalog['model_sha256']==stamp
BED=np.array([325.,320.,325.]);USABLE=BED-np.array([20,20,10]);records=[];oriented={}

def rot(axis,angle):
 m=np.eye(4);m[:3,:3]=Rotation.from_euler(axis,angle,degrees=True).as_matrix();return m

def category(p):
 k=p['id']
 if p['material']=='petg':return 'printed'
 if p['material']=='rubber':return 'elastomer-fit'
 if k.startswith(('axle_bolt','axle_nut','shin_clamp_bolt','shin_clamp_nut','output_pivot_nut','bearing_','pod_tie_','bolt_','input_pin','output_pin','shin_head_bolt','shin_head_nut','shin_head_washer','knee_retaining_ring','shin_join_bolt','shin_join_nut','shin_join_washer')) or k=='lidar_lid':return 'purchased'
 if k.startswith(('shin_clamp_sleeve','sleeve_','pod_sleeve_','knee_axle','knee_inner_spacer','shin_join_sleeve')):return 'stock-fabrication'
 if p['material']=='aluminum' or k in ['pushrod','pushrod_right']:return 'machining'
 return 'stock-fabrication'

def guidance(k):
 base=k.removesuffix('_right')
 if base=='body_center_0':return ('Roof exterior down; integral side walls rise upward.','Interior remains open. Local support at display recess, curved roof perimeter and side screw bosses; no trapped bottom cavity.','Top-and-side shell requires two setups and thin-wall workholding; preserve lift-off clearance to frame.')
 if base.startswith('body_center_side'):return ('Broad exterior side down.','Small rounded perimeter may need a brim; upper edge is separated from the roof.','Two face setups; finish upper mounting holes after assembly fit check.')
 if base=='electronics_shelf':return ('Flat underside on bed; all holes and slots vertical.','Constant 4 mm extrusion; no designed bridges or supports. Inspect hole compensation and first layer in the slicer.','Flat cut plate candidate with drilled slots; a future thinner metal version needs a stiffness and mounting-height review.')
 if base=='chassis_lower_brace':return ('Broad flat face on bed for an unloaded fit mockup.','Constant 3 mm plate; vertical holes, no designed supports. Use metal for the structural frame candidate.','Flat-cut aluminum outline, clearance holes and four tapped deck mounts. Verify threads and rail-joint strength before loaded use.')
 if base=='motor_service_ring':return ('Flat split face on bed; motor axis vertical.','Open center permits support removal; inspect the short tie bosses in the slicer.','Separate ring avoids machining a captive motor-plate recess.')
 if base=='knee_head':return ('Bench fit mockup only; bearing axis vertical.','Use metal for the load path. Open-ended bearing seats and fork allow tool access.','One machined head with opposed bearing bores, integral pushrod fork and keyed tongue; finish bore coaxiality and pin seats in common setups.')
 if base=='thigh_inner':return ('Motor axis near vertical; leg length lies along the bed.','Support below the offset thigh web; the motor-plate recess is now open; use accessible support regions, not filled motor or bearing bores.','Open-ended motor cup and removable outer clamshell improve tool access; finish the motor and sleeve seats from common datums.')
 if base=='thigh_outer':return ('Exterior down, open structural cavity up; leg length along the bed.','Local support beneath the exterior and integral service-ring webs; keep the cavity accessible and inspect the collar roots layer by layer.','Two setups with a ball-end finish on the outer skin; keep joint datum faces and compression-sleeve seats.')
 if base.startswith('shin_') and 'carrier' not in base:return ('Fore/aft exterior down, split face upward. Limb length and bearing axis lie in the bed plane.','Use removable local support beneath the rounded exterior and bearing lip. Use both halves, broad mating lands and compression sleeves. Joint slip and layer separation remain unqualified.','Machine the open structural halves, then finish the split bearing bores with the halves bolted against their closure stops. The fork is integral; no internal head is installed.')
 if base.startswith('shoulder_cover'):return ('Annular end on bed, motor axis vertical.','Support at the internal annular step and local carrier relief; support must pull out through the open end.','Deep thin-wall cowling; turning plus milling or a split cover is preferable to deep-pocket milling.')
 if base in ['front_fascia','sensor_bezel']:return ('Rear rim down, convex exterior upward.','Shallow supports beneath the curved rear skin and bezel; keep support off the visible face and screw holes.','Two setups; retain front perimeter and sensor-opening datums.')
 if base=='body_nose_surround':return ('Front rim toward bed; tongue rises upward.','Support beneath return tongue and fascia posts; remove through open rear.','Thin curved wrap with return tongue; multiple setups and workholding tabs need planning.')
 if base=='battery_cassette':return ('Closed base on bed; open pack cavity upward.','Continuous sloped webs support the guide edges; inspect local overhangs in the slicer. Keep the four top-loading nut pockets open; print the cassette base down.','Deep thin-wall enclosure; use an assembled sheet enclosure if machining cost dominates.')
 if base.startswith(('body_','belly_')):return ('Measured orientation minimizes the screened overhang area among axial candidates.','Local supports at compound curves, ribs and shoulder recesses; inspect layer preview before printing.','Thin compound shell; two setups and soft jaws or a vacuum fixture need review.')
 if base.startswith('foot'):return ('Flat neck toward bed; sole upward.','TPU shape/fit prototype only. The boot retention cavity and fastener are not yet detailed.','Elastomer part: print TPU or develop a mold; do not mill this as a rigid metal foot.')
 if base.startswith(('motor_carrier','roll_cartridge')):return ('Flange face on bed for a fit-only mockup.','Plastic mockup cannot replace the metal actuator load path.','Multi-setup machining; bore/journal, perpendicular flange and fastener access require supplier review.')
 if base=='input_crank':return ('Motor face on bed for a fit mockup.','Fork overhangs require accessible local support; metal production part.','One stepped motor-output coupling and double-shear crank. Finish pilot, bolt circle, pin shoulder bore and M5 thread.')
 if base in ['output_crank','pushrod']:return ('Broad plate face on bed for a fit-only mockup.','Fit-only: retain metal for the loaded linkage.','Plate blank plus drilled/reamed pin holes; finish mating seats and edge radii.')
 return ('Broad stable face on bed.','Inspect small holes, edge overhangs and first-layer adhesion.','Review stock form, tool reach, setup datums and hole tolerances before CAM.')

def orientations(k):
 side=-1 if k.endswith('_right') else 1;base=k.removesuffix('_right')
 if base in ['electronics_shelf','chassis_lower_brace']:return [np.eye(4)]
 if base=='body_center_0':return [rot('x',180)]
 if base.startswith('body_center_side'):return [rot('x',-90*int(base.rsplit('_',1)[1]))]
 if base=='motor_service_ring':return [rot('x',90*side)]
 if base=='thigh_outer':return [rot('x',-90*side)]
 if base=='thigh_inner':return [rot('x',a*side) for a in [90,-90]]
 if base in ['shin_inner','shin_outer','shin_shell']:return [rot('y',-90 if base=='shin_inner' else 90)]
 if base in ['front_fascia','sensor_bezel']:return [rot('y',-90)]
 if base=='body_nose_surround':return [rot('y',90)]
 if base.startswith('shoulder_cover'):return [rot('x',90),rot('x',-90)]
 if base=='battery_cassette':return [np.eye(4)]
 if base.startswith('foot'):return [rot('x',180)]
 return [np.eye(4),rot('x',180),rot('x',90),rot('x',-90),rot('y',90),rot('y',-90)]

def screen(mesh):
 normals=mesh.face_normals;centers=mesh.triangles_center;area=mesh.area_faces
 down=(normals[:,2]<-math.cos(math.radians(45)))&(centers[:,2]>.5)
 projection=area[down]*(-normals[down,2]);a=float(projection.sum())
 contact=float(area[(normals[:,2]<-.9)&(centers[:,2]<.25)].sum())
 h=float((projection*centers[down,2]).sum()/max(a,1e-9))
 return {'downward_projected_area_mm2':a,'area_weighted_overhang_height_mm':h,'near_bed_downward_area_mm2':contact,
         'score':a*(1+h/35)-min(contact,1500)*.15}

for p in catalog['parts']:
 k=p['id'];route=category(p);note,support,cnc=guidance(k)
 if route=='purchased':
  note='Purchased component; CAD envelope for assembly review.';support='Select the actual bearing, fastener or sensor component before assembly.';cnc='Verify vendor dimensions and retention; no machining operation is specified.'
 elif route=='stock-fabrication':
  note='Cut and finish stock tube or rod to the modeled dimensions.';support='Use the specified metal stock; no production print orientation is assigned.';cnc='Deburr and finish end faces, bores and pin fits as required by the mating assembly.'
 rec={'id':k,'title':p['title'],'quantity':p['quantity'],'route':route,'material':p['material'],'step':p['step'],'step_sha256':p['step_sha256'],'orientation_note':note,'support_note':support,'machining_note':cnc}
 if route not in ['purchased','stock-fabrication']:
  src=trimesh.load_mesh(OUT/p['stl']);src.merge_vertices(digits_vertex=4);src.update_faces(src.nondegenerate_faces());src.update_faces(src.unique_faces());src.remove_unreferenced_vertices()
  candidates=[]
  for m in orientations(k):
   trial=src.copy();trial.apply_transform(m);lo,hi=trial.bounds
   if hi[0]-lo[0]>USABLE[0] or hi[1]-lo[1]>USABLE[1]:
    r=rot('z',90);m=r@m;trial=src.copy();trial.apply_transform(m);lo,hi=trial.bounds
   shift=np.array([-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]])
   trial.apply_translation(shift);m=m.copy();m[:3,3]+=shift
   result=screen(trial);result['fits']=bool(np.all(trial.extents<=USABLE));result['matrix']=m.tolist()
   candidates.append((result,trial))
  eligible=[v for v in candidates if v[0]['fits']];assert eligible,k
  chosen,mesh=min(eligible,key=lambda v:v[0]['score']);rec.update(print_bounds_mm=mesh.extents.tolist(),transform=chosen['matrix'],screen=chosen,orientation_candidates=[a for a,_ in candidates])
  folder='printed-stl' if route in ['printed','elastomer-fit'] else 'fit-only-stl'
  dest=DEST/folder/(k+'.stl');mesh.export(dest);rec['oriented_stl']=str(dest.relative_to(OUT));rec['stl_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest()
  assert mesh.is_watertight and mesh.volume>0,k
  if route=='printed':mesh.export(OUT/'print-stl'/f'{k}.stl')
  if route in ['printed','elastomer-fit']:
   oriented[k]=mesh
   (DEST/'printed-step'/f'{k}.step').write_bytes((OUT/p['step']).read_bytes())
  if route=='machining':
   (DEST/'cnc-step'/f'{k}.step').write_bytes((OUT/p['step']).read_bytes());rec['cnc_step']=f'manufacturing/cnc-step/{k}.step'
 records.append(rec)
 print(k,route,flush=True)

# Conservative rectangular nesting keeps every instance inside the brim allowance.
plates=[]
for material in ['petg','rubber']:
 instances=[(r,copy) for r in records if r['id'] in oriented and r['material']==material for copy in range(r['quantity'])]
 instances.sort(key=lambda pair:tuple(-v for v in sorted(pair[0]['print_bounds_mm'][:2],reverse=True)))
 for r,copy in instances:
  w,d=r['print_bounds_mm'][:2];found=None
  for plate in plates:
   if plate['material']!=material:continue
   for row in plate['rows']:
    if d<=row['depth'] and row['x']+w<=315:
     found=(plate,row);break
   if found:break
   y=max([10]+[row['y']+row['depth']+10 for row in plate['rows']])
   if y+d<=310:
    row={'x':10.,'y':y,'depth':d};plate['rows'].append(row);found=(plate,row);break
  if not found:
   plate={'id':len(plates)+1,'material':material,'rows':[{'x':10.,'y':10.,'depth':d}],'parts':[]};plates.append(plate);found=(plate,plate['rows'][0])
  plate,row=found;plate['parts'].append({'id':r['id'],'copy':copy+1,'center_mm':[row['x']+w/2,row['y']+d/2,0],'bounds_mm':r['print_bounds_mm']});row['x']+=w+10

NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',NS)
for plate in plates:
 root=ET.Element(f'{{{NS}}}model',{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
 ET.SubElement(root,'metadata',{'name':'Title'}).text=f'Tinfox plate {plate["id"]} — unsliced geometry'
 resources=ET.SubElement(root,'resources');build=ET.SubElement(root,'build');ids={}
 for item in plate['parts']:
  k=item['id'];mesh=oriented[k]
  if k not in ids:
   oid=str(len(ids)+1);ids[k]=oid;obj=ET.SubElement(resources,'object',{'id':oid,'type':'model','name':k});mm=ET.SubElement(obj,'mesh');vv=ET.SubElement(mm,'vertices');ff=ET.SubElement(mm,'triangles')
   for v in mesh.vertices:ET.SubElement(vv,'vertex',dict(zip(['x','y','z'],[f'{x:.5f}' for x in v])))
   for f in mesh.faces:ET.SubElement(ff,'triangle',dict(zip(['v1','v2','v3'],map(str,f))))
  x,y,z=item['center_mm'];ET.SubElement(build,'item',{'objectid':ids[k],'transform':f'1 0 0 0 1 0 0 0 1 {x:.5f} {y:.5f} {z:.5f}'})
 name=f'plate-{plate["id"]:02d}.3mf';plate['file']='manufacturing/plates/'+name
 with zipfile.ZipFile(DEST/'plates'/name,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
  z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
  z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
 plate.pop('rows')
 # Render the projected CAD triangles, not rectangles standing in for the parts.
 svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 365 375">','<rect width="365" height="375" fill="#eeeee7"/>','<rect x="20" y="25" width="325" height="320" fill="#dce2d5" stroke="#617164"/>','<rect x="30" y="35" width="305" height="300" fill="none" stroke="#a1ada0" stroke-dasharray="3 3"/>',f'<text x="20" y="17" font-size="11" font-family="sans-serif">Plate {plate["id"]:02d} · {"TPU fit samples" if plate["material"]=="rubber" else "PETG"}</text>']
 for item in plate['parts']:
  mesh=oriented[item['id']];v=mesh.vertices[:,:2]+np.array(item['center_mm'][:2]);v[:,0]+=20;v[:,1]=345-v[:,1]
  for face in mesh.faces:
   xy=v[face];svg.append('<path d="M'+' L'.join(f'{x:.2f},{y:.2f}' for x,y in xy)+' Z" fill="#59685d"/>')
  x,y,_=item['center_mm'];svg.append(f'<text x="{20+x:.1f}" y="{345-y:.1f}" font-size="5" text-anchor="middle" fill="#f6f4e9" font-family="sans-serif">{html.escape(item["id"])}</text>')
 svg.append('<text x="20" y="363" font-size="9" font-family="sans-serif">325 × 320 mm · unsliced · inspect supports before printing</text></svg>')
 (DEST/'plates'/name.replace('.3mf','.svg')).write_text(''.join(svg))

report={'model_sha256':stamp,'units':'mm','printer':'Bambu Lab H2D single nozzle','build_volume_mm':BED.tolist(),'usable_with_margins_mm':USABLE.tolist(),'scope':'Unsliced geometry and orientation screening. Downward projected area includes bridges and surfaces supported by other portions of the same part; it is not slicer support volume or a support-free certification. Orientations retain long structural links near the XY plane.','parts':records,'plates':plates}
(OUT/'manufacturing-plan.json').write_text(json.dumps(report,indent=2))
with (DEST/'inventory.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['part','quantity','route','material','oriented size mm','orientation','supports','machining considerations'])
 for r in records:w.writerow([r['id'],r['quantity'],r['route'],r['material'],' x '.join(f'{v:.1f}' for v in r.get('print_bounds_mm',[])),r['orientation_note'],r['support_note'],r['machining_note']])
# Keep the catalog's part-specific manufacturing advice available in the existing viewer.
lookup={r['id']:r for r in records}
for p in catalog['parts']:
 r=lookup[p['id']];p['fabrication']=r;p['manufacturing']=r['support_note']+' '+r['machining_note']
(OUT/'parts-catalog.json').write_text(json.dumps(catalog,indent=2))
print(f'{len(records)} records; {len(oriented)} printable geometries; {len(plates)} unsliced plates',flush=True)
# The existing individual CAD download must carry the same catalog as the viewer.
readme='''TINFOX INDIVIDUAL CAD SOLIDS\nUnits: millimetres. STEP solids retain local assembly coordinates.\nConsult manufacturing-plan.json for quantities, routes, print orientations and support notes.\nPrinted geometry, machining candidates and purchased hardware are distinguished in the catalog.\nPlastic fit mockups of actuator mounts and cranks are not approved load-bearing substitutes.\n'''
with zipfile.ZipFile(OUT/'tinfox-individual-cad.zip','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('README.txt',readme);z.write(OUT/'parts-catalog.json','parts-catalog.json');z.write(OUT/'manufacturing-plan.json','manufacturing-plan.json')
 for p in catalog['parts']:z.write(OUT/p['step'],p['step'])
