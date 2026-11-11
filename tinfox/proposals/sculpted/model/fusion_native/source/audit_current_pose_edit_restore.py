"""Exercise installed native pose dependencies and restore the saved nominal stance."""
import gzip,json,sys
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];target=json.loads((ROOT/'manifests/whole-robot-integration-target.json').read_text());model=json.loads(gzip.decompress((ROOT/target['reference_model']).read_bytes()));sys.path.insert(0,str(ROOT.parent));import kinematics as k
k.P.update(model['parameters']);poses={'asymmetric':{'FL':[7,-10,-75],'FR':[-5,38,-76],'RL':[9,42,-90],'RR':[-8,24,-48]},'fold':model['poses']['fold'],'restored':model['poses']['stand']};cases=[{'name':name,'angles':angles,'frames':{leg:{name:m.tolist()for name,m in k.frames(leg,angles[leg]).items()}for leg in k.LEGS}}for name,angles in poses.items()]
installed=json.loads((ROOT/'audits/current-native-installed-all.json').read_text());items_by_path={v['native_path']:{'name':n,'local_matrix_cm':v['local_matrix_cm'],'kind':v['kind']}for n,v in installed['instances'].items()}
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time,os

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;rows=[];tick=time.monotonic();parameters={name:d.userParameters.itemByName(name)for name in ['pose_'+leg+'_'+axis for leg in ['FL','FR','RL','RR']for axis in ['roll','hip','knee']]};before={name:p.expression for name,p in parameters.items()};modules={leg:next(o for o in root.occurrences if o.component.partNumber=='CURRENT_ASSEMBLY_'+leg)for leg in ['FL','FR','RL','RR']}
 definitions={child.component.partNumber:child.component for module in modules.values()for frame in module.component.occurrences if frame.component.partNumber.startswith('CURRENT_FRAME_')for child in frame.component.occurrences if child.component.bRepBodies.count}
 def shape_state(c):
  result=[]
  for body in c.bRepBodies:
   bb=body.boundingBox;result.append({'faces':body.faces.count,'edges':body.edges.count,'vertices':[list(v.geometry.asArray())for v in body.vertices],'bounds_cm':[*bb.minPoint.asArray(),*bb.maxPoint.asArray()]})
  return result
 assert all(o.component.joints.count==0 for o in root.occurrences if o.component.partNumber in ['ASSEMBLY_FL','ASSEMBLY_FR','ASSEMBLY_RL','ASSEMBLY_RR'])
 baseline={key:shape_state(c)for key,c in definitions.items()};assert d.userParameters.itemByName('qa_current_pose_case')is None;driver=d.userParameters.add('qa_current_pose_case',core.ValueInput.createByReal(0),'','Temporary synchronized pose validation driver; removed after restoring independent controls.')
 def progress(stage):open(os.path.join(os.path.expanduser('~'),'Library','Caches','Tinfox','current-native-pose-validation.json'),'w').write(json.dumps({'stage':stage,'elapsed_seconds':time.monotonic()-tick,'completed_cases':[row['name']for row in rows]}))
 def rigid_definition_checks():
  greatest=0
  for key,c in definitions.items():
   current=shape_state(c);assert len(current)==len(baseline[key]);assert c.meshBodies.count==0 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),key
   for a,b in zip(baseline[key],current):
    assert (a['faces'],a['edges'],len(a['vertices']))==(b['faces'],b['edges'],len(b['vertices'])),key;assert max(abs(x-y)for x,y in zip(a['bounds_cm'],b['bounds_cm']))<1e-6,(key,'bounds');error=max((min(sum((x-y)**2 for x,y in zip(v,w))for w in b['vertices'])for v in a['vertices']),default=0)**.5*10;assert error<.00001,(key,'rigid geometry',error);greatest=max(greatest,error)
  return {'native_definitions':len(definitions),'maximum_vertex_error_mm':greatest,'topology_and_bounds_unchanged':True}
 progress('controls_setup')
 try:
  for leg,nominal in CASES[-1]['angles'].items():
   for i,axis in enumerate(['roll','hip','knee']):
    n=nominal[i];a=CASES[0]['angles'][leg][i]-n;b=CASES[1]['angles'][leg][i]-n-2*a;parameters['pose_'+leg+'_'+axis].expression='('+str(n)+' deg)+('+str(a)+' deg)*qa_current_pose_case+('+str(b)+' deg)*qa_current_pose_case*(qa_current_pose_case-1)/2'
  for case_index,case in enumerate(CASES):
   progress('setting_'+case['name'])
   driver.expression=str([1,2,0][case_index])
   assert d.computeAll();checks=[]
   for leg,module in modules.items():
    assert all(j.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState and not j.isSuppressed for j in module.component.joints)
    for frame in module.component.occurrences:
     if not frame.component.partNumber.startswith('CURRENT_FRAME_'):continue
     group=frame.component.partNumber.split('_')[-1];fp=frame.createForAssemblyContext(module);actual=list(fp.transform2.asArray());expected=[v*(.1 if j==3 and i<3 else 1)for i,row in enumerate(case['frames'][leg][group])for j,v in enumerate(row)];error=max(abs(a-b)for a,b in zip(actual,expected));assert error<1e-7,(case['name'],leg,group,error);points=[]
     physical=[]
     def visit(cp):
      if cp.component.bRepBodies.count:
       item=ITEMS_BY_PATH[cp.fullPathName];local=item['local_matrix_cm'];target=[sum(actual[i*4+k]*local[k*4+j]for k in range(4))for i in range(4)for j in range(4)];assert max(abs(a-b)for a,b in zip(cp.transform2.asArray(),target))<1e-7,(case['name'],item['name'],'leaf transform');m=core.Matrix3D.create();assert m.setWithArray(target)
       for body in cp.component.bRepBodies:
        if body.vertices.count:
         v=body.vertices.item(0);p=v.geometry.copy();p.transformBy(m);q=v.createForAssemblyContext(cp).geometry;vertex_error=p.distanceTo(q)*10;assert vertex_error<1e-6,(case['name'],item['name'],vertex_error);points.append(vertex_error)
       physical.append({'name':item['name'],'kind':item['kind']})
      for nested in cp.component.occurrences:visit(nested.createForAssemblyContext(cp))
     for child in frame.component.occurrences:visit(child.createForAssemblyContext(fp))
     checks.append({'leg':leg,'group':group,'matrix_error_cm':error,'physical_item_checks':len(physical),'native_custom_items':sum(x['kind']=='native_custom'for x in physical),'purchased_items':sum(x['kind']=='reference'for x in physical),'same_vertex_checks':len(points),'maximum_vertex_error_mm':max(points,default=0)})
   rows.append({'name':case['name'],'angles':case['angles'],'checks':checks,'rigid_definition_checks':rigid_definition_checks()})
   progress('checked_'+case['name'])
 finally:
  driver.expression='0'
  for name,expression in before.items():
   if parameters[name].expression!=expression:parameters[name].expression=expression
  assert driver.isDeletable;assert driver.deleteMe()
  progress('independent_parameters_restored')
 assert d.computeAll();assert all(parameters[n].expression==e for n,e in before.items());print(json.dumps({'passed':True,'saved_version':doc.dataFile.versionNumber,'modified':doc.isModified,'source_model_sha256':TARGET,'cases':rows,'restored_parameter_expressions':before,'definition_fingerprints_cm':baseline,'elapsed_seconds':time.monotonic()-tick,'scope':'Actual native pose matrices and custom boundary vertices for four handed legs, including asymmetric roll/pitch and folded knee. Tests parameter dependency and placement, not collision-free certification of each pose.'}))
'''.replace('CASES',repr(cases)).replace('TARGET',repr(target['model_sha256'])).replace('ITEMS_BY_PATH',repr(items_by_path))
compile(s,'audit_current_pose_edit_restore.py','exec');r=rpc(s,'current-native-pose-edit-restore',timeout=1800);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-native-pose-edit-restore.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k not in ['cases','restored_parameter_expressions','definition_fingerprints_cm']})
