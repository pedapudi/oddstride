"""Collect the reproducible design, geometry and review in one archive."""
from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[1]
out=root/'model/output/tinfox-review-package.zip'
files=[]
for folder in ['model','design','analysis']:
 for path in (root/folder).rglob('*'):
  if path.is_file() and not any(x in path.parts for x in ['.cache','__pycache__']) and path!=out:
   files.append(path)
files.append(root/'README.md')
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for path in sorted(files):z.write(path,path.relative_to(root.parent))
print(f'{out}: {len(files)} files, {out.stat().st_size/1e6:.1f} MB')
