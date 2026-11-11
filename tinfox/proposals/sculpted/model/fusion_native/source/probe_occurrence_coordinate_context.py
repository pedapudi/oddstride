"""Determine Fusion proxy/local transforms using direct vertex coordinates."""
import json
from pathlib import Path
from run_native import rpc
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
s=script_header()+(ROOT/'source/intent_geometry.py').read_text()+'''
def run(_context: str):
 import json
 app=core.Application.get();leg=app.activeDocument;assert leg.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';require_personal_capacity(app,leg,KNOWN,new_cloud_files=0,reserve_slots=1);scratch=app.documents.add(core.DocumentTypes.FusionDesignDocumentType);d=fusion.Design.cast(app.activeProduct);root=d.rootComponent
 def perform():
  source=root.occurrences.addNewComponent(core.Matrix3D.create());source.component.name='Native source';IntentGeometry(d,source.component).box('2 mm','2 mm','2 mm','0 mm','0 mm','0 mm','Witness');container=root.occurrences.addNewComponent(core.Matrix3D.create());container.component.name='Leg group';container.isGrounded=True;frame=container.component.occurrences.addNewComponent(core.Matrix3D.create());frame.component.name='Frame';fp=frame.createForAssemblyContext(container);result=source.moveToComponent(fp);proxy=result if result.assemblyContext else result.createForAssemblyContext(fp)
  fp.isGroundToParent=False;proxy.isGroundToParent=True;datum=container.component.occurrences.addNewComponent(core.Matrix3D.create());datum.component.name='Datum';datum.createForAssemblyContext(container).isGrounded=True;first=fusion.JointGeometry.createByPoint(frame.component.originConstructionPoint.createForAssemblyContext(frame));second=fusion.JointGeometry.createByPoint(datum.component.originConstructionPoint.createForAssemblyContext(datum));inp=container.component.joints.createInput(first,second);inp.setAsRigidJointMotion();joint=container.component.joints.add(inp);joint.offsetX.expression='185 mm';joint.offsetY.expression='68 mm';assert d.computeAll()
  def snapshot(label):
   b=proxy.component.bRepBodies.item(0);bp=b.createForAssemblyContext(proxy);return {'joint_health':int(joint.healthState),'joint_message':joint.errorOrWarningMessage,'ground_properties':{name:getattr(fp,name) for name in dir(fp) if 'ground' in name.lower() and not callable(getattr(fp,name))},'fresh_matrix':container.component.occurrences.itemByName('Frame:1').createForAssemblyContext(container).transform2.asArray(),'label':label,'path':proxy.fullPathName,'proxy_matrix':proxy.transform2.asArray(),'native_matrix':(proxy.nativeObject or proxy).transform2.asArray(),'frame_proxy_matrix':fp.transform2.asArray(),'context':proxy.assemblyContext.fullPathName if proxy.assemblyContext else None,'native_vertex':b.vertices.item(0).geometry.asArray(),'proxy_vertex':bp.vertices.item(0).geometry.asArray()}
  rows=[snapshot('After identity reparenting and native pose mate')];joint.offsetX.expression='200 mm';assert d.computeAll();rows.append(snapshot('After native mate change'));return rows
 try:record=perform()
 finally:scratch.close(False);leg.activate()
 print(json.dumps(record))
'''.replace('KNOWN',repr(known_files()))
r=rpc(s,'native-occurrence-coordinate-context',timeout=60);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/native-occurrence-coordinate-context.json').write_text(json.dumps(record,indent=2));print(record)
