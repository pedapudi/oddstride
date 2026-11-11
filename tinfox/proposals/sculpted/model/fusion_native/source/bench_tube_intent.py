"""Native cut-tube and knee-axle families driven by the mating clamp datums."""
class BenchTubeIntent:
 def __init__(self,g):self.g=g;self.c=g.component
 def parameters(self):
  for name,value in {'bt_pod_od':5,'bt_pod_id':3.4,'bt_pod_short_length':6,'bt_clamp_od':8,'bt_clamp_id':4.3,'bt_knee_axle_od':12,'bt_knee_axle_id':5.5}.items():self.g.parameter(name,value,comment='Modeled stock dimensions from the frozen prototype; purchasing and cut-length tolerances remain separately qualified.')
  for name,value in {'bt_pod_start_y':'sm_hub_pad_y+sm_hub_tie_pad_thickness','bt_pod_long_length':'sm_stator_base_y-bt_pod_start_y','bt_pod_short_y':'sm_stator_pad_y+sm_stator_pad_thickness','bt_knee_axle_length':'st_knee_washer_outer_floor_y-st_knee_washer_inner_floor_y'}.items():self.g.parameter(name,value)
 def tube(self,x,y,z,length,od,id,name):
  self.parameters();g=self.g;c=self.c;plane=g.plane(c.xZConstructionPlane,y,name+' cut datum');sk=c.sketches.add(plane);sk.name=name+' annular stock';center=g.skeleton_point(sk,x,'-('+z+')');g.point_dimensions(sk,center,x,'-('+z+')')
  for diameter in [od,id]:
   circle=sk.sketchCurves.sketchCircles.addByCenterRadius(center.geometry,g.mm(diameter)/20);sk.geometricConstraints.addCoincident(circle.centerSketchPoint,center);sk.sketchDimensions.addRadialDimension(circle,core.Point3D.create(center.geometry.x+.4,center.geometry.y+.4,0)).parameter.expression='('+diameter+')/2'
  profile=next(p for p in sk.profiles if p.profileLoops.count==2);inp=c.features.extrudeFeatures.createInput(profile,fusion.FeatureOperations.NewBodyFeatureOperation);inp.setDistanceExtent(False,g.value(length));f=c.features.extrudeFeatures.add(inp);f.name=name;sk.isVisible=False;body=f.bodies.item(0);body.name=name;return body
 def build(self,key):
  if key=='knee_axle':return [self.tube('0 mm','st_knee_washer_inner_floor_y','-lc_thigh_length','bt_knee_axle_length','bt_knee_axle_od','bt_knee_axle_id','Removable M5-retained knee axle')]
  if key.startswith('sleeve_'):
   where='rear'if key.endswith('0')else'front';return [self.tube('st_'+where+'_clamp_x','st_clamp_sleeve_start_y','st_'+where+'_clamp_z','st_clamp_sleeve_length','bt_clamp_od','bt_clamp_id','Eighteen millimeter clamp compression sleeve')]
  angle=int(key.rsplit('_',1)[-1]);x=f'sm_tie_radius*cos({angle} deg)';z=f'sm_tie_radius*sin({angle} deg)';return [self.tube(x,'bt_pod_start_y',z,'bt_pod_long_length','bt_pod_od','bt_pod_id','Long motor tie compression tube'),self.tube(x,'bt_pod_short_y',z,'bt_pod_short_length','bt_pod_od','bt_pod_id','Short motor tie compression tube')]
