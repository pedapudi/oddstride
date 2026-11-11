"""Measure actual linked geometry, poses and paired fastener interfaces."""
def shared_datum_state(app,role):
 doc=authoring_document(app,role);d=fusion.Design.cast(doc.products.itemByProductType('DesignProductType'));names={'chassis':['robot_hip_x','robot_fastener_diametral_allowance','cover_hip_x'],'leg':['lc_hip_x','lc_roll_y'],'head':['body_hip_x','saddle_fastener_diametral_clearance']}[role];parts={}
 for c in d.allComponents:
  if c.partNumber in {'chassis':['body_center_0','belly_center_0','chassis_crossmember_121'],'head':['front_fascia','body_nose_surround'],'leg':[]}[role]:
   b=c.bRepBodies.item(0);pts=[v.geometry for v in b.vertices];parts[c.partNumber]={'bounds_mm':[min(getattr(p,a) for p in pts)*10 for a in ['x','y','z']]+[max(getattr(p,a) for p in pts)*10 for a in ['x','y','z']],'features':c.features.count,'faces':b.faces.count}
 frames={}
 if role=='leg':
  for module in d.rootComponent.occurrences:
   if module.component.partNumber.startswith('ASSEMBLY_'):
    for frame in module.childOccurrences:
     attr=frame.component.attributes.itemByName('Tinfox','KinematicFrame')
     if attr:frames[attr.value]=frame.transform2.asArray()
 probe=None
 if role in ['chassis','head']:
  c=next(c for c in d.allComponents if c.partNumber==('chassis_crossmember_121' if role=='chassis' else 'body_nose_surround'));x=d.userParameters.itemByName('saddle_x').value+.225;z=4.1 if role=='chassis' else 5.2;probe=int(c.bRepBodies.item(0).pointContainment(core.Point3D.create(x,2.4,z)))
 issues=[(c.partNumber,f.name,f.errorOrWarningMessage) for c in d.allComponents for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]
 return {'role':role,'version':doc.dataFile.versionNumber,'modified':doc.isModified,'up_to_date':doc.isUpToDate,'can_advance':doc.canAdvanceToLatest,'parameters_mm':{name:d.userParameters.itemByName(name).value*10 for name in names},'derived_parameters_mm':{p.name:p.value*10 for p in d.derivedParameters},'parts':parts,'frames':frames,'fastener_probe':probe,'unhealthy':issues}
