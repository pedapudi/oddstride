"""Design-intent primitives for the frozen V0 head support.

The longitudinal hull retains its original fourteen design stations, but every
transverse section uses eight lines and eight exact tangent arcs. The shoulder
clearance uses six analytic curves instead of a sampled polygon.
"""

class NoseIntent:
 def __init__(self,geometry):self.g=geometry;self.component=geometry.component
 def parameters(self):
  values={'body_envelope_width':222.4,'body_mid_roof_z':49.5,'body_mid_floor_z':-48,'body_hip_x':185,'nose_loft_start_x':132,'nose_end_x':245.4,'nose_roof_hip_rise':6,'nose_width_taper':20.4,'nose_roof_drop':10,'nose_floor_rise':4,'nose_rounding_start_x':214,'nose_top_bevel':18,'nose_top_bevel_drop':7.2,'nose_bottom_bevel':17,'nose_bottom_bevel_drop':6.2,'nose_section_radius':9,'nose_section_radius_rise':9,'nose_end_fillet':5,'nose_wall':4.2,'nose_end_start_x':241,'nose_mount_x':121,'nose_mount_half_spacing':18,'nose_mount_clearance_diameter':3.4,'shoulder_roll_y':68,'shoulder_axial_length':117,'shoulder_outboard_reach':111,'shoulder_inboard_reach':51,'shoulder_half_height':55,'shoulder_clearance':2}
  for name,value in values.items():self.g.parameter(name,value,comment='V0 head/body design dimension; vendor interfaces are independent')
  self.g.parameter('shoulder_roll_limit',61,'deg','Conservative shoulder clearance sweep in either roll direction')
 def hull(self,inset,name,station_list=None):
  g=self.g;self.parameters();stations=station_list if station_list is not None else [132,138,148,160,172,180,185,192,202,214,226,236,242];inset_value=g.mm(inset);stations=[x for x in stations if x<245.4-inset_value];profiles=[]
  for index,number in enumerate(stations+[245.4-inset_value]):
   last=index==len(stations)
   if last:x='nose_end_x - ('+inset+')'
   elif number<=185:x='nose_loft_start_x + (body_hip_x - nose_loft_start_x) * '+str((number-132)/53)
   else:x='body_hip_x + (nose_end_x - body_hip_x) * '+str((number-185)/60.4)
   if number<=185:
    f='(1-cos(180 deg * (('+x+') - nose_loft_start_x) / (body_hip_x - nose_loft_start_x)))/2'
    df='sin(180 deg * (('+x+') - nose_loft_start_x) / (body_hip_x - nose_loft_start_x)) * 3.141592653589793 / (2*(body_hip_x-nose_loft_start_x))'
    width='body_envelope_width';top='body_mid_roof_z + nose_roof_hip_rise * '+f;floor='body_mid_floor_z';dw='0';dt='nose_roof_hip_rise * '+df;db='0'
   else:
    f='(1-cos(180 deg * (('+x+') - body_hip_x) / (nose_end_x - body_hip_x)))/2'
    df='sin(180 deg * (('+x+') - body_hip_x) / (nose_end_x-body_hip_x)) * 3.141592653589793 / (2*(nose_end_x-body_hip_x))'
    width='body_envelope_width - nose_width_taper * '+f;top='body_mid_roof_z + nose_roof_hip_rise - nose_roof_drop * '+f;floor='body_mid_floor_z + nose_floor_rise * '+f;dw='-nose_width_taper * '+df;dt='-nose_roof_drop * '+df;db='nose_floor_rise * '+df
   if number<=214:cf='0';cdf='0 / 1 mm'
   else:
    cf='(1-cos(180 deg * (('+x+') - nose_rounding_start_x) / (nose_end_x - nose_rounding_start_x)))/2'
    cdf='sin(180 deg * (('+x+') - nose_rounding_start_x) / (nose_end_x-nose_rounding_start_x)) * 3.141592653589793 / (2*(nose_end_x-nose_rounding_start_x))'
   bt='nose_top_bevel - nose_top_bevel_drop * '+cf;bb='nose_bottom_bevel - nose_bottom_bevel_drop * '+cf;dbt='-nose_top_bevel_drop * '+cdf;dbb='-nose_bottom_bevel_drop * '+cdf
   side='('+width+')/2 - ('+inset+')*sqrt(1+(('+dw+')/2)^2)';roof='('+top+') - ('+inset+')*sqrt(1+('+dt+')^2)';bottom='('+floor+') + ('+inset+')*sqrt(1+('+db+')^2)'
   upper='('+width+')/2 + ('+top+') - ('+bt+') - ('+inset+')*sqrt(2+(('+dw+')/2+('+dt+')-('+dbt+'))^2)'
   lower='('+width+')/2 - ('+floor+') - ('+bb+') - ('+inset+')*sqrt(2+(('+dw+')/2-('+db+')-('+dbb+'))^2)'
   radius='nose_section_radius + nose_section_radius_rise * '+cf+' - ('+inset+')'
   prefix=name.lower().replace(' ','_')+'_'+str(index+1).zfill(2)+'_'
   expressions={'x':x,'side':side,'roof':roof,'floor':bottom,'top_bevel':'('+side+')+('+roof+')-('+upper+')','bottom_bevel':'('+side+')-('+bottom+')-('+lower+')','radius':radius}
   for role,expression in expressions.items():g.parameter(prefix+role,expression,comment='Derived hull station; edit the named envelope dimensions')
   plane=g.plane(self.component.yZConstructionPlane,prefix+'x',name+' station '+str(index+1))
   profiles.append(g.rounded_octagon(plane,*[prefix+role for role in ['side','roof','floor','top_bevel','bottom_bevel','radius']],name+' profile '+str(index+1)))

  body=g.loft(profiles,name+' envelope');return g.end_fillet(body,'nose_end_x - ('+inset+')','nose_end_fillet - ('+inset+')',name+' end round')
 def shoulder(self):
  g=self.g;c=self.component;self.parameters()
  g.parameter('shoulder_outer_corner_radius','sqrt(shoulder_outboard_reach^2 + shoulder_half_height^2)',comment='Derived corner orbit')
  g.parameter('shoulder_inner_corner_radius','sqrt(shoulder_inboard_reach^2 + shoulder_half_height^2)',comment='Derived corner orbit')
  g.parameter('shoulder_corner_angle','shoulder_roll_limit + atan(shoulder_half_height / shoulder_outboard_reach)','deg','Outer corner at maximum roll')
  g.parameter('shoulder_tangent_angle','shoulder_corner_angle + acos(shoulder_inner_corner_radius / shoulder_outer_corner_radius)','deg','Common convex-envelope tangent')
  plane=g.plane(c.yZConstructionPlane,'body_hip_x - shoulder_axial_length/2','Shoulder sweep rear datum');sk=c.sketches.add(plane);sk.name='Continuous shoulder clearance envelope'
  origin=g.skeleton_point(sk,'0 mm','shoulder_roll_y');g.point_dimensions(sk,origin,'0 mm','shoulder_roll_y')
  top=g.skeleton_point(sk,'-shoulder_outer_corner_radius*sin(shoulder_corner_angle)','shoulder_roll_y + shoulder_outer_corner_radius*cos(shoulder_corner_angle)');g.point_dimensions(sk,top,'-shoulder_outer_corner_radius*sin(shoulder_corner_angle)','shoulder_roll_y + shoulder_outer_corner_radius*cos(shoulder_corner_angle)')
  bottom=g.skeleton_point(sk,'shoulder_outer_corner_radius*sin(shoulder_corner_angle)','shoulder_roll_y + shoulder_outer_corner_radius*cos(shoulder_corner_angle)');g.point_dimensions(sk,bottom,'shoulder_outer_corner_radius*sin(shoulder_corner_angle)',None);sk.geometricConstraints.addHorizontalPoints(top,bottom)
  arc0,start0,end0=g.driven_arc(sk,origin,'shoulder_outer_corner_radius + shoulder_clearance','90 deg - shoulder_corner_angle','90 deg + shoulder_corner_angle','Outer corner sweep')
  arc1,start1,end1=g.driven_arc(sk,top,'shoulder_clearance','90 deg + shoulder_corner_angle','90 deg + shoulder_tangent_angle','Upper clearance corner')
  arc2,start2,end2=g.driven_arc(sk,origin,'shoulder_inner_corner_radius + shoulder_clearance','90 deg + shoulder_tangent_angle','450 deg - shoulder_tangent_angle','Inner corner sweep')
  arc3,start3,end3=g.driven_arc(sk,bottom,'shoulder_clearance','450 deg - shoulder_tangent_angle','450 deg - shoulder_corner_angle','Lower clearance corner')
  # Arc endpoints share the same analytic expressions; do not add redundant constraints.
  sk.sketchCurves.sketchLines.addByTwoPoints(end1,start2);sk.sketchCurves.sketchLines.addByTwoPoints(end2,start3);assert sk.profiles.count==1
  feature=g.extrude(sk,'nose_end_start_x - (body_hip_x - shoulder_axial_length/2)','Shoulder clearance sweep');return feature.bodies.item(0)
