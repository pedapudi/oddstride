"""Open, seated DIN7991 knee-stator fasteners within the existing plate envelope."""
class KneeStatorSeatIntent(SlimMountIntent):
 def seats(self,body):
  g=self.g;c=self.c
  g.parameter('ks_head_nominal_diameter',5.9,comment='Existing DIN7991 M3 reference head diameter; verify purchased screws, not an ISO10642 equivalence claim.')
  g.parameter('ks_seat_diametral_allowance',0,comment='Conical seating fit allowance; zero preserves contact with the nominal reference head.')
  g.parameter('ks_head_included_angle',90,'deg')
  g.parameter('ks_seat_radius','(ks_head_nominal_diameter+ks_seat_diametral_allowance)/2')
  g.parameter('ks_seat_depth','(ks_seat_radius-sm_stator_hole_radius)/tan(ks_head_included_angle/2)')
  g.parameter('ks_head_top_y','sm_stator_mount_plane')
  g.parameter('ks_seat_bottom_y','ks_head_top_y-ks_seat_depth')
  g.parameter('ks_clock',20,'deg')
  x='sm_stator_pcd_radius*cos(ks_clock)';z='sm_stator_pcd_radius*sin(ks_clock)'
  plane=g.plane(c.xYConstructionPlane,z,'Knee stator seat axial section datum');sk=c.sketches.add(plane);sk.name='One 90 degree countersink section';sk.isComputeDeferred=True
  expressions=[(x,'ks_seat_bottom_y'),(f'({x})+sm_stator_hole_radius','ks_seat_bottom_y'),(f'({x})+ks_seat_radius','ks_head_top_y'),(x,'ks_head_top_y')]
  points=[];xs={};ys={}
  for px,py in expressions:
   p=g.skeleton_point(sk,px,py);g.point_dimensions(sk,p,None if px in xs else px,None if py in ys else py)
   if px in xs:sk.geometricConstraints.addVerticalPoints(xs[px],p)
   if py in ys:sk.geometricConstraints.addHorizontalPoints(ys[py],p)
   xs[px]=p;ys[py]=p;points.append(p)
  for i,p in enumerate(points):sk.sketchCurves.sketchLines.addByTwoPoints(p,points[(i+1)%4])
  axis=sk.sketchCurves.sketchLines.addByTwoPoints(points[0],points[3]);axis.isConstruction=True
  sk.isComputeDeferred=False;assert sk.profiles.count==1
  inp=c.features.revolveFeatures.createInput(sk.profiles.item(0),axis,fusion.FeatureOperations.CutFeatureOperation);inp.participantBodies=[body];inp.setAngleExtent(False,g.value('360 deg'));f=c.features.revolveFeatures.add(inp);f.name='Open DIN7991 M3 seating cone';sk.isVisible=False
  return self.feature_pattern(f,'lc_carrier_stator_bolt_count','Nine open knee-stator countersinks')
 def stator(self):return self.seats(super().stator())
