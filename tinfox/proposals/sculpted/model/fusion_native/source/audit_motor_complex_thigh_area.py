"""Convergence check for a trimmed source whose direct surface quadrature is unstable."""
import hashlib,json,tempfile
from pathlib import Path
import numpy as np,trimesh,gmsh,cadquery as cq
ROOT=Path(__file__).resolve().parents[1]
rows=[]
for label,path in [('source',ROOT/'snapshots/motor-complex-20261029T050757Z/thigh_outer.step')]:
 shape=cq.importers.importStep(str(path)).val();boundary=cq.Compound.makeCompound(shape.Faces());samples=[]
 for h,curvature in [(3,24),(1.5,48),(.75,96)]:
  gmsh.initialize()
  try:
   gmsh.option.setNumber('General.Terminal',0);gmsh.logger.start();gmsh.model.occ.importShapes(str(path));gmsh.model.occ.synchronize();gmsh.option.setNumber('Mesh.MeshSizeMin',h/10);gmsh.option.setNumber('Mesh.MeshSizeMax',h);gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',curvature);gmsh.option.setNumber('Mesh.Algorithm',6);gmsh.model.mesh.generate(2)
   with tempfile.TemporaryDirectory()as folder:
    target=Path(folder)/'surface.stl';gmsh.write(str(target));mesh=trimesh.load_mesh(target);mesh.merge_vertices()
   warnings=gmsh.logger.get();gmsh.logger.stop()
  finally:gmsh.finalize()
  assert mesh.is_watertight and mesh.is_winding_consistent
  ids=np.unique(np.linspace(0,len(mesh.vertices)-1,min(1000,len(mesh.vertices))).astype(int));errors=[boundary.distance(cq.Vertex.makeVertex(*mesh.vertices[i]))for i in ids]
  record={'max_size_mm':h,'curvature_resolution':curvature,'area_mm2':float(mesh.area),'triangles':len(mesh.faces),'watertight':True,'sampled_vertex_boundary_max_mm':max(errors),'warnings':[x for x in warnings if x.startswith(('Warning','Error'))]};samples.append(record);print(label,record,flush=True)
 uncertainty=4*abs(samples[-1]['area_mm2']-samples[-2]['area_mm2']);rows.append({'shape':label,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'samples':samples,'convergence_allowance_mm2':uncertainty})
native_path=ROOT/'exports/motor-complex-native-thigh_outer.step'
native_shape=cq.importers.importStep(str(native_path)).val()
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
samples=[]
for eps in [1e-7,1e-9,1e-11,1e-13]:
 props=GProp_GProps();error=BRepGProp.SurfaceProperties_s(native_shape.wrapped,props,eps,True);samples.append({'requested_error':eps,'area_mm2':props.Mass(),'estimated_relative_error':error})
uncertainty=4*abs(samples[-1]['area_mm2']-samples[-2]['area_mm2']);assert uncertainty/samples[-1]['area_mm2']<1e-8
rows.append({'shape':'native','sha256':hashlib.sha256(native_path.read_bytes()).hexdigest(),'samples':samples,'convergence_allowance_mm2':uncertainty,'method':'Converged analytic trimmed-surface quadrature; no mesh required.'})
source,native=rows;relative=(abs(source['samples'][-1]['area_mm2']-native['samples'][-1]['area_mm2'])+sum(r['convergence_allowance_mm2']for r in rows))/source['samples'][-1]['area_mm2'];report={'method':'Source: closed Gmsh surface meshes at three resolutions, every mesh watertight and sampled vertices on the exact source boundary. Native: stable analytic trimmed-surface area at four quadrature tolerances. Four-times-last-change allowances; original unstable source Gauss diagnostics preserved.','parts':rows,'relative_area_error_with_allowance':relative,'threshold':.001,'passed':relative<.001 and source['samples'][-1]['sampled_vertex_boundary_max_mm']<.01 and native['convergence_allowance_mm2']/native['samples'][-1]['area_mm2']<1e-8};(ROOT/'audits/motor-complex-thigh-area-convergence.json').write_text(json.dumps(report,indent=2));print('AREA GATE',report['passed'],relative,flush=True)
