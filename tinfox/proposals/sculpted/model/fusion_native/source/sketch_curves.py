"""Recover analytic lines and arcs from source curves converted to NURBS.

STEP preparation converted some straight lines and circular arcs to splines.
Authoring their 81 sampled points as native fitted splines wastes computation and
makes sketches harder to edit. Only curves matching analytic geometry within
0.000001 mm at every captured sample are simplified; other curves stay unchanged.
"""
import math
def sub(a,b):return [x-y for x,y in zip(a,b)]
def add(a,b):return [x+y for x,y in zip(a,b)]
def mul(a,t):return [x*t for x in a]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def analytic(edge):
 if edge['kind']!='spline' or edge.get('native_keep_spline'):return edge
 points=edge['points'];a,c=points[0],points[-1];line=sub(c,a);length=norm(line)
 tolerance=.000001
 if length>tolerance and max(norm(cross(sub(p,a),line))/length for p in points)<tolerance:
  return {**edge,'kind':'line','start':a,'end':c,'native_simplification':'Analytic line recovered from collinear source spline samples'}
 if length<=tolerance:return edge
 b=points[len(points)//2];u=sub(b,a);v=sub(c,a);n=cross(u,v);nn=dot(n,n)
 if nn<1e-18:return edge
 center=add(a,mul(add(mul(cross(v,n),dot(u,u)),mul(cross(n,u),dot(v,v))),1/(2*nn)))
 radius=norm(sub(a,center));normal=mul(n,1/math.sqrt(nn))
 error=max(max(abs(norm(sub(p,center))-radius),abs(dot(sub(p,center),normal))) for p in points)
 if error<tolerance:
  return {**edge,'kind':'arc','start':a,'mid':b,'end':c,'center':center,'radius':radius,'normal':normal,'native_simplification':'Analytic arc recovered from circular source spline samples'}
 return edge
def simplify_profiles(nodes):
 counts={'spline_to_line':0,'spline_to_arc':0,'remaining_splines':0}
 for node in nodes:
  profiles=node.get('profiles',[])+([node['outerWire']] if 'outerWire' in node else [])+node.get('innerWires',[])
  for profile in profiles:
   edges=[]
   for edge in profile['edges']:
    converted=analytic(edge);edges.append(converted)
    if edge['kind']=='spline':counts['remaining_splines' if converted['kind']=='spline' else 'spline_to_'+converted['kind']]+=1
   profile['edges']=edges
 return counts
