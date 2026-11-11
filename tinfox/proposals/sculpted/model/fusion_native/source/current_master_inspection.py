"""Bind visible linked-subsystem instances to the current native source inventory."""
def inspect_current_master(design, expected, custom, leg_rows, body_rows):
 root=design.rootComponent;actual={};unexpected=[];leaf_contexts={};subsystems=[];leg_paths={row['native_path']:(name,row)for name,row in leg_rows.items()};body_paths={row['native_path']:(row['name'],row)for row in body_rows};identity=list(core.Matrix3D.create().asArray())
 auxiliary_paths={row['native_path']for row in body_rows if row['name']=='electronics_clearance'}
 def walk(occ,role,prefix,ancestor_visible=True):
  relative=occ.fullPathName[len(prefix)+1:];visible=ancestor_visible and occ.isLightBulbOn
  if not visible and not(role=='chassis'and any(relative==p or p.startswith(relative+'+')for p in auxiliary_paths)):return
  c=occ.component;name=None;record=None;kind=None
  if c.bRepBodies.count:
   if role=='leg' and relative in leg_paths:name,record=leg_paths[relative];kind=record['kind']
   elif role=='chassis' and relative in body_paths:name,record=body_paths[relative];kind='reference'
   elif c.partNumber in custom and c.partNumber in expected and not expected[c.partNumber].get('leg'):
    name=c.partNumber;record={'world_matrix_cm':identity};kind='native_custom'
   if name is None:unexpected.append({'role':role,'path':occ.fullPathName,'relative_path':relative,'part_number':c.partNumber,'bodies':c.bRepBodies.count})
   else:
    auxiliary=name=='electronics_clearance';assert name not in actual,name;wanted=record.get('world_matrix_cm',record.get('matrix_cm'));matrix=list(occ.transform2.asArray());error=max(abs(a-b)for a,b in zip(wanted,matrix));assert error<1e-7,(name,'master transform',error);native_visible=visible and all(b.isLightBulbOn for b in c.bRepBodies);assert native_visible!=auxiliary,name;v=c.bRepBodies.item(0).vertices.item(0)if c.bRepBodies.item(0).vertices.count else None;vertex_error=None
    if v:
     m=core.Matrix3D.create();assert m.setWithArray(wanted);p=v.geometry.copy();p.transformBy(m);vertex_error=p.distanceTo(v.createForAssemblyContext(occ).geometry)*10;assert vertex_error<1e-6,(name,'native point',vertex_error)
    actual[name]={'part_key':expected[name]['mesh'],'leg':expected[name].get('leg'),'group':expected[name].get('group'),'kind':kind,'native_path':occ.fullPathName,'subsystem':role,'component_part_number':c.partNumber,'body_count':c.bRepBodies.count,'world_matrix_cm':matrix,'matrix_error_cm':error,'same_vertex_error_mm':vertex_error,'auxiliary':auxiliary,'native_visible':native_visible,'service_role':'keepout'if auxiliary else None};leaf_contexts[name]=occ
  for child in c.occurrences:walk(child.createForAssemblyContext(occ),role,prefix,visible)
 for subsystem in root.occurrences:
  attr=subsystem.attributes.itemByName('Tinfox','Subsystem');assert attr and subsystem.isReferencedComponent;role=attr.value;assert max(abs(a-b)for a,b in zip(subsystem.transform2.asArray(),identity))<1e-8;subsystems.append({'role':role,'version':subsystem.documentReference.version,'path':subsystem.fullPathName});walk(subsystem,role,subsystem.fullPathName)
 assert not unexpected,unexpected;assert set(actual)==set(expected),{'missing':sorted(set(expected)-set(actual)),'extra':sorted(set(actual)-set(expected))};assert sum(r['body_count']for r in actual.values())==703
 assert sum(r['native_visible']for r in actual.values())==683 and sum(r['body_count']for r in actual.values()if r['native_visible'])==702
 return {'passed':True,'instances':actual,'subsystems':subsystems,'model_items':len(actual),'solid_bodies':703,'visible_model_items':683,'visible_solid_bodies':702,'hidden_auxiliary_envelopes':['electronics_clearance'],'native_custom_and_stock_items':sum(r['kind']=='native_custom'for r in actual.values()),'reference_items':sum(r['kind']=='reference'for r in actual.values())},leaf_contexts
