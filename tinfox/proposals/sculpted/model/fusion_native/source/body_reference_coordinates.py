"""Keep a single placement driver for the lidar's native cover and references."""
def bind_lidar_reference_coordinates(design):
 c=next(c for c in design.allComponents if c.partNumber=='lidar_lid');rows=[]
 for name,value in [('reference_lidar_base_x',121),('reference_lidar_lid_base_z',102)]:
  if design.userParameters.itemByName(name) is None:design.userParameters.add(name,core.ValueInput.createByString(str(value)+' mm'),'mm','Frozen reference coordinates, separate from live family placement datums.')
 for parameter in c.modelParameters:
  if parameter.createdBy.name not in ['Shared sensor seat placement','Frozen lidar reference coordinates']:continue
  expression=parameter.expression
  if 'saddle_x' in expression:new='reference_lidar_base_x-82 mm'
  elif 'saddle_sensor_lid_bottom_z' in expression:new='reference_lidar_lid_base_z-74 mm'
  else:continue
  value=parameter.value;parameter.expression=new;assert abs(parameter.value-value)<1e-9;rows.append({'parameter':parameter.name,'before':expression,'after':new})
 for feature in c.features:
  if feature.name=='Shared sensor seat placement':feature.name='Frozen lidar reference coordinates'
 assert len(rows)==2,rows
 return rows
