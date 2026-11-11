"""Prevent migration-reference builders from republishing canonical native parts."""
import json
from pathlib import Path


def require_generated_authority(root=None):
    root = Path(root) if root else Path(__file__).resolve().parent
    authority = root / 'fusion_native/manifests/source-authority.json'
    if authority.exists() and json.loads(authority.read_text()).get('full_robot_native_source_of_truth'):
        raise RuntimeError(
            'The low-profile robot is canonical in Fusion. Export the verified '
            'saved native model; this generated-CAD builder is retained only '
            'as a migration reference.')
    manifest = root / 'fusion_native/manifests/motor-complex-native-exports.json'
    if manifest.exists() and json.loads(manifest.read_text()).get('native_source_of_truth'):
        raise RuntimeError(
            'The motor complex is canonical in Fusion. Export the verified saved '
            'native parts and prepare their meshes; this generated-CAD builder '
            'is retained only as a migration reference.')
