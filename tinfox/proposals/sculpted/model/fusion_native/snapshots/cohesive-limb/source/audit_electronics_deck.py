"""Check the flat deck, independent attachments and export planar cutting profiles."""
import json,hashlib
from pathlib import Path
import cadquery as cq
import ezdxf
from kinematics import ROOT,P
from build import box,cyl
out=ROOT/'output';raw=(out/'model.json').read_bytes();model=json.loads(raw);stamp=hashlib.sha256(raw).hexdigest()
audit=json.loads((out/'assembly-audit.json').read_text());plan=json.loads((out/'manufacturing-plan.json').read_text())
assert audit['model_sha256']==stamp and audit['passed']
assert plan['model_sha256']==stamp
parts={p['name']:p for p in model['parts']}
def shape(n):return cq.importers.importStep(str(out/'step-parts'/f'{n}.step')).val()
deck=shape('electronics_shelf');brace=shape('chassis_lower_brace');b=deck.BoundingBox()
assert abs(b.xlen-134)<.001 and abs(b.ylen-186)<.001 and abs(b.zlen-4)<.001
assert len(deck.Solids())==1 and deck.isValid()
# A constant cross-section and no downward faces above the bed establish the
# support-free geometric orientation; actual slicing is still required.
section=deck.intersect(box(160,210,.1,(0,0,5.5)))
assert abs(section.Volume()/.1*4-deck.Volume())<.01
record=next(p for p in plan['parts'] if p['id']=='electronics_shelf')
assert record['route']=='printed'
assert record['screen']['downward_projected_area_mm2']<1e-3
assert abs(record['print_bounds_mm'][2]-4)<.001
for path in audit['paths']:
 if 'electronics_shelf' in path['moving_parts']:
  assert 'battery_cassette' not in path['removed_before']
  assert 'chassis_lower_brace' not in path['removed_before']
  assert not any(n.startswith('cassette_screw_') for n in path['removed_before'])
 if 'battery_cassette' in path['moving_parts']:
  assert 'electronics_shelf' not in path['removed_before']
  assert 'chassis_lower_brace' not in path['removed_before']
assert sum(n.startswith('tray_screw_') for n in parts)==4
assert sum(n.startswith('cassette_screw_') for n in parts)==4
assert sum(n.startswith('chassis_brace_screw_') for n in parts)==4
clearances=[]
for side in [-1,1]:
 battery=box(*P['battery_envelope_mm'],(0,side*44.5,P['battery_center_z']),7)
 for x in [-52,52]:
  screw=cyl(1.5,8,(x,side*88,-.5),(0,0,1)).fuse(cyl(2.75,3,(x,side*88,7.5),(0,0,1)))
  overlap=max(0,screw.intersect(battery).Volume());gap=screw.distance(battery)
  assert overlap<1e-4 and gap>1.0,(side,x,gap)
  clearances.append({'side':side,'x_mm':x,'battery_to_deck_screw_mm':gap})
patterns=out/'flat-patterns';patterns.mkdir(exist_ok=True)
for n,s,z in [('electronics_shelf',deck,5.5),('chassis_lower_brace',brace,2)]:
 wp=cq.Workplane('XY').add(s).section(z)
 cq.exporters.export(wp,str(patterns/(n+'.dxf')),exportType='DXF')
 doc=ezdxf.readfile(patterns/(n+'.dxf'));assert len(doc.modelspace())>0
 assert doc.header.get('$INSUNITS')==4,'DXF must declare millimetres'
old=json.loads((ROOT.parent/'design/iterations/electronics-deck-baseline/model.json').read_text())
old_mass=sum(p['mass_kg'] for p in old['parts']);new_mass=sum(p['mass_kg'] for p in model['parts'])
report={'model_sha256':stamp,'deck_dimensions_mm':[b.xlen,b.ylen,b.zlen],'deck_mass_g':parts['electronics_shelf']['mass_kg']*1000,'fixed_brace_mass_g':parts['chassis_lower_brace']['mass_kg']*1000,'assembly_mass_delta_g':(new_mass-old_mass)*1000,'flat_section_verified':True,'designed_support_area_mm2':record['screen']['downward_projected_area_mm2'],'computer_to_roof_gap_mm':audit['computer_to_roof_gap_mm'],'battery_screw_clearances':clearances,'independent_service_paths':True,'scope':'Nominal solids, sampled service paths and geometric print orientation. No slicer toolpath, thread pullout, frame racking, printed creep or thermal test.'}
(out/'electronics-deck-audit.json').write_text(json.dumps(report,indent=2))
(patterns/'README.txt').write_text('''TINFOX FLAT CUTTING PROFILES — MILLIMETRES

Electronics deck: the current part is 4 mm PETG, printed flat. The DXF is a
profile candidate for later flat cutting or CNC. A thinner aluminum version
requires revised screw lengths, equipment height and a stiffness check.

Fixed lower brace: 3 mm aluminum candidate. The midplane DXF gives the cut
outline and holes. Finish the four 2.5 mm pilot holes as M3 x 0.5 threads;
four 3.4 mm holes are rail clearances. Deburr edges. The STEP includes small
edge radii that a cutting operation alone does not produce.

Confirm available stock thickness, cutting process, hole limits and tapping
with the fabricator. These files are not a manufacturing release.
''')
print(json.dumps(report,indent=2))
