"""Rounded shin sections retain independent knee hardware and open clamp seats."""
class RoundedShinIntent(CohesiveLimbIntent):
 def parameters(self):
  super().parameters();g=self.g
  values={'rs_wall':'lc_shell_wall','rs_center_y':'lc_shin_y_min+lc_shin_width/2','rs_outer_start_z':'-lc_knee_crown_radius+3 mm','rs_outer_end_z':'-lc_shin_profile_length','rs_inner_start_z':'-lc_knee_crown_radius-5 mm','rs_inner_end_z':'-lc_shin_profile_length+8 mm','rs_inner_top_radius':.8}
  for prefix,widths,radii in [('outer',[44,35,32,29,25],[1.2,9,11,11,10]),('inner',[40,35,32,29,26],[4,9,11,11,10])]:
   for i,(width,radius)in enumerate(zip(widths,radii)):values[f'rs_{prefix}_width_{i}']=width;values[f'rs_{prefix}_radius_{i}']=radius
  for key,value in values.items():g.parameter(key,value,comment='Five intentional shin sections. Knee seat sizes stay independent of shank length and shell wall.')
 def loft(self,inner=False,guide_weights=None):
  self.parameters();g=self.g;c=self.c;prefix='inner'if inner else'outer';fractions=[0,14/102,49/102,79/102,1]if inner else[0,22/118,57/118,87/118,1];sketches=[]
  for i,fraction in enumerate(fractions):
   z=f'rs_{prefix}_start_z+({fraction:.16g})*(rs_{prefix}_end_z-rs_{prefix}_start_z)';center=f'lc_shin_curve_amplitude*(-({z})/lc_shank_foot_center)*(1+({z})/lc_shank_foot_center)';width=f'rs_{prefix}_width_{i}'+('-2*rs_wall'if inner else'');depth='lc_shin_width'+('-2*rs_wall'if inner else'');radius='rs_inner_top_radius'if inner and i==0 else f'rs_{prefix}_radius_{i}'+('-rs_wall'if inner else'');plane=g.plane(c.xYConstructionPlane,z,f'{prefix.title()} shin station {i+1}');sketches.append(g.rounded_rectangle(plane,width,depth,radius,'rs_center_y',f'{prefix.title()} rounded section {i+1}',center))
  if guide_weights is None:return g.loft(sketches,'Five-section rounded shin '+('cavity'if inner else'envelope'))
  paths=[]
  for kind in ['side','end','corner']:
   for sx,sy in [(1,1),(-1,1),(-1,-1),(1,-1)]:
    stations=[]
    for i,t in enumerate(fractions):
     z=f'rs_{prefix}_start_z+({t:.16g})*(rs_{prefix}_end_z-rs_{prefix}_start_z)';cx=f'lc_shin_curve_amplitude*(-({z})/lc_shank_foot_center)*(1+({z})/lc_shank_foot_center)';w=f'rs_{prefix}_width_{i}'+('-2*rs_wall'if inner else'');r='rs_inner_top_radius'if inner and i==0 else f'rs_{prefix}_radius_{i}'+('-rs_wall'if inner else'');x=f'({w})/2';y='(lc_shin_width'+('-2*rs_wall'if inner else'')+')/2'
     if kind=='end':x+=f'-({r})'
     if kind=='side':y+=f'-({r})'
     if kind=='corner':x+=f'-(1-1/sqrt(2))*({r})';y+=f'-(1-1/sqrt(2))*({r})'
     stations.append([f'({cx})+({sx})*({x})',f'rs_center_y+({sy})*({y})',z])
    curves=core.ObjectCollection.create()
    for j,matrix in enumerate(guide_weights):
     coords=[[' + '.join(f'({value:.17g})*({stations[k][axis]})'for k,value in enumerate(row)if abs(value)>1e-14)for axis in range(3)]for row in matrix];curves.add(g.control_spline_3d(coords,f'{prefix.title()} shin {kind} guide {sx} {sy} span {j+1}',degree=3))
    path=c.features.createPath(curves,False);assert path;paths.append(path)
  inp=c.features.loftFeatures.createInput(fusion.FeatureOperations.NewBodyFeatureOperation);inp.isSolid=True;inp.isTangentEdgesMerged=False
  for sk in sketches:inp.loftSections.add(sk.profiles.item(0))
  for path in paths:assert inp.centerLineOrRails.addRail(path)
  feature=c.features.loftFeatures.add(inp);feature.name='Five-section rounded shin '+('cavity'if inner else'envelope')
  for sk in sketches:sk.isVisible=False
  return feature.bodies.item(0)
 def round_housing(self,outer,fit,inner_weights):
  g=self.g;c=self.c
  for key,value in {'lc_clamp_land_radius':8.6,'lc_clamp_x':2,'lc_clamp_upper_z':-30,'lc_clamp_lower_z':'-(105/136)*lc_shin_profile_length'}.items():g.parameter(key,value)
  cap=g.box('180 mm','120 mm','120 mm','0 mm','rs_center_y','rs_outer_start_z+60 mm','Complete knee crown envelope')
  sk=self.circles('lc_shin_y_min',[('lc_clamp_x','lc_clamp_upper_z','lc_clamp_land_radius'),('lc_clamp_x','lc_clamp_lower_z','lc_clamp_land_radius')],'Two flat clamp bearing lands')
  lands=list(g.extrude_all(sk,'lc_shin_width','Integral clamp lands').bodies)
  objects=core.ObjectCollection.create()
  for body in lands:objects.add(body)
  copies=list(c.features.copyPasteBodies.add(objects).bodies)
  outer=g.combine(outer,[cap]+lands,fusion.FeatureOperations.JoinFeatureOperation,'Rounded stem with complete crown and clamp lands')
  blank=self.blank(fit);body=g.combine(blank,[outer],fusion.FeatureOperations.IntersectFeatureOperation,'Round the shared cam and stem envelope')
  inner=self.loft(True,inner_weights);inner=g.combine(inner,copies,fusion.FeatureOperations.CutFeatureOperation,'Preserve flat clamp lands through the cavity')
  return g.combine(body,[inner],fusion.FeatureOperations.CutFeatureOperation,'Hollow rounded structural shin')
 def bearing_seats(self,body):
  g=self.g
  for key,value in {'lc_inner_bearing_lead':2,'lc_bearing_span':24,'lc_bearing_fit_allowance':0,'lc_shaft_channel_radius':8.2,'lc_bearing_inner_y':'lc_shin_y_min+lc_inner_bearing_lead','lc_bearing_outer_y':'lc_bearing_inner_y+lc_bearing_span','lc_bearing_seat_radius':'lc_bearing_od/2+lc_bearing_fit_allowance'}.items():g.parameter(key,value)
  rows=[('lc_shin_y_min-1 mm','lc_bearing_inner_y+lc_bearing_width-lc_shin_y_min+1 mm','lc_bearing_seat_radius','Inboard serviceable bearing seat'),('lc_bearing_outer_y','lc_shin_y_max-lc_bearing_outer_y+1 mm','lc_bearing_seat_radius','Outboard serviceable bearing seat'),('lc_shin_y_min-7 mm','lc_shin_width+14 mm','lc_shaft_channel_radius','Knee shaft and spacer clearance')]
  for y,depth,radius,name in rows:body=self.extrude_all(self.circles(y,[('0 mm','0 mm',radius)],name),depth,name,fusion.FeatureOperations.CutFeatureOperation,body)
  return body
 def open_clamp_hardware(self,body):
  g=self.g
  for key,value in {'lc_pin_head_clearance':5.3,'lc_pin_shoulder_clearance':3.05,'lc_pin_thread_clearance':2.7,'lc_pin_nut_af':8.2,'lc_clamp_sleeve_radius':4.05,'lc_clamp_bolt_radius':2.2,'lc_extraction_radius':1.3,'rs_washer_nominal_od':12,'rs_washer_access_diametral_allowance':.4,'rs_washer_access_radius':'(rs_washer_nominal_od+rs_washer_access_diametral_allowance)/2','rs_sleeve_start':'lc_shin_y_min+7 mm','rs_sleeve_length':18,'rs_sleeve_end':'rs_sleeve_start+rs_sleeve_length'}.items():g.parameter(key,value)
  def cut(y,depth,defs,name):
   nonlocal body
   body=self.extrude_all(self.circles(y,defs,name),depth,name,fusion.FeatureOperations.CutFeatureOperation,body)
  pin=lambda radius:[('lc_pin_x','lc_pin_z',radius)]
  clamps=lambda radius:[('lc_clamp_x','lc_clamp_upper_z',radius),('lc_clamp_x','lc_clamp_lower_z',radius)]
  cut('lc_shin_y_min-1 mm','10 mm',pin('lc_pin_head_clearance'),'Output shoulder screw head access')
  cut('lc_shin_y_min+9 mm','20 mm',pin('lc_pin_shoulder_clearance'),'Output shoulder journal')
  cut('lc_shin_y_max-5.1 mm','12 mm',pin('lc_pin_thread_clearance'),'M5 output tail clearance')
  body=self.extrude_all(self.hexagons('lc_shin_y_max-5 mm',[('lc_pin_x','lc_pin_z','lc_pin_nut_af')],'Open output nut access'),'12 mm','Open output nut access',fusion.FeatureOperations.CutFeatureOperation,body)
  cut('rs_sleeve_start','rs_sleeve_length',clamps('lc_clamp_sleeve_radius'),'Compression sleeve seats')
  cut('lc_shin_y_min-5 mm','lc_shin_width+8 mm',clamps('lc_clamp_bolt_radius'),'M4 clamp through clearance')
  cut('lc_shin_y_min-8 mm','rs_sleeve_start-lc_shin_y_min+8 mm',clamps('rs_washer_access_radius'),'Open inboard washer seats')
  cut('rs_sleeve_end','40 mm',clamps('rs_washer_access_radius'),'Open outboard washer and socket seats')
  cut('lc_bearing_inner_y+lc_bearing_width','lc_bearing_span-lc_bearing_width',[('lc_bearing_od/2-lc_extraction_radius','0 mm','lc_extraction_radius'),('-(lc_bearing_od/2-lc_extraction_radius)','0 mm','lc_extraction_radius')],'Bearing extraction punch paths')
  return body
