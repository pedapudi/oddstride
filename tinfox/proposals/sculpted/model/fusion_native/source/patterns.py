"""Recognize complete coaxial hole circles for native sketch-and-pattern features."""
import math,collections,copy

def fold_translations(nodes):
 next_id=max(nodes)+1
 def shifted_edge(edge,vector):
  edge=copy.deepcopy(edge)
  for key in ['start','end','mid','center']:
   if key in edge:edge[key]=[x+y for x,y in zip(edge[key],vector)]
  if 'points' in edge:edge['points']=[[x+y for x,y in zip(p,vector)] for p in edge['points']]
  if 'control_points' in edge:edge['control_points']=[[x+y for x,y in zip(p,vector)] for p in edge['control_points']]
  return edge
 def shifted_profile(profile,vector):
  return {**profile,'origin':[x+y for x,y in zip(profile['origin'],vector)],'edges':[shifted_edge(e,vector) for e in profile['edges']]}
 def shifted_node(key,vector,new_id):
  nonlocal next_id
  n=nodes[key];result={**n,'id':new_id,'source_translation_folded':key}
  if n['op'] in ['makeBox','makeCylinder','makeCone','makeSphere']:
   result['pnt']=[x+y for x,y in zip(n['pnt'],vector)]
  elif n['op']=='extrudeLinear':
   result['outerWire']=shifted_profile(n['outerWire'],vector);result['innerWires']=[shifted_profile(p,vector) for p in n['innerWires']]
  elif n['op']=='makeLoft':result['profiles']=[shifted_profile(p,vector) for p in n['profiles']]
  elif n['op']=='fillet':
   child_id=next_id;next_id+=1;child=shifted_node(n['target'],vector,child_id)
   if child is None:return None
   nodes[child_id]=child;result['target']=child_id;result['edges']=[shifted_edge(e,vector) for e in n['edges']]
  elif n['op']=='translate':return shifted_node(n['target'],[x+y for x,y in zip(n['vector'],vector)],new_id)
  else:return None
  return result
 for key,node in list(nodes.items()):
  if node['op']=='translate':
   replacement=shifted_node(node['target'],node['vector'],key)
   if replacement is not None:nodes[key]=replacement
 return nodes

def simplify(nodes,root):
 nodes=fold_translations({n['id']:dict(n) for n in nodes});usage=collections.Counter()
 # A hollow ruled loft through coaxial circles is exactly a revolved polygon.
 # This turns each rounded-cover cuff into one editable wall sketch and revolve.
 for key,node in list(nodes.items()):
  if node['op']!='cut' or len(node['tools'])!=1:continue
  outer=nodes[node['target']];inner=nodes[node['tools'][0]]
  if outer['op']!='makeLoft' or inner['op']!='makeLoft' or not outer['ruled'] or not inner['ruled']:continue
  profiles=outer['profiles'];holes=inner['profiles']
  if len(profiles)!=len(holes) or any(len(p['edges'])!=1 or p['edges'][0]['kind']!='circle' for p in profiles+holes):continue
  rings=[p['edges'][0] for p in profiles];bores=[p['edges'][0] for p in holes];axis=max(range(3),key=lambda i:abs(rings[0]['normal'][i]));perp=[i for i in range(3) if i!=axis]
  if any(abs(abs(r['normal'][axis])-1)>1e-7 for r in rings+bores):continue
  if any(max(abs(r['center'][i]-rings[0]['center'][i]) for i in perp)>1e-7 for r in rings+bores):continue
  if any(max(abs(a-b) for a,b in zip(r['center'],h['center']))>1e-7 or r['radius']<=h['radius'] for r,h in zip(rings,bores)):continue
  nodes[key]={'id':key,'op':'ruledAnnularRevolve','centers':[r['center'] for r in rings],'outer_radii':[r['radius'] for r in rings],'inner_radii':[r['radius'] for r in bores],'axis':axis,'source_loft_nodes':[outer['id'],inner['id']]}
 for n in nodes.values():
  usage.update(([n['target']] if 'target' in n else [])+n.get('tools',[]))
 consumed=set()
 for key,node in list(nodes.items()):
  if key in consumed or node['op']!='cut':continue
  chain=[];current=node;signature=None
  while current['op']=='cut' and len(current['tools'])==1:
   tool=nodes[current['tools'][0]]
   if tool['op']!='makeCylinder' or tool['angleDegrees']!=360:break
   axis=max(range(3),key=lambda i:abs(tool['dir'][i]))
   if abs(tool['dir'][axis])<.999999:break
   sig=(round(tool['radius'],7),round(tool['height'],7),tuple(tool['dir']),round(tool['pnt'][axis],7))
   if signature is not None and sig!=signature:break
   signature=sig;chain.append((current,tool));base=current['target']
   if usage[base]!=1:break
   current=nodes[base]
  if len(chain)<3:continue
  axis=max(range(3),key=lambda i:abs(chain[0][1]['dir'][i]));uv=[i for i in range(3) if i!=axis]
  points=[[tool['pnt'][i] for i in uv] for _,tool in chain]
  center=[sum(p[i] for p in points)/len(points) for i in range(2)]
  # Restrict to built-in principal axes so no opaque arbitrary datum is needed.
  if max(abs(v) for v in center)>1e-6:continue
  radii=[math.hypot(*p) for p in points]
  if min(radii)<1e-6 or max(radii)-min(radii)>1e-6:continue
  angles=sorted(math.atan2(p[1],p[0])%(2*math.pi) for p in points)
  gaps=[(angles[(i+1)%len(angles)]-angles[i])%(2*math.pi) for i in range(len(angles))]
  if max(abs(g-2*math.pi/len(angles)) for g in gaps)>1e-6:continue
  seed=min((tool for _,tool in chain),key=lambda t:math.atan2(t['pnt'][uv[1]],t['pnt'][uv[0]])%(2*math.pi))
  nodes[key]={'id':key,'op':'circularCutPattern','target':base,'seed':seed,'quantity':len(chain),'axis':axis,'pitch_radius':sum(radii)/len(radii),'source_cut_nodes':[n['id'] for n,_ in chain]}
  consumed.update(n['id'] for n,_ in chain[1:])
 keep={}
 def visit(k):
  if k in keep:return
  n=nodes[k];keep[k]=n
  for child in ([n['target']] if 'target' in n else [])+n.get('tools',[]):visit(child)
 visit(root)
 return list(keep.values())
