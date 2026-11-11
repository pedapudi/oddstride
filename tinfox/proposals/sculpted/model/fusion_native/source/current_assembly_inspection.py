"""Inspect current physical instances through actual native occurrence contexts."""
def current_matrix_product(a,b):
 return [sum(a[i*4+k]*b[k*4+j]for k in range(4))for i in range(4)for j in range(4)]

def current_native_instances(design, expected, reference_parts, frame_matrices, legs=None):
 root=design.rootComponent;tm=fusion.TemporaryBRepManager.get();actual={};native_bodies={};frames=[]
 def transformed_bounds(component,matrix):
  m=core.Matrix3D.create();assert m.setWithArray(matrix);boxes=[];bodies=[]
  for body in component.bRepBodies:
   b=tm.copy(body);assert tm.transform(b,m);bb=b.boundingBox;boxes.append([v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]]);bodies.append(b)
  return [min(x[i]for x in boxes)for i in range(3)]+[max(x[i]for x in boxes)for i in range(3,6)],bodies
 for leg in (legs or ['FL','FR','RL','RR']):
  module=next(o for o in root.occurrences if o.component.partNumber=='CURRENT_ASSEMBLY_'+leg)
  for frame in module.component.occurrences:
   if not frame.component.partNumber.startswith('CURRENT_FRAME_'):continue
   group=frame.component.partNumber.split('_')[-1];context=frame.createForAssemblyContext(module);fm=list(context.transform2.asArray());wanted=[v*(.1 if j==3 and i<3 else 1)for i,row in enumerate(frame_matrices[leg][group])for j,v in enumerate(row)];error=max(abs(a-b)for a,b in zip(fm,wanted));assert error<1e-7,(leg,group,error,fm,wanted);frames.append({'leg':leg,'group':group,'matrix_cm':fm,'error_cm':error});inverse=context.transform2.copy();assert inverse.invert();inverse=list(inverse.asArray());found_refs=set();names=[name for name,p in reference_parts.items()if p['group']==leg+'_'+group]
   def visit(occ):
    c=occ.component
    if c.bRepBodies.count:
     relative=current_matrix_product(inverse,list(occ.transform2.asArray()));bounds,_=transformed_bounds(c,relative);attribute_owner=occ.nativeObject or occ;source=attribute_owner.attributes.itemByName('Tinfox','SourceInstance');part=attribute_owner.attributes.itemByName('Tinfox','NativePart')
     if part:
      assert source and source.value in expected;name=source.value;key=part.value;kind='native_custom';assert max(abs(a-b)for a,b in zip(relative,core.Matrix3D.create().asArray()))<1e-7,(name,relative);bounds_error=None
     else:
      candidates=sorted((max(abs(a-b)for a,b in zip(bounds,reference_parts[n]['bounds_mm'])),n)for n in names if n not in found_refs and reference_parts[n]['geometry_comparison']['valid_solid_count']==c.bRepBodies.count);assert candidates and candidates[0][0]<.05,(leg,group,occ.fullPathName,bounds,candidates[:3]);bounds_error,name=candidates[0];found_refs.add(name);key=expected[name]['mesh'];kind='reference'
     assert name not in actual,name;actual[name]={'mesh':expected[name]['mesh'],'native_key':key,'kind':kind,'leg':leg,'group':group,'component_part_number':c.partNumber,'native_path':occ.fullPathName,'local_bounds_mm':bounds,'bounds_error_mm':bounds_error,'body_count':c.bRepBodies.count,'world_matrix_cm':list(occ.transform2.asArray()),'local_matrix_cm':relative};native_bodies[name]=transformed_bounds(c,list(occ.transform2.asArray()))[1]
    for child in c.occurrences:visit(child.createForAssemblyContext(occ))
   for child in frame.component.occurrences:visit(child.createForAssemblyContext(context))
   assert found_refs==set(names),(leg,group,sorted(set(names)-found_refs))
 selected={n for n,p in expected.items()if p.get('leg')in(legs or ['FL','FR','RL','RR'])};assert set(actual)==selected,{'missing':sorted(selected-set(actual)),'extra':sorted(set(actual)-selected)}
 return {'passed':True,'instances':actual,'frames':frames,'physical_items':len(actual),'native_bodies':sum(p['body_count']for p in actual.values()),'custom_items':sum(p['kind']=='native_custom'for p in actual.values()),'reference_items':sum(p['kind']=='reference'for p in actual.values())},native_bodies
