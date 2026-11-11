"""Import a verified six-frame vendor bundle with one Fusion import operation."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];leg=sys.argv[1];assert leg in ['RL','RR'];bundle=next(x for x in json.loads((ROOT/'manifests/whole-reference-bundles.json').read_text())['bundles']if x['leg']==leg)
source=(ROOT/'source/import_current_reference_groups.py').read_text()
preamble=''' bundle=BUNDLE_SPECIFICATION;bundle_number='CURRENT_REFERENCE_BUNDLE_'+SELECTION;assert not any(c.partNumber==bundle_number for c in d.allComponents);bo=holder.component.occurrences.addNewComponent(core.Matrix3D.create());bo.component.partNumber=bundle_number;bo.component.name=SELECTION+' purchased reference bundle - construction';path=os.path.join(REMOTE,os.path.basename(bundle['path']));assert hashlib.sha256(open(path,'rb').read()).hexdigest()==bundle['sha256'];options=app.importManager.createSTEPImportOptions(path);options.isViewFit=False;assert app.importManager.importToTarget2(options,bo.component)is not None;bundle_groups={};expected_groups={g['group']for g in GROUPS}
 def discover(context):
  label=re.sub(r' \\(\\d+\\)$','',context.component.name)
  if label in expected_groups:
   assert label not in bundle_groups;bundle_groups[label]=context;return
  for child in context.component.occurrences:discover(child.createForAssemblyContext(context))
 discover(bo.createForAssemblyContext(holder));assert set(bundle_groups)==expected_groups,(list(bundle_groups),list(expected_groups))
'''
source=source.replace(' for item in GROUPS:',preamble+' for item in GROUPS:')
a=source.index("  name=item['group'];number=");b=source.index('\n  def inspect(context):',a)
source=source[:a]+"  name=item['group'];number='CURRENT_REFERENCE_'+name;assert not any(c.partNumber==number for c in d.allComponents),number;group_context=bundle_groups[name];occ=group_context.nativeObject or group_context;c=occ.component;c.partNumber=number;c.attributes.add('Tinfox','ImportTransportSTEP_SHA256',bundle['sha256']);leaves=[];found=set()"+source[b:]
source=source.replace('inspect(occ.createForAssemblyContext(holder));','inspect(group_context);')
source=source.replace("'''.replace('ROLE'", "'''.replace('BUNDLE_SPECIFICATION',"+repr(repr(bundle))+").replace('ROLE'")
source=source.replace("tag='current-reference-import-'+selection", "tag='current-reference-bundle-'+selection")
exec(compile(source,str(ROOT/'source/import_current_reference_groups.py'),'exec'),{'__file__':str(ROOT/'source/import_current_reference_groups.py'),'__name__':'__main__'})
