"""Create a native handed part linked to its canonical native master body."""
import sys,json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
MIRRORS={'battery_side_panel_1':('battery_side_panel_-1','XZ'),'battery_access_latch_1':('battery_access_latch_-1','XZ'),'battery_latch_1':('battery_latch_-1','XZ'),'chassis_beam_102':('chassis_beam_-102','XZ'),'chassis_crossmember_-121':('chassis_crossmember_121','YZ'),'roll_cartridge_-1':('roll_cartridge_1','YZ')}
def source_for(key):return (key[:-6],'XZ') if key.endswith('_right') else MIRRORS.get(key)
def mirror(key,subsystem=None):
 source,plane=source_for(key)
 script='''import adsk.core as core,adsk.fusion as fusion,os,tempfile,json

def run(_context: str):
    app=core.Application.get();d=fusion.Design.cast(app.activeProduct)
    source=None;parent=None
    if SUBSYSTEM_FILE:
        doc=next(doc for doc in app.documents if doc.isSaved and doc.dataFile.id==SUBSYSTEM_FILE);doc.activate();d=fusion.Design.cast(app.activeProduct);assert not doc.dataFile.isReadOnly and not doc.isModified
        parent=d.rootComponent;source=next((o.component for o in parent.occurrences if o.component.partNumber==SOURCE),None)
    else:
        assert app.activeDocument.name.startswith('Tinfox - Native Master Assembly')
        for group in d.rootComponent.occurrences:
            for occ in group.component.occurrences:
                if occ.component.partNumber==SOURCE:source=occ.component;parent=group.component
    assert source is not None,'Canonical native part is missing'
    assert not any(o.component.partNumber==KEY for o in parent.occurrences),'Handed part already exists'
    start=d.timeline.count;occ=parent.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name=KEY.replace('_',' ');c.partNumber=KEY
    source_bodies=core.ObjectCollection.create()
    for body in source.bRepBodies:source_bodies.add(body)
    copy=c.features.copyPasteBodies.add(source_bodies);copy.name='Linked canonical part';assert copy.isParametric
    copy.timelineObject.rollTo(True)
    try:source_links=[{'part':body.parentComponent.partNumber,'assembly_path':body.assemblyContext.fullPathName if body.assemblyContext else None} for body in copy.sourceBody]
    finally:d.timeline.moveToEnd()
    assert source_links and all(link['part']==SOURCE for link in source_links),'Canonical parametric link was not preserved'
    originals=list(c.bRepBodies);objects=core.ObjectCollection.create()
    for body in originals:objects.add(body)
    inp=c.features.mirrorFeatures.createInput(objects,c.xZConstructionPlane if PLANE=='XZ' else c.yZConstructionPlane);inp.isCombine=False
    feature=c.features.mirrorFeatures.add(inp);feature.name='Handed reflection about '+PLANE
    bodies=[b for b in c.bRepBodies if b not in originals];assert len(bodies)==len(originals)
    for i,body in enumerate(bodies):body.name=KEY+(' segment '+str(i+1) if len(bodies)>1 else '')
    for original in originals:c.features.removeFeatures.add(original)
    d.timeline.timelineGroups.add(start,d.timeline.count-1).name=KEY.replace('_',' ')
    path=os.path.join(tempfile.gettempdir(),'tinfox-native');step=os.path.join(path,KEY+'.step');stl=os.path.join(path,KEY+'.stl')
    ex=d.exportManager;assert ex.execute(ex.createSTEPExportOptions(step,c))
    options=ex.createSTLExportOptions(c,stl);options.unitType=fusion.DistanceUnits.MillimeterDistanceUnits;options.meshRefinement=fusion.MeshRefinementSettings.MeshRefinementHigh;assert ex.execute(options)
    import time,adsk
    doc=app.activeDocument;version=doc.dataFile.versionNumber;assert doc.save('V0 native handed part: '+KEY+'; full migration audit remains open.')
    deadline=time.monotonic()+90
    while (doc.isModified or doc.dataFile.versionNumber<=version or not doc.dataFile.isComplete) and time.monotonic()<deadline:adsk.doEvents();time.sleep(.1)
    assert not doc.isModified and doc.dataFile.versionNumber>version and doc.dataFile.isComplete
    print(json.dumps({'part':KEY,'file_id':doc.dataFile.id,'version':doc.dataFile.versionNumber,'source':SOURCE,'plane':PLANE,'features':c.features.count,'sketches':c.sketches.count,'body_count':c.bRepBodies.count,'parametric_source_links':source_links,'volume_mm3':sum(body.physicalProperties.volume for body in bodies)*1000,'paths':[step,stl]}))
'''
 subsystem_file=json.loads((ROOT/'manifests/subsystems.json').read_text())['subsystems'][subsystem]['file_id'] if subsystem else None
 for token,value in [('SUBSYSTEM_FILE',subsystem_file),('SOURCE',source),('PLANE',plane),('KEY',key)]:script=script.replace(token,repr(value))
 result=rpc(script,key+'-mirror')
 if not result[0].get('success',True):return False
 info=json.loads(result[0]['message']);(ROOT/'audits'/f'{key}-native-mirror.json').write_text(json.dumps(info,indent=2))
 if subsystem:
  manifest=json.loads((ROOT/'manifests/subsystems.json').read_text());manifest['subsystems'][subsystem]['version']=info['version'];manifest['subsystems'][subsystem].setdefault('mirrors',{})[key]=info;(ROOT/'manifests/subsystems.json').write_text(json.dumps(manifest,indent=2))
 for path in info['paths']:fetch(path,Path(path).name)
 return True
if __name__=='__main__':sys.exit(0 if mirror(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else None) else 1)
