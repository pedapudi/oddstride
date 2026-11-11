"""Weld coincident STL vertices, including sub-micron tessellation slivers."""
import trimesh

def clean_mesh(mesh):
    mesh.merge_vertices(digits_vertex=4)
    mesh.update_faces(mesh.nondegenerate_faces());mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices()
    if not mesh.is_watertight:
        before=mesh.volume
        mesh.merge_vertices(digits_vertex=3)
        mesh.update_faces(mesh.nondegenerate_faces());mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices()
        if not mesh.is_watertight or abs(mesh.volume-before)/max(abs(before),1)>1e-5:
            raise ValueError('Mesh has defects beyond 0.001 mm tessellation welding')
    return mesh
