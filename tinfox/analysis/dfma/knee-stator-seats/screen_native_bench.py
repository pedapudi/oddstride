"""Independent broad static screen of an inventoried native assembly export."""
from pathlib import Path
import argparse,collections,concurrent.futures,hashlib,json,multiprocessing,os,re,time
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
H=Path(__file__).resolve().parent
SHAPES=[]
def bounds(s):
 b=s.BoundingBox();return[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def volume(s):
 p=GProp_GProps();BRepGProp.VolumePropertiesGK_s(s.wrapped,p,1e-9,True,True);return p.Mass()
def pair_check(pair):
 i,j=pair;start=time.monotonic()
 try:
  status=H/f'screen-worker-{os.getpid()}.json';status.write_text(json.dumps(dict(pair=[i,j],phase='boolean',started=time.time())))
  result=SHAPES[i]._bool_op((SHAPES[i],),(SHAPES[j],),BRepAlgoAPI_Common(),parallel=False);solids=result.Solids()
  valid=result.isValid();status.write_text(json.dumps(dict(pair=[i,j],phase='volume',started=time.time())))
  if not valid:return dict(indices=[i,j],error='Invalid exact Boolean result',result_valid=False,elapsed_seconds=time.monotonic()-start)
  volumes=[volume(s) for s in solids];v=sum(volumes)
  return dict(indices=[i,j],overlap_mm3=v,positive=v>1e-6,result_valid=result.isValid(),intersection_solids=len(solids),individual_signed_solid_volumes_mm3=volumes,intersection_bounds_mm=bounds(result) if result.Vertices() else None,elapsed_seconds=time.monotonic()-start)
 except Exception as e:return dict(indices=[i,j],error=repr(e),elapsed_seconds=time.monotonic()-start)
def init_worker(step,indices):
 global SHAPES
 leaves=list(walk(cq.Assembly.load(step)));SHAPES=[leaves[i][1] for i in indices]
def walk(node,loc=None,path=''):
 loc=(loc or cq.Location())*node.loc;path=path+'/'+node.name
 for shape in node.shapes:
  for solid in shape.Solids():yield path,solid.moved(loc)
 for child in node.children:yield from walk(child,loc,path)
def main():
 global SHAPES
 parser=argparse.ArgumentParser();parser.add_argument('--step',required=True);parser.add_argument('--inventory',required=True);parser.add_argument('--workers',type=int,default=4);args=parser.parse_args()
 step=Path(args.step).resolve();invpath=Path(args.inventory).resolve();raw=step.read_bytes();invraw=invpath.read_bytes();digest=hashlib.sha256(raw).hexdigest()
 folder=H/'static-bench-input'/digest;folder.mkdir(parents=True,exist_ok=True)
 frozen=folder/'assembly.step';frozen.write_bytes(raw);(folder/'inventory.json').write_bytes(invraw)
 inventory=json.loads(invraw);rows=inventory['inventory'];assert len(rows)==121
 assy=cq.Assembly.load(str(frozen));leaves=list(walk(assy));assert len(leaves)==121,len(leaves)
 candidates=[]
 for label,shape in leaves:
  candidates.append(dict(step_label=label,shape=shape,bounds_mm=bounds(shape),volume_mm3=volume(shape)))
 bindings=[];used=set()
 for row in rows:
  opts=[]
  for index,c in enumerate(candidates):
   if index in used:continue
   error=max(abs(x-y) for x,y in zip(row['bounds_mm'],c['bounds_mm']))
   ve=abs(row['native_very_high_volume_mm3']-c['volume_mm3'])/max(abs(c['volume_mm3']),1)
   if error<.01 and ve<.0001:opts.append((index,error,ve))
  assert len(opts)==1,(row['name'],opts)
  index,be,ve=opts[0];used.add(index);c=candidates[index]
  norm=lambda s:re.sub('[^a-z0-9]','',s.lower())
  matches={key:norm(row.get(key,'')) in norm(c['step_label']) for key in ('name','body_name','part_number') if row.get(key)}
  component=re.sub(r':\d+$','',row['path'].split('+')[-1]);matches['occurrence_component_name']=norm(component) in norm(c['step_label'])
  bindings.append(dict(inventory=row,step_label=c['step_label'],semantic_label_matches=matches,step_bounds_mm=c['bounds_mm'],step_gk_volume_mm3=c['volume_mm3'],bounds_error_max_mm=be,native_property_relative_volume_error=ve,source_solid_index=index));SHAPES.append(c['shape'])
 (folder/'bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
 pairs=[];pruned=0
 for i,a in enumerate(SHAPES):
  aa=bounds(a)
  for j in range(i+1,len(SHAPES)):
   bb=bounds(SHAPES[j])
   if any(min(aa[k+3],bb[k+3])-max(aa[k],bb[k])<=1e-8 for k in range(3)):pruned+=1
   else:pairs.append((i,j))
 print(json.dumps(dict(stage='bound',step_sha256=digest,total_parts=121,total_pairs=7260,aabb_pruned=pruned,exact_candidates=len(pairs))),flush=True)
 start=time.monotonic();checks=[]
 journal=H/'native-bench-static-checks.partial.jsonl';journal.write_text('')
 with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn'),initializer=init_worker,initargs=(str(frozen),[b['source_solid_index']for b in bindings])) as pool:
  futures=[pool.submit(pair_check,pair)for pair in pairs]
  for future in concurrent.futures.as_completed(futures):
   result=future.result()
   result['pair']=[bindings[i]['inventory']['name'] for i in result['indices']];checks.append(result)
   with journal.open('a')as f:f.write(json.dumps(result)+'\n')
   if result.get('positive') or result.get('error'):print(json.dumps(result),flush=True)
   elif len(checks)%50==0:print(json.dumps(dict(stage='checking',completed=len(checks),total=len(pairs))),flush=True)
 positives=[r for r in checks if r.get('positive')];errors=[r for r in checks if 'error'in r]
 report=dict(passed=False,status='quantitative_static_screen_complete_pending_explicit_pair_classification',step=dict(path=str(step),frozen_path=str(frozen),sha256=digest),inventory=dict(path=str(invpath),sha256=hashlib.sha256(invraw).hexdigest()),identity_binding=bindings,binding_method='Unique placed bounds within0.01mm and VeryHigh/nativeSTEP volume within0.01%; STEP assembly labels retained independently. No solid-order assumption.',solid_count=121,category_counts=dict(collections.Counter(r['category'] for r in rows)),motor_count=sum(r['name'] in ('Roll motor','Hip pitch motor','Knee pitch motor') for r in rows),connector_count=sum(bool(re.fullmatch(r'FL_(hip|knee|roll)_port_(-1|1)_(socket|plug|boot|cable)',r['name'])) for r in rows),total_pairs=7260,aabb_pruned_pairs=pruned,exact_pair_count=len(pairs),positive_volume_threshold_mm3=1e-6,checks=checks,positive_pairs=positives,errors=errors,elapsed_seconds=time.monotonic()-start,limitations=['Nominal rigid static assembly only. No manufacturing tolerance, loaded deflection, powered motion or print-strength qualification.','Positive-volume pairs remain explicitly unclassified until reviewed individually; no category or same-group pair was excluded.','Native physical-property volume is used only for identity binding. Intersection volumes use independent span-aware Gauss-Kronrod integration.'])
 out=H/'native-bench-static-screen.json';out.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(report=str(out),positive_count=len(positives),errors=len(errors),elapsed_seconds=report['elapsed_seconds'])),flush=True)
if __name__=='__main__':main()
