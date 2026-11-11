"""Export a labelled dimensional coupon; it is not an installed robot component."""
import cadquery as cq
import json,hashlib
from kinematics import ROOT
out=ROOT/'output/print-fixtures';out.mkdir(exist_ok=True)
s=cq.Workplane('XY').box(140,94,5,centered=(True,True,False)).edges('|Z').fillet(3).val()
def hole(x,y,d):
 global s
 s=s.cut(cq.Solid.makeCylinder(d/2,7,cq.Vector(x,y,-1)))
 # A top lead-in does not change the labelled cylindrical diameter.
 s=s.cut(cq.Solid.makeCone(d/2,d/2+.4,.4,cq.Vector(x,y,4.6)))
def label(text,x,y):
 global s
 t=cq.Workplane('XY').text(text,3,.4,combine=True).val().translate((x,y,4.6));s=s.cut(t)
for x,d in zip([-45,0,45],[34.0,34.2,34.4]):hole(x,20,d);label(str(d),x,-1)
label('CARRIER OD 34 / NOMINAL BORE',0,43)
for x,d in zip([-53,-33,-13],[3.2,3.4,3.6]):hole(x,-17,d);label(str(d),x,-26)
for x,d in zip([12,32,52],[5.2,5.4,5.6]):hole(x,-17,d);label(str(d),x,-26)
for x,af in zip([-32,0,32],[5.6,5.8,6.0]):
 pocket=cq.Workplane('XY',origin=(x,-37,2.2)).polygon(6,af/(3**.5/2)).extrude(3).val();s=s.cut(pocket);hole(x,-37,3.2);label(str(af)+' AF',x+12,-37)
assert s.isValid() and len(s.Solids())==1
for ext in ['step','stl']:cq.exporters.export(s,str(out/('dimensional-coupon.'+ext)))
reopened=cq.importers.importStep(str(out/'dimensional-coupon.step')).val();assert reopened.isValid()
(out/'README.txt').write_text('DIMENSIONAL FIT COUPON — 140 x 94 x 5 mm\nPrint flat, labels upward, in the same material/profile as the limb. No support is needed for the vertical holes and top-open pockets. The 34 mm series checks the metal shin-carrier OD, not a bare 28 mm bearing. Small circular holes check M3 clearance and 5 mm sleeve clearance. Hex pockets check M3 nut fit; AF means across flats. Measure after cooling; record actual hardware fits and tune clearance parameters before full-size printing. This is a dimensional coupon, not a strength test. Do not press bearings directly into plastic based on this result.\n')
(out/'coupon-verification.json').write_text(json.dumps({'valid':True,'dimensions_mm':[140,94,5],'step_sha256':hashlib.sha256((out/'dimensional-coupon.step').read_bytes()).hexdigest(),'installed_component':False},indent=2));print('Dimensional fit coupon exported and STEP reopened.')
