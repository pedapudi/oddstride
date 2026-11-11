import sys,json,hashlib
from pathlib import Path
import cadquery as cq
sys.path.insert(0,'tinfox/proposals/sculpted/model');import low_sensor_saddle as s
p=Path('tinfox/proposals/sculpted/model/fusion_native');shape=s.reference('front_fascia').intersect(s.box(45,240,200,(268.5,0,0)));path=p/'snapshots/current-targets/integrated-low-face.step';cq.exporters.export(shape,str(path));print({'volume':shape.Volume(),'solids':len(shape.Solids()),'valid':shape.isValid(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
