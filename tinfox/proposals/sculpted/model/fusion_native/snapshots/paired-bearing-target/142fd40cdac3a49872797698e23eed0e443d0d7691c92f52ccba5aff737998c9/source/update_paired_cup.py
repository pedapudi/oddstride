"""Stage the four carrier solids before publishing their review-model delta."""
import hashlib,json,shutil,tempfile
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import paired_roll as design
import build as b
from export_closed_mesh import closed_mesh
from kinematics import ROOT
OUT=ROOT/'output/paired-roll-work'
def volume(s):
    gp=GProp_GProps();BRepGProp.VolumePropertiesGK_s(s.wrapped,gp,1e-9,True,True);return gp.Mass()
raw=(OUT/'model.json').read_bytes();data=json.loads(raw);rows=[]
with tempfile.TemporaryDirectory(prefix='tinfox-cup-stage-') as folder:
    from pathlib import Path
    stage=Path(folder)
    for front in [1,-1]:
        base=design.cup(front)
        for right in [False,True]:
            key=f'motor_carrier_{front}'+('_right' if right else '')
            s=base.mirror('XZ') if right else base
            step,stl=stage/(key+'.step'),stage/(key+'.stl')
            cq.exporters.export(s,str(step));cq.exporters.export(s,str(stl),tolerance=.07,angularTolerance=.1)
            v=volume(s);mesh,check=closed_mesh(step,stl,v)
            restored=cq.importers.importStep(str(step)).val();error=abs(volume(restored)-v)
            assert restored.isValid() and len(restored.Solids())==1 and error<max(.05,v*1e-5),(key,error)
            data['meshes'][key]={'vertices':mesh.vertices.tolist(),'faces':mesh.faces.tolist()};bb=s.BoundingBox()
            for p in data['parts']:
                if p['mesh']==key:p.update(volume_mm3=v,mass_kg=v*b.DENSITY[p['material']],com_mm=list(s.Center().toTuple()),bounds_mm=[bb.xlen,bb.ylen,bb.zlen])
            rows.append(dict(part=key,mesh=check,volume_mm3=v,step_volume_error_mm3=error))
    data['source_model_sha256']=hashlib.sha256(raw).hexdigest()
    encoded=json.dumps(data,separators=(',',':')).encode();stamp=hashlib.sha256(encoded).hexdigest()
    for row in rows:
        for ext,sub in [('step','step'),('stl','stl')]:shutil.copy2(stage/(row['part']+'.'+ext),OUT/sub/(row['part']+'.'+ext))
    (OUT/'model.json').write_bytes(encoded)
    prior=json.loads((OUT/'step-roundtrip.json').read_text());prior['model_sha256']=stamp
    prior['parts']=[x for x in prior['parts'] if not x['part'].startswith('motor_carrier_')]+rows
    (OUT/'step-roundtrip.json').write_text(json.dumps(prior,indent=2))
print('MODEL',stamp,flush=True)
