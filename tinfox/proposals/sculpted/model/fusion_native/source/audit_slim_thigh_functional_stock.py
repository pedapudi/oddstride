"""Compare the source construction immediately before connector openings."""
import inspect,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
import cadquery as cq
import slim_limb as sl
from audit_part import audit
from audit_sections import audit as sections
code=inspect.getsource(sl.master.__wrapped__);code=code.replace('@cache\n','').replace('def master(','def functional_source(');boundary=code.index('    for sign in [-1,1]:');code=code[:boundary]+'    return s.clean()\n';namespace=dict(vars(sl));exec(compile(code,'source_functional_thigh.py','exec'),namespace);shape=namespace['functional_source'](False,3.5)
path=ROOT/'snapshots/latest-leg/thigh-stages/slim-thigh-functional-stock.step';cq.exporters.export(shape,str(path));ref={'id':'slim-thigh-functional-stock','source_step':str(path),'absolute_mesh_deflection_mm':.005,'volume_method':'gauss_kronrod_spans','volume_method_reason':'Converged span-aware volume for nonuniform cubic structural surfaces.','functional_clearance_cylinders':[[13.5,0,0,-170,0,1,0]],'functional_clearance_proof':'audits/slim-thigh-cavity-analytic-arc-proof.json'}
audit('slim-thigh-functional-stock','slim-thigh-functional-stock',ref);sections('slim-thigh-functional-stock','slim-thigh-functional-stock',ref)
