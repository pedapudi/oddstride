"""Export an immutable saved-version native assembly and its manufacturing surfaces."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'source/export_motor_complex_native.py').read_text()
source=source.replace('from motor_complex_exports import COMPONENTS','from motor_complex_corrected_exports import COMPONENTS, RELATED')
source=source.replace('motor-complex-native','motor-complex-leg23-native')
source=source.replace("os.makedirs(folder,exist_ok=True);tick=", "assert doc.dataFile.versionNumber==23 and doc.dataFile.isComplete and not doc.isModified;assert not os.path.exists(folder);os.makedirs(folder);tick=")
needle="assembled=export3mf(bench,'assembled-motor-complex');meshes={};"
replacement="""assembled=export3mf(bench,'assembled-motor-complex');assembly_step_path=os.path.join(folder,'assembled-motor-complex.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(assembly_step_path,bench.component));assert os.path.getsize(assembly_step_path)>500000;files.append(assembly_step_path);assembly_step={'path':assembly_step_path,'sha256':hashlib.sha256(open(assembly_step_path,'rb').read()).hexdigest(),'bytes':os.path.getsize(assembly_step_path),'role':'Native assembly export for independent exact-solid checks; never a custom authoring import.'};related=[]
 for key,number in RELATED_PARTS.items():
  component=next(c for c in d.allComponents if c.partNumber==number);body=component.bRepBodies.item(0);record=export3mf(body,key);bb=body.boundingBox;record.update(part=key,component_part_number=number,native_bounds_mm=[v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]],saved_version=doc.dataFile.versionNumber,status='Part-audited native family candidate; not complete-robot authority.');related.append(record)
 meshes={};"""
source=source.replace(needle,replacement)
source=source.replace("'assembly_3mf':assembled,", "'assembly_3mf':assembled,'assembly_step':assembly_step,'related_native_parts':related,")
source=source.replace("'''.replace('PARTS',repr({k:v[0]for k,v in COMPONENTS.items()}))", "'''.replace('RELATED_PARTS',repr({k:v[0]for k,v in RELATED.items()})).replace('PARTS',repr({k:v[0]for k,v in COMPONENTS.items()}))")
exec(compile(source,str(ROOT/'source/export_motor_complex_native.py'),'exec'),{'__file__':str(ROOT/'source/export_motor_complex_native.py'),'__name__':'__main__'})
