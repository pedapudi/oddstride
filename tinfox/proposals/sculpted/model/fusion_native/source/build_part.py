"""Compile one captured part into a native Fusion component and audit exports."""
import json,sys,hashlib
from pathlib import Path
from run_native import rpc
NATIVE=Path(__file__).resolve().parents[1]
LABELS={'battery_skid':'Battery skid plate','electronics_shelf':'Electronics deck','chassis_lower_brace':'Lower chassis brace','chassis_crossmember_121':'Front chassis crossmember','chassis_crossmember_-121':'Rear chassis crossmember','pushrod':'Knee pushrod','input_crank':'Knee drive crank','hip_hub':'Hip output hub','thigh_inner':'Thigh inner structural shell','thigh_outer':'Thigh outer structural shell','shin_inner':'Shin inner structural shell','shin_outer':'Shin outer structural shell','body_center_0':'Upper body shell','belly_center_0':'Lower body shell','body_nose_surround':'Head shoulder bridge','front_fascia':'Camera fascia'}
def recipe(key):
 manifest=json.loads((NATIVE/'manifests/parts.json').read_text());record=next(p for p in manifest['parts'] if p['id']==key)
 recipe_path=record.get('source_graph','snapshots/source_graph.json')
 source=json.loads((NATIVE/recipe_path).read_text());nodes={n['id']:n for n in source['nodes']};root=source['parts'][key]['root'];canonical={}
 if key=='body_center_0':
  # These original sweep tools lie wholly outside the old cover's final
  # ±125.4 mm center split. Keep the later rounded cuffs and their own cuts.
  assert nodes[127]['op']=='extrudeLinear' and nodes[127]['vecNormal']==[117.,0.,0.]
  assert nodes[152]['op']=='makeBox' and abs(nodes[152]['length']-250.8)<1e-7
  for node_id in [132,134,143,151]:nodes[node_id]={'id':node_id,'op':'compound','tools':[nodes[node_id]['target']]}
 if key=='chassis_beam_-102':
  # The entire beam lies inside the torso's constant X=-132..132 extrusion.
  # End lofts and their nose/tail fillets are outside the intersected region.
  # This preserves geometry while removing expensive, irrelevant construction.
  bounds=source['parts'][key]['bounds_mm'];assert bounds['xmin']>-132 and bounds['xmax']<132
  assert nodes[root]['op']=='intersect' and nodes[root]['tools']==[963]
  assert nodes[957]['op']=='extrudeLinear' and nodes[957]['vecNormal']==[264.,0.,0.]
  nodes[root]={**nodes[root],'tools':[957]}
 if key in ['front_fascia','body_nose_surround'] and recipe_path=='snapshots/source_graph.json':
  for node_id in [7,9]:
   edge_points=[p for e in nodes[node_id]['edges'] for p in [e['start'],e['end']]]
   x=edge_points[0][0];assert all(abs(p[0]-x)<1e-6 for p in edge_points)
   nodes[node_id]={**nodes[node_id],'fillet_end_plane':[0,x]}
 if key=='thigh_outer':
  # Trim the cavity with the complementary upper roof cutter. This avoids a
  # near-coincident intersection in Fusion while preserving the same roof.
  import copy
  for operation_id,tool_id in [(2049,2046),(2056,2053),(2098,2095)]:
   cutter=copy.deepcopy(nodes[tool_id]);assert cutter['op']=='extrudeLinear'
   for edge in cutter['outerWire']['edges']:
    for field in ['start','end']:
     if abs(edge[field][1])<1e-9:edge[field][1]=120.
    for point in edge.get('points',[]):
     if abs(point[1])<1e-9:point[1]=120.
   edges=[]
   for edge in cutter['outerWire']['edges']:
    if edge['kind']!='spline':edges.append(edge);continue
    points=edge['points'];level=points[0][1];active=[i for i,p in enumerate(points) if abs(p[1]-level)>1e-6];lo=max(0,min(active)-1);hi=min(len(points)-1,max(active)+1)
    for a,b in [(points[0],points[lo])]:
     if a!=b:edges.append({'kind':'line','start':a,'end':b})
    from sketch_curves import analytic,cross,sub,norm
    for j in range(lo,hi,2):
     k=min(j+2,hi);a,b=points[j],points[k]
     if k-j==2 and norm(cross(sub(points[j+1],a),sub(b,a)))/norm(sub(b,a))>.0001:
      edges.append(analytic({'kind':'spline','start':a,'end':b,'points':[a,points[j+1],b]}))
     else:edges.append({'kind':'line','start':a,'end':b})
    if points[hi]!=points[-1]:edges.append({'kind':'line','start':points[hi],'end':points[-1]})
   cutter['outerWire']['edges']=edges
   nodes[tool_id]=cutter;nodes[operation_id]={**nodes[operation_id],'op':'profileCut'}
 if key in ['front_fascia','body_nose_surround'] and recipe_path=='snapshots/source_graph.json':
  if key=='body_nose_surround':
   # The mirrored rear return lies at X=-232.2..-230 mm. The positive-X
   # head reconstruction discards it; the independent replay verifies this.
   assert nodes[214]['op']=='fuse' and nodes[214]['tools']==[213]
   nodes[214]={'id':214,'op':'compound','tools':[nodes[214]['target']]}
   # The fascia subtraction uses its independently verified compact recipe.
   # It must not rebuild a complete torso merely to recover four front posts.
   compact=json.loads((NATIVE/'snapshots/reconstructed/front_fascia/recipe.json').read_text())
   offset=500000
   for original in compact['nodes']:
    n=dict(original);n['id']+=offset
    if 'target' in n:n['target']+=offset
    if 'tools' in n:n['tools']=[v+offset for v in n['tools']]
    nodes[n['id']]=n
   fascia_root=source['parts']['front_fascia']['root']
   nodes[fascia_root]={'id':fascia_root,'op':'compound','tools':[compact['parts']['front_fascia']['root']+offset]}
  reachable=set()
  def source_visit(k):
   if k in reachable:return
   reachable.add(k);n=nodes[k]
   for child in ([n['target']] if 'target' in n else [])+n.get('tools',[]):source_visit(child)
  source_visit(root)
  for torso_id in [9,19,37,1418,1430,234,4112]:
   if torso_id in reachable:
    path=NATIVE/'source/torso_overrides'/f'{torso_id}.json';assert path.exists(),('Torso section capture pending',torso_id)
    override=json.loads(path.read_text())['nodes']
    for node in override:
     if key=='body_nose_surround' and node['id']==torso_id:
      # The head's final positive-X regions cannot intersect the rear loft.
      assert node['op']=='fuse' and len(node['tools'])==2
      node={**node,'tools':node['tools'][:1]}
     nodes[node['id']]=node
 def alias(k):
  if k in canonical:return canonical[k]
  n=nodes[k]
  if n['op']=='compound' and len(n['tools'])==1:k=alias(n['tools'][0])
  elif n['op']=='fuse' and not n['tools']:k=alias(n['target'])
  elif n['op']=='translate' and all(abs(v)<1e-10 for v in n['vector']):k=alias(n['target'])
  elif n['op']=='moved' and all(abs(v-(1 if i==j else 0))<1e-10 for i,row in enumerate(n['matrix']) for j,v in enumerate(row)):k=alias(n['target'])
  elif n['op']=='rotate' and abs(n['degrees'])<1e-10:k=alias(n['target'])
  canonical[n['id']]=k;return k
 keep={}
 def visit(k):
  k=alias(k)
  if k in keep:return k
  n=dict(nodes[k]);keep[k]=n
  if 'target'in n:n['target']=visit(n['target'])
  if 'tools'in n:n['tools']=[visit(t) for t in n['tools']]
  return k
 root=visit(root)
 override_path=NATIVE/'source/native_profile_overrides.json'
 if override_path.exists() and recipe_path=='snapshots/source_graph.json':
  for node_id,override in json.loads(override_path.read_text()).items():
   if int(node_id) in keep:keep[int(node_id)]['profiles']=override['profiles']
 part_override=NATIVE/'source/profile_overrides'/f'{key}.json'
 if part_override.exists():
  for node_id,override in json.loads(part_override.read_text()).items():
   if int(node_id) in keep:keep[int(node_id)]['profiles']=override['profiles']
 from patterns import simplify
 nodes=simplify(list(keep.values()),root)
 from sketch_curves import simplify_profiles
 curve_stats=simplify_profiles(nodes)
 return {'root':root,'nodes':nodes,'volume_mm3':source['parts'][key]['volume_mm3'],'profile_curve_simplifications':curve_stats}
def build(key,replace=False):
 graph=recipe(key);engine=(NATIVE/'source/fusion_builder.py').read_text();group='Shared leg designs'
 if key.startswith(('battery_','chassis_','body_','belly_','front_')):group='Body and chassis'
 if key.startswith(('electronics_','lidar_','sensor_','power_')):group='Electronics and sensors'
 script=engine+'''\n\ndef run(_context: str):
    import tempfile,os,time
    app=core.Application.get();d=fusion.Design.cast(app.activeProduct)
    assert app.activeDocument.name.startswith('Tinfox - Native Master Assembly'),'Wrong active document'
    graph=GRAPH
    group=next(o.component for o in d.rootComponent.occurrences if o.component.name==GROUP)
    existing=[o for o in group.occurrences if o.component.partNumber==KEY]
    assert REPLACE or not existing,'Part already exists'
    if REPLACE:
        for occurrence in existing:occurrence.deleteMe()
        for parameter in list(d.userParameters):
            if parameter.name.startswith(safe(KEY+'_')):parameter.deleteMe()
    start=d.timeline.count
    occ=group.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name=LABEL;c.partNumber=KEY
    phase_start=time.perf_counter();phase_times={}
    builder=Builder(d,c,KEY,graph['nodes'])
    if KEY.startswith('pod_sleeve_'):
        # The source item is a two-piece cut-tube kit, separated by the stator
        # plate. Preserve both physical pieces as separately named native bodies.
        moved=builder.nodes[graph['root']];pair=builder.nodes[moved['target']]
        assert moved['op']=='moved' and pair['op']=='fuse' and len(pair['tools'])==1
        bodies=builder.build(pair['target'])+builder.build(pair['tools'][0])
        assert len(bodies)==2
        transform=core.Matrix3D.create();values=[]
        for row in moved['matrix']:values+=row[:3]+[row[3]*MM]
        transform.setWithArray(values+[0,0,0,1])
        builder.transform(bodies,transform,'Position two-piece tube kit',False)
        for body,label in zip(bodies,['Long compression tube','Short stand-off tube']):body.name=label
    else:bodies=[builder.finish(graph['root'])]
    phase_times['native_construction']=time.perf_counter()-phase_start;phase_start=time.perf_counter()
    volume=sum(body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume for body in bodies)*1000;err=abs(volume-graph['volume_mm3'])/graph['volume_mm3']
    phase_times['physical_properties']=time.perf_counter()-phase_start;phase_start=time.perf_counter()
    # This is only a gross authoring check against the source recipe's low
    # accuracy mass properties. The exported STEP must separately pass the
    # stricter 0.1% adaptive-volume and 0.05 mm surface migration gates.
    assert err<.01,('Gross native/source recipe volume differs',KEY,volume,graph['volume_mm3'],err)
    d.timeline.timelineGroups.add(start,d.timeline.count-1).name=LABEL
    path=os.path.join(tempfile.gettempdir(),'tinfox-native');os.makedirs(path,exist_ok=True)
    step=os.path.join(path,KEY+'.step');stl=os.path.join(path,KEY+'.stl')
    ex=d.exportManager;assert ex.execute(ex.createSTEPExportOptions(step,c))
    phase_times['step_export']=time.perf_counter()-phase_start;phase_start=time.perf_counter()
    opts=ex.createSTLExportOptions(c,stl);opts.meshRefinement=fusion.MeshRefinementSettings.MeshRefinementHigh
    opts.unitType=fusion.DistanceUnits.MillimeterDistanceUnits
    assert ex.execute(opts)
    phase_times['stl_export']=time.perf_counter()-phase_start;phase_start=time.perf_counter()
    app.activeDocument.save('V0 native part: '+KEY+'; full migration audit remains open.')
    phase_times['cloud_save']=time.perf_counter()-phase_start
    print(json.dumps({'part':KEY,'label':LABEL,'sketches':c.sketches.count,'feature_count':c.features.count,'parameter_count':sum(1 for p in d.userParameters if p.name.startswith(safe(KEY+'_'))),'volume_mm3':volume,'source_volume_mm3':graph['volume_mm3'],'relative_volume_error':err,'body_count':c.bRepBodies.count,'phase_seconds':phase_times,'slowest_native_features':sorted(builder.timings,key=lambda item:item['seconds_since_previous_feature'],reverse=True)[:10],'paths':[step,stl]}))
'''
 for token,value in [('GRAPH',graph),('GROUP',group),('KEY',key),('LABEL',LABELS.get(key,key.replace('_',' ').capitalize())),('REPLACE',replace)]:script=script.replace(token,repr(value))
 (NATIVE/'source/last_build_script.py').write_text(script)
 messages=rpc(script,key+'-build')
 if any(isinstance(m,dict) and not m.get('success',True) for m in messages):return False
 from fetch_exports import fetch
 info=json.loads(messages[0]['message'])
 for p in info['paths']:fetch(p,Path(p).name)
 return True
if __name__=='__main__':sys.exit(0 if build(sys.argv[1],'--replace' in sys.argv) else 1)
