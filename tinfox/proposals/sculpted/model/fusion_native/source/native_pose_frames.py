"""Native dimensional pose mates for the quadruped's analytic linkage.

These are parameter-driven CAD poses, not free dynamic revolute joints. Joint
angle and signed offset parameters preserve the four-bar relationship without
sketch distance constraints switching sides at the crank's dead-center angle.
"""
class NativeLegPoseFrames:
 def __init__(self,design,leg_occurrence,leg,front,side):
  self.d=design;self.leg_occ=leg_occurrence;self.owner=leg_occurrence.component;self.leg=leg;self.front=front;self.side=side;self.frames={};self.point_cache={};self.joints=[]
  g=IntentGeometry(design,self.owner)
  for name,value in {'lc_hip_x':185,'lc_roll_y':68,'lc_pitch_offset':0}.items():g.parameter(name,value,comment='Robot family hip placement, independent of vendor bolt dimensions')
  for axis,value in [('roll',0),('hip',30),('knee',-60)]:g.parameter('pose_'+leg+'_'+axis,value,'deg',comment='Native kinematic pose control; collision-free limits are not implied')
 def proxy(self,occ):return occ if occ.assemblyContext else occ.createForAssemblyContext(self.leg_occ)
 def add_frame(self,name,matrix):
  occ=self.owner.occurrences.addNewComponent(matrix);occ.component.name={'mount':'Fixed shoulder','roll':'Hip roll carrier','thigh':'Thigh and proximal motors','knee':'Shin and foot','crank':'Knee drive crank','rod':'Parallel pushrod'}[name];occ.component.partNumber='FRAME_'+self.leg+'_'+name;occ.component.attributes.add('Tinfox','KinematicFrame',self.leg+':'+name);self.frames[name]=occ;return occ
 def point(self,occ,plane='XZ',x='0 mm',y='0 mm',name='Joint datum'):
  key=(occ.component.id,plane,x,y)
  if key in self.point_cache:return self.point_cache[key]
  c=occ.component;g=IntentGeometry(self.d,c);p={'XY':c.xYConstructionPlane,'XZ':c.xZConstructionPlane,'YZ':c.yZConstructionPlane}[plane];sk=c.sketches.add(p);sk.name=name;point=g.skeleton_point(sk,x,y);g.point_dimensions(sk,point,x,y);sk.isLightBulbOn=False;geometry=fusion.JointGeometry.createByPoint(point.createForAssemblyContext(occ));self.point_cache[key]=geometry;return geometry
 def mate(self,name,child,parent,plane,angle='0 deg',parent_x='0 mm',parent_y='0 mm',offset_x=None,offset_y=None,offset=None):
  first=self.point(child,plane,name=name+' child datum');second=self.point(parent,plane,parent_x,parent_y,name+' parent datum');inp=self.owner.joints.createInput(first,second);inp.setAsRigidJointMotion();inp.angle=core.ValueInput.createByString(angle);joint=self.owner.joints.add(inp);joint.name=self.leg+' '+name+' pose';joint.attributes.add('Tinfox','PoseDriver','Native angular/offset parameters; analytic kinematic pose, not a dynamic joint')
  for parameter,expression in [(joint.offsetX,offset_x),(joint.offsetY,offset_y),(joint.offset,offset)]:
   if expression is not None:parameter.expression=expression
  self.joints.append(joint);return joint
 def constrain(self):
  datum=self.owner.occurrences.addNewComponent(core.Matrix3D.create());datum.component.name='Grounded robot datum';datum.component.partNumber='DATUM_'+self.leg;self.proxy(datum).isGrounded=True;datum.isLightBulbOn=False;f=self.frames;k='pose_'+self.leg+'_knee';hip='pose_'+self.leg+'_hip';roll='pose_'+self.leg+'_roll'
  self.mate('Hip mounting position',f['mount'],datum,'XY',offset_x=str(self.front)+'*lc_hip_x',offset_y=str(self.side)+'*lc_roll_y')
  self.mate('Hip roll',f['roll'],f['mount'],'YZ',str(self.side)+'*'+roll)
  self.mate('Hip pitch',f['thigh'],f['roll'],'XZ',hip,offset=str(self.side)+'*lc_pitch_offset')
  self.mate('Knee pitch',f['knee'],f['thigh'],'XZ',k,parent_y='lc_thigh_length')
  self.mate('Knee drive phase',f['crank'],f['thigh'],'XZ',k+'+lc_crank_phase')
  self.mate('Parallel link position',f['rod'],f['thigh'],'XZ',offset_x='lc_crank_radius*cos('+k+'+lc_crank_phase)',offset_y='lc_crank_radius*sin('+k+'+lc_crank_phase)')
 def matrices(self):return {name:self.proxy(occ).transform2.asArray() for name,occ in self.frames.items()}
