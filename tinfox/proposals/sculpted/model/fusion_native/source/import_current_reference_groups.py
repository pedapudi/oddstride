"""Import verified purchased/display references; custom geometry is explicitly excluded."""
import json,sys
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];selection=sys.argv[1];assert selection in ['FL','FR','RL','RR','Body'];m=json.loads((ROOT/'manifests/whole-purchased-reference-groups.json').read_text());transfer=json.loads((ROOT/'audits/whole-reference-transfer.json').read_text());assert m['passed'] and m['custom_import_count']==0;groups=[g for g in m['groups']if g['group'].startswith(selection+'_')];parts={p['name']:p for p in m['parts']if p['group'].startswith(selection+'_')};role='chassis'if selection=='Body'else'leg'
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time,hashlib,os,re

def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,ROLE);doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;tick=time.monotonic();holders=[o for o in root.occurrences if o.component.partNumber=='CURRENT_PURCHASED_LIBRARY'];assert len(holders)<=1
 if holders:holder=holders[0]
 else:
  holder=root.occurrences.addNewComponent(core.Matrix3D.create());holder.component.name='Current purchased and display references - construction';holder.component.partNumber='CURRENT_PURCHASED_LIBRARY'
 holder.isLightBulbOn=False;rows=[]
 current_joints=[j for o in root.occurrences if o.component.partNumber.startswith('CURRENT_ASSEMBLY_')for j in o.component.joints]if ROLE=='leg'else[]
 for item in GROUPS:
  name=item['group'];number='CURRENT_REFERENCE_'+name;assert not any(c.partNumber==number for c in d.allComponents),number;occ=holder.component.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name=name.replace('_',' ')+' purchased references';c.partNumber=number;path=os.path.join(REMOTE,os.path.basename(item['path']));assert hashlib.sha256(open(path,'rb').read()).hexdigest()==item['sha256'];options=app.importManager.createSTEPImportOptions(path);options.isViewFit=False;assert app.importManager.importToTarget2(options,c)is not None;leaves=[];found=set()
  def inspect(context):
   component=context.component
   if component.bRepBodies.count:
    boxes=[]
    for body in component.bRepBodies:
     bb=body.createForAssemblyContext(context).boundingBox;boxes.append([v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]])
    combined=[min(box[i]for box in boxes)for i in range(3)]+[max(box[i]for box in boxes)for i in range(3,6)];matches=sorted((max(abs(a-b)for a,b in zip(combined,PARTS[label]['bounds_mm'])),label)for label in item['names']if label not in found and PARTS[label]['geometry_comparison']['valid_solid_count']==component.bRepBodies.count);assert matches and matches[0][0]<.05,(name,context.fullPathName,combined,matches[:3]);error,label=matches[0];found.add(label);source=PARTS[label];reference_role='nonmanufacturing_display_reference'if label in ['body_wordmark','body_serial']else source['reference_role'];context.attributes.add('Tinfox','ReferenceName',label);context.attributes.add('Tinfox','SourceInstance',label);context.attributes.add('Tinfox','GeometryRole',reference_role);context.attributes.add('Tinfox','SourceModelSHA256',TARGET);context.attributes.add('Tinfox','KinematicFrame',name);component.attributes.add('Tinfox','GeometryRole','Purchased/display reference definition; occurrence attributes identify each physical instance.');leaves.append({'name':label,'bodies':component.bRepBodies.count,'reference_role':reference_role,'group_bounds_mm':combined,'bounds_error_mm':error,'occurrence_path':context.fullPathName,'imported_definition':component.name,'matrix_cm':list(context.transform2.asArray())})
   for child in list(component.occurrences):
    inspect(child.createForAssemblyContext(context))
    if not child.isGroundToParent:child.isGroundToParent=True
  inspect(occ.createForAssemblyContext(holder));assert found==set(item['names']),(name,found,item['names']);assert sum(x['bodies']for x in leaves)==item['solid_count'];c.attributes.add('Tinfox','GeometryRole','Purchased and explicitly nonmanufacturing display references only; no imported custom manufacturing parts.');c.attributes.add('Tinfox','SourceSTEP_SHA256',item['sha256']);c.attributes.add('Tinfox','KinematicFrame',name);occ.isGroundToParent=True;rows.append({'group':name,'component_part_number':number,'source_sha256':item['sha256'],'reference_items':len(leaves),'solid_count':sum(x['bodies']for x in leaves),'parts':leaves})
 holder.isLightBulbOn=False;print(json.dumps({'passed':True,'saved':False,'source_model_sha256':TARGET,'selection':SELECTION,'custom_imports':0,'pose_joints_suppressed_at_return':sum(j.isSuppressed for j in current_joints),'groups':rows,'reference_items':sum(x['reference_items']for x in rows),'solid_count':sum(x['solid_count']for x in rows),'elapsed_seconds':time.monotonic()-tick,'scope':'Verified vendor/equipment/display reference import in hidden construction library. Physical frame installation and global placement checks remain pending.'}))
'''.replace('ROLE',repr(role)).replace('GROUPS',repr(groups)).replace('PARTS',repr(parts)).replace('REMOTE',repr(transfer['remote_directory'])).replace('TARGET',repr(m['source_model_sha256'])).replace('SELECTION',repr(selection))
compile(s,'import_current_reference_groups.py','exec');tag='current-reference-import-'+selection;r=rpc(s,tag,timeout=900);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits'/(tag+'.json')).write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items()if k!='groups'})
