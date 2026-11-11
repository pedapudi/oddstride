"""Record measured torso changes and generate a matched-camera review."""
import json,hashlib
import trimesh
from kinematics import ROOT,P
before=json.loads((ROOT/'body-baseline.json').read_text())
raw=(ROOT/'output/model.json').read_bytes();m=json.loads(raw)
parts=[p for p in m['parts'] if p['name'].startswith(('body_','belly_'))]
vertices=[v for p in parts for v in m['meshes'][p['mesh']]['vertices']]
lo=[min(v[i] for v in vertices) for i in range(3)];hi=[max(v[i] for v in vertices) for i in range(3)]
web=[]
for name in ['FL_thigh_inner','FL_thigh_outer']:
    part=next(p for p in m['parts'] if p['name']==name);mesh=m['meshes'][part['mesh']]
    section=trimesh.Trimesh(vertices=mesh['vertices'],faces=mesh['faces'],process=False).section(plane_origin=[0,0,-98],plane_normal=[0,0,1])
    web.extend(section.vertices[:,1])
after={'model_sha256':hashlib.sha256(raw).hexdigest(),'parameters':{k:P[k] for k in ['body_length','body_width','body_height']},'rigid_torso_bounds_mm':{'min':lo,'max':hi,'extent':[hi[i]-lo[i] for i in range(3)]},'torso_shell_mass_kg':sum(p['mass_kg'] for p in parts),'central_roof_height_mm':P['central_roof_height_mm'],'shoulder_cap_span_mm':2*(P['roll_y']+P['cap_y']),'thigh_web_depth_mm':float(max(web)-min(web)),'structural_limb_mass_kg':sum(p['mass_kg'] for p in m['parts'] if any(p['name'].endswith('_'+x) for x in ['thigh_inner','thigh_outer','shin_inner','shin_outer']))}
record={'before':before,'after':after,'scope':before['scope'],'retained_packaging':{'computer_bay_mm':P['electronics_clearance_mm'],'battery_each_mm':P['battery_envelope_mm'],'motor_count':12,'foot_center_track_mm':2*(P['roll_y']+P['shin_y'])}}
(ROOT/'output/torso-comparison.json').write_text(json.dumps(record,indent=2))
rows=[('Shoulder cap span',f"{before['shoulder_cap_span_mm']:.1f} mm",f"{after['shoulder_cap_span_mm']:.1f} mm"),('Thigh depth through central web',f"{before['thigh_web_depth_mm']:.1f} mm",f"{after['thigh_web_depth_mm']:.1f} mm"),('Body / belly shell mass',f"{before['torso_shell_mass_kg']*1000:.0f} g",f"{after['torso_shell_mass_kg']*1000:.0f} g"),('Structural limb halves, all four legs',f"{before['structural_limb_mass_kg']*1000:.0f} g",f"{after['structural_limb_mass_kg']*1000:.0f} g"),('Body length',f"{before['parameters']['body_length']} mm",f"{P['body_length']} mm")]

html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tinfox · torso refinement</title><style>
body{margin:0;background:#eeede6;color:#29312d;font:16px system-ui}main{max-width:1440px;margin:auto;padding:32px}a{color:inherit}h1{font-size:44px;letter-spacing:-2px;margin:24px 0 12px}p{max-width:860px;line-height:1.6}.images{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:30px 0}figure{margin:0;background:#deddd5;border-radius:16px;overflow:hidden}img{display:block;width:100%}figcaption{padding:16px;font-size:13px;letter-spacing:1px;text-transform:uppercase}table{width:100%;border-collapse:collapse;font-size:15px}th,td{padding:14px;border-bottom:1px solid #ccc;text-align:left}.note{font-size:13px;color:#626c65}@media(max-width:800px){.images{grid-template-columns:1fr}main{padding:18px}h1{font-size:32px}}</style><main>
<a href="./">← Open the 3D CAD</a> · <a href="parts.html">Individual CAD parts</a><h1>Softer body surfaces. Recessed shoulders. Sculpted limbs.</h1><p>The body corners soften toward the shoulders, and recessed metal caps remove the raised rings at the thigh roots. The thigh surfaces curve inward through their central webs while retaining the joint seats. The shin ends have softer corners. Both structural halves remain removable.</p>
<div class="images"><figure><img src="/body-before.png" alt="Previous body and limb CAD"><figcaption>Previous CAD</figcaption></figure><figure><img src="/studio.png" alt="Revised CAD with recessed shoulder caps, sculpted thighs and rounded body corners"><figcaption>Revised CAD</figcaption></figure></div>
<table><thead><tr><th>Measured change</th><th>Previous</th><th>Revised</th></tr></thead><tbody>'''
html+=''.join('<tr>'+''.join('<td>'+v+'</td>' for v in row)+'</tr>' for row in rows)
html+='''</tbody></table><p>Both tool-battery envelopes and the 130 × 135 × 32 mm computer bay remain in the assembly. The hip spacing, inset leg mounts, 170 mm links and rear knee pushrods are retained.</p><p class="note">Both images render the CAD meshes with the same camera and lighting. The 464 mm body length and 170 mm leg links are retained. Shoulder cap span excludes other protrusions. Flexible shoulder gaiters remain provisional. Shell stiffness, cooling and manufacturing details require physical validation.</p><p><a href="../output/tinfox-assembly.step">STEP assembly</a> · <a href="../output/torso-comparison.json">Dimensions and CAD fingerprints</a> · <a href="../output/engineering.json">Motion and torque results</a></p></main></html>'''
(ROOT/'review/body.html').write_text(html)
print('Body and limb comparison:',rows)
