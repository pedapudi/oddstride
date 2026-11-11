"""Current native pose datums, with an independent fore-aft motor-center offset."""
class CurrentLegPoseFrames(NativeLegPoseFrames):
 def add_frame(self,name,matrix):
  o=super().add_frame(name,matrix);o.component.partNumber='CURRENT_FRAME_'+self.leg+'_'+name;return o
 def constrain(self):
  datum=self.owner.occurrences.addNewComponent(core.Matrix3D.create());datum.component.name='Grounded robot datum';datum.component.partNumber='CURRENT_DATUM_'+self.leg;self.proxy(datum).isGrounded=True;datum.isLightBulbOn=False;f=self.frames;k='pose_'+self.leg+'_knee';hip='pose_'+self.leg+'_hip';roll='pose_'+self.leg+'_roll'
  self.mate('Hip mounting position',f['mount'],datum,'XY',offset_x=str(self.front)+'*lc_hip_x',offset_y=str(self.side)+'*lc_roll_y')
  self.mate('Hip roll',f['roll'],f['mount'],'YZ',str(self.side)+'*'+roll)
  self.mate('Hip pitch',f['thigh'],f['roll'],'XZ',hip,offset_x=str(self.front)+'*pr_pitch_x_offset',offset=str(self.side)+'*lc_pitch_offset')
  self.mate('Knee pitch',f['knee'],f['thigh'],'XZ',k,parent_y='lc_thigh_length')
  self.mate('Knee drive phase',f['crank'],f['thigh'],'XZ',k+'+lc_crank_phase')
  self.mate('Parallel link position',f['rod'],f['thigh'],'XZ',offset_x='lc_crank_radius*cos('+k+'+lc_crank_phase)',offset_y='lc_crank_radius*sin('+k+'+lc_crank_phase)')
