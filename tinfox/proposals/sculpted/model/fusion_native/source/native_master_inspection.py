"""Verify assembled native occurrences against frozen robot coordinates."""
def inspect_native_master(root,EXPECTED,CUSTOM_KEYS,REFERENCE_NAMES,FRAMES):
 actual={};unexpected=[]
 def matrix(values):
  m=core.Matrix3D.create();assert m.setWithArray([v*(.1 if j==3 and i<3 else 1) for i,row in enumerate(values) for j,v in enumerate(row)]);return m
 def visit(occ,leg=None,group=None):
  c=occ.component;attr=c.attributes.itemByName('Tinfox','KinematicFrame')
  if attr:leg,group=attr.value.split(':' if ':' in attr.value else '_',1)
  key=c.partNumber;name=None;kind=None
  if key in CUSTOM_KEYS and c.bRepBodies.count:
   source=occ.attributes.itemByName('Tinfox','SourceInstance');name=source.value if source else next((p['name'] for p in EXPECTED.values() if p['mesh']==key and p['leg']==leg and (p['group']==group or leg is None)),None);kind='custom'
  elif c.partNumber in REFERENCE_NAMES:name=c.partNumber;kind='reference'
  elif c.name in REFERENCE_NAMES:name=c.name;kind='reference'
  if name:
   assert name in EXPECTED and name not in actual,(name,occ.fullPathName);row=EXPECTED[name];expected=matrix(FRAMES[row['leg']][row['group']]) if row['leg'] else core.Matrix3D.create();error=max(abs(a-b) for a,b in zip(expected.asArray(),occ.transform2.asArray()));assert error<1e-7,(name,error,occ.fullPathName);vertex_error=None
   if c.bRepBodies.count:
    body=c.bRepBodies.item(0);point=body.vertices.item(0).geometry.copy();point.transformBy(expected);vertex=body.createForAssemblyContext(occ).vertices.item(0).geometry;vertex_error=point.distanceTo(vertex)*10;assert vertex_error<1e-6,(name,vertex_error)
   actual[name]={'part_key':row['mesh'],'kind':kind,'path':occ.fullPathName,'matrix_error_cm':error,'vertex_error_mm':vertex_error,'component_bodies':c.bRepBodies.count};return
  if c.bRepBodies.count:unexpected.append({'part':key,'name':c.name,'path':occ.fullPathName,'bodies':c.bRepBodies.count})
  for child in occ.childOccurrences:visit(child,leg,group)
 for o in root.occurrences:visit(o)
 assert set(actual)==set(EXPECTED),{'missing':sorted(set(EXPECTED)-set(actual)),'extra':sorted(set(actual)-set(EXPECTED))};assert not unexpected,unexpected;assert sum(r['kind']=='custom' for r in actual.values())==100
 return {'instances':actual,'source_items':len(actual),'custom_instances':sum(r['kind']=='custom' for r in actual.values()),'reference_items':sum(r['kind']=='reference' for r in actual.values()),'passed':True}
