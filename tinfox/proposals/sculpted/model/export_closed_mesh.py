"""Produce a closed review mesh from a valid STEP when the default mesher fails."""
from pathlib import Path
import tempfile
import trimesh
from mesh_cleanup import clean_mesh

def closed_mesh(step_file,stl_file,expected_volume):
    try:
        mesh=clean_mesh(trimesh.load_mesh(stl_file))
        method='OpenCascade'
        warnings=[]
    except ValueError:
        import gmsh
        gmsh.initialize()
        try:
            gmsh.option.setNumber('General.Terminal',0)
            gmsh.logger.start()
            gmsh.model.occ.importShapes(str(Path(step_file).resolve()))
            gmsh.model.occ.synchronize()
            gmsh.option.setNumber('Mesh.MeshSizeMin',.4)
            gmsh.option.setNumber('Mesh.MeshSizeMax',3)
            gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',24)
            gmsh.option.setNumber('Mesh.Algorithm',6)
            gmsh.option.setNumber('Mesh.Binary',1)
            gmsh.model.mesh.generate(2)
            with tempfile.TemporaryDirectory(prefix='tinfox-mesh-') as folder:
                file=Path(folder)/'surface.stl';gmsh.write(str(file))
                mesh=clean_mesh(trimesh.load_mesh(file))
            warnings=[x for x in gmsh.logger.get() if x.startswith(('Warning','Error'))]
            gmsh.logger.stop()
        finally:gmsh.finalize()
        method='Gmsh STEP surface triangulation'
    error=abs(abs(mesh.volume)-expected_volume)/expected_volume
    assert mesh.is_watertight and mesh.is_winding_consistent and error<.002,(step_file,error)
    mesh.export(stl_file)
    return mesh,{'mesher':method,'watertight':True,'consistent_winding':True,
        'relative_volume_error':error,'mesher_warnings':warnings,
        'scope':'Closed surface mesh and bounded volume difference. Does not establish continuous surface deviation, printability or CNC access.'}
