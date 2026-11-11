"""Generate standalone, annotated SVG concept sheets without CAD dependencies."""

import math
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent
INK, MUTED, TEAL, ORANGE = '#183038', '#60737a', '#087e8b', '#d46b32'
BG, PANEL, LINE = '#f3f2ec', '#fffefa', '#d6dfdd'


class Sheet:
    def __init__(self, number, title, subtitle, height=1100):
        self.height = height
        self.parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="{height}" viewBox="0 0 1600 {height}" role="img" aria-labelledby="title desc">
<title id="title">Tinfox: {escape(title)}</title><desc id="desc">{escape(subtitle)} Preliminary concept drawing; no parts are qualified for manufacture.</desc>
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto-start-reverse"><path d="M 0 0 L 8 4 L 0 8 z" fill="{MUTED}"/></marker></defs>
<style>text{{font-family:Arial,Helvetica,sans-serif;fill:{INK}}}.small{{font-size:16px;fill:{MUTED}}}.label{{font-size:19px}}.caption{{font-size:17px;fill:{MUTED}}}.title{{font-size:40px;font-weight:700}}.section{{font-size:23px;font-weight:700}}.dim{{font-size:16px;fill:{TEAL}}}</style>''']
        self.rect(0, 0, 1600, height, BG, radius=0)
        self.text(44, 44, 'ODDSTRIDE / TINFOX', 'small')
        self.text(44, 95, f'{number}  {title}', 'title')
        self.text(44, 126, subtitle, 'caption')
        self.text(44, height-18, 'CONCEPT REVIEW • 170 mm links • All RS-02 • Dimensions in mm • Not manufacturing drawings', 'small')

    def raw(self, s): self.parts.append(s)

    def rect(self, x, y, w, h, fill=PANEL, stroke='none', radius=16):
        self.raw(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>')

    def line(self, x1, y1, x2, y2, color=INK, width=2, dash=None, arrows=False):
        extra = f' stroke-dasharray="{dash}"' if dash else ''
        if arrows: extra += ' marker-start="url(#arrow)" marker-end="url(#arrow)"'
        self.raw(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{width}" stroke-linecap="round"{extra}/>')

    def circle(self, x, y, r, fill, stroke='none', width=2):
        self.raw(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')

    def text(self, x, y, content, cls='label', anchor='start', fill=None):
        style = f' style="fill:{fill}"' if fill else ''
        self.raw(f'<text x="{x:.2f}" y="{y:.2f}" class="{cls}" text-anchor="{anchor}"{style}>{escape(content)}</text>')

    def lines(self, x, y, rows, cls='caption', spacing=25):
        for i, row in enumerate(rows): self.text(x, y+i*spacing, row, cls)

    def path(self, d, fill='none', stroke=INK, width=2):
        self.raw(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>')

    def joint(self, x, y, r=8):
        self.circle(x, y, r, PANEL, INK, 2)
        self.circle(x, y, 2.5, INK)

    def dim(self, x1, y1, x2, y2, label, tx=None, ty=None):
        self.line(x1, y1, x2, y2, MUTED, 1.2, arrows=True)
        self.text((x1+x2)/2 if tx is None else tx, (y1+y2)/2-10 if ty is None else ty, label, 'dim', 'middle')

    def leader(self, pts, label, x, y):
        for a, b in zip(pts, pts[1:]): self.line(*a, *b, MUTED, 1.3)
        self.circle(*pts[0], 3, MUTED)
        self.text(x, y, label, 'caption')

    def save(self, filename):
        (OUT / filename).write_text('\n'.join(self.parts) + '\n</svg>\n')


def organic_link(sheet, p, q, width=30, color='#cce4e3'):
    # Curved, tapered silhouette around a straight pivot-to-pivot load path.
    dx, dy = q[0]-p[0], q[1]-p[1]
    length = math.hypot(dx, dy)
    nx, ny = -dy/length, dx/length
    def pt(t, offset): return (p[0]+dx*t+nx*offset, p[1]+dy*t+ny*offset)
    a,b,c,d,e,f,g,h = pt(0,width*.55),pt(.2,width),pt(.7,width*.5),pt(1,width*.35),pt(1,-width*.35),pt(.7,-width*.6),pt(.2,-width*.8),pt(0,-width*.55)
    sheet.path(f'M {a[0]} {a[1]} C {b[0]} {b[1]} {c[0]} {c[1]} {d[0]} {d[1]} L {e[0]} {e[1]} C {f[0]} {f[1]} {g[0]} {g[1]} {h[0]} {h[1]} Z', color, TEAL, 2)
    sheet.line(*p, *q, TEAL, 1, '5 7')


def layout():
    s=Sheet('01', 'Body, batteries & leg proportions', 'Packaging study • curved replaceable structures • motor placements are envelopes, not mounting designs')
    s.rect(40,155,1010,590)
    s.rect(1070,155,490,885)
    s.rect(40,765,1010,275)
    s.text(65,190,'SIDE / NEAR LEGS','section')
    scale=1.3
    hip_y=290
    knee_y=hip_y+170*math.cos(math.radians(35))*scale
    floor=hip_y+340*math.cos(math.radians(35))*scale
    s.line(70,floor,1025,floor,LINE,2)
    s.text(75,floor+30,'Ground plane','small')
    # Chassis outline: approximately 500 mm long; no wall thickness specified.
    s.path('M 180 290 C 165 235 190 208 240 202 C 385 180 670 185 790 210 C 827 218 842 246 830 290 L 815 338 Q 795 355 760 355 L 245 355 Q 198 350 180 290 Z', '#dce6e5', INK, 2.5)
    # Removable cassettes are recessed above the hip axis.
    for x in [310,520]:
        s.rect(x,251,195,130,'#f4d9c5',ORANGE,10)
        s.rect(x+35,239,120,15,'#e1b795',ORANGE,4)
        s.text(x+97.5,296,'BATTERY','label','middle')
        s.text(x+97.5,322,'150 × 100 envelope','small','middle')
        s.text(x+97.5,346,'adapter not detailed','small','middle')
    s.line(302,381,723,381,INK,5)
    s.rect(375,210,275,26,'#b8caca',INK,5)
    s.text(512,229,'COMPUTER / POWER / MCU','small','middle')
    s.rect(455,163,110,37,'#94b0b3',INK,9)
    s.text(510,151,'LiDAR envelope','small','middle')
    for hip_x in [245,765]:
        hip=(hip_x,hip_y)
        knee=(hip_x+170*math.sin(math.radians(35))*scale,knee_y)
        foot=(hip_x,floor)
        organic_link(s,hip,knee,27)
        organic_link(s,knee,foot,20,'#edf3ed')
        # Two near-hip motor outlines overlap in side projection; axial stack unresolved.
        s.circle(hip_x,hip_y,43,'#f0f4f0',TEAL,3)
        s.circle(hip_x-27,hip_y-20,37,'#d5e5e4',TEAL,2)
        s.circle(hip_x-27,hip_y-20,15,PANEL,TEAL,2)
        s.joint(*hip)
        s.joint(*knee,13)
        s.path(f'M {foot[0]-16} {foot[1]-15} Q {foot[0]} {foot[1]-26} {foot[0]+16} {foot[1]-15} L {foot[0]+19} {foot[1]} L {foot[0]-19} {foot[1]} Z',INK,INK)
        s.circle(*foot,2,ORANGE)
    s.leader([(221,260),(110,235),(80,235)],'Hip + knee motors',75,220)
    s.text(75,260,'near the body','caption')
    s.leader([(347,440),(435,440),(435,420)],'170 mm thigh',445,425)
    s.leader([(324,545),(430,545)],'170 mm to foot contact',440,550)
    s.dim(985,381,985,floor,'209 mm',966,(381+floor)/2)
    s.text(980,684,'8.2 in belly clearance','small','end')
    s.dim(245,710,765,710,'400 mm hip spacing • provisional')
    s.lines(1095,195,['DESIGN INTENT'],'section')
    s.lines(1095,235,['All 12 actuators remain RS-02.','Knee motors move with the upper thigh,','close to the hip to reduce swing inertia.'])
    s.line(1095,310,1530,310,LINE)
    s.text(1095,349,'Recess the battery cassette','section')
    s.lines(1095,385,['Two packs sit fore–aft beneath the body.','The illustrated pack envelope is a placeholder.','It does not establish fit for DeWalt or M18.','A 70 mm hip-to-skid drop requires the','packs to extend upward into the chassis.'])
    s.line(1095,521,1530,521,LINE)
    s.text(1095,558,'Keep recovery contact off sensors','section')
    s.lines(1095,594,['Rounded side covers and upper guards','need to carry rollover contact loads.','The LiDAR shown here is not yet protected.','Self-righting clearance is unverified.'])
    s.line(1095,706,1530,706,LINE)
    s.text(1095,744,'Shape follows the mechanism','section')
    s.lines(1095,780,['Broad, rounded hips taper into slim shins.','Covers can conceal the rod while opening','for bearing and fastener access.','Printed curves are a styling study; wall','thickness and strength are not specified.'])
    s.rect(1095,935,435,72,'#fff0d6')
    s.lines(1110,964,['REVIEW: proportions, battery position,','leg curvature and motor concentration.'],'small',23)
    # Plan view, at 1 px/mm, matching 400 mm hip spacing and 500 mm body length.
    s.text(65,800,'TOP VIEW / WIDTH IS A DESIGN VARIABLE','section')
    s.rect(260,835,500,160,'#dce6e5',INK,35)
    for x in [310,710]:
        for y in [840,980]:
            s.rect(x-37,y-25,74,50,'#bfd4d6',TEAL,13)
            s.circle(x,y,12,PANEL,TEAL)
    for x in [360,530]: s.rect(x,875,150,80,'none',ORANGE,8)
    s.text(510,926,'Battery footprints below','small','middle')
    s.dim(820,835,820,995,'160 mm',875,922)
    s.text(870,947,'chassis width','small','middle')
    s.text(870,971,'provisional','small','middle')
    s.text(80,1030,'Hip modules extend beyond the chassis. Overall width and bearing stacks remain unresolved.','small')
    s.save('01-body-layout.svg')


def linkage_range():
    values=[]
    for i in range(3601):
        a=2*math.pi*i/3600
        bx,by=15*math.cos(a),170+15*math.sin(a)
        d=math.hypot(bx,by)
        values.append(math.atan2(by,bx)-math.acos((d*d+30*30-170*170)/(2*d*30)))
    return math.degrees(max(values)-min(values))


def knee():
    s=Sheet('02','How the rigid knee linkage works','Mechanism explanation • equal cranks show motion transfer • the torque-multiplying geometry is not selected')
    s.rect(40,155,930,885)
    s.rect(990,155,570,885)
    s.text(65,193,'SIDE VIEW / THIGH HELD STILL FOR EXPLANATION','section')
    A=(310,310); D=(310,650)
    phi=math.radians(-20)
    B=(A[0]+50*math.cos(phi),A[1]+50*math.sin(phi))
    C=(D[0]+50*math.cos(phi),D[1]+50*math.sin(phi))
    foot=(D[0]+340*math.cos(phi+math.pi/2),D[1]+340*math.sin(phi+math.pi/2))
    organic_link(s,A,D,34)
    organic_link(s,D,foot,27,'#e9eee5')
    s.circle(*A,65,'#d6e8e7',TEAL,3)
    s.circle(*A,39,PANEL,TEAL,2)
    s.line(*A,*B,ORANGE,11)
    s.line(*B,*C,ORANGE,8)
    s.line(*D,*C,TEAL,12)
    for point,name,dx,dy in [(A,'A',-22,-20),(B,'B',16,-10),(C,'C',18,0),(D,'D',-26,4)]:
        s.joint(*point,8)
        s.text(point[0]+dx,point[1]+dy,name,'section')
    s.circle(*foot,16,INK)
    s.dim(185,310,185,650,'170 mm',133,485)
    s.text(130,510,'illustrative A–D','small','middle')
    s.leader([(310,246),(450,246),(450,230)],'A: knee motor output axis',470,235)
    s.lines(470,264,['Motor housing fixed to the upper thigh.','The hip-pitch motor moves this whole assembly.'],'small')
    s.leader([(334,301),(435,345)],'A–B: short motor crank',470,351)
    s.text(470,378,'25 mm radius in this explanation','small')
    s.leader([(B[0],460),(440,460)],'B–C: rigid push–pull rod',470,466)
    s.lines(470,496,['Rod pivots at both ends.','It transfers tension and compression.','Shown outside the cover for visibility.'],'small')
    s.leader([(333,642),(440,615)],'D–C: lever rigidly attached to shin',470,621)
    s.text(470,650,'25 mm radius; rotates about knee pivot D','small')
    s.leader([(310,667),(185,710)],'D: supported knee axle',80,737)
    s.leader([(388,865),(510,865)],'Shin and knee lever turn together',530,870)
    s.text(65,1008,'The thigh is the fourth link: A → B → C → D → A. Hip axis placement is not resolved here.','small')
    s.text(1015,197,'What happens when the motor turns','section')
    s.lines(1015,237,['1. The motor rotates crank A–B.','2. The crank pushes or pulls rod B–C.','3. The rod turns lever D–C and the shin.','4. Bearings at D carry the knee support loads.'],'label',32)
    s.line(1015,371,1535,371,LINE)
    s.text(1015,408,'This drawing transfers motion 1:1','section')
    s.lines(1015,446,['Equal cranks and equal long links form a','parallelogram. Away from aligned positions,','input and output turn through equal angles.','This explains the mechanism; it does not','supply the 2:1 torque gain used in screening.'])
    s.rect(1015,590,520,178,'#fff0d6')
    s.text(1033,625,'A longer knee lever restricts travel','section')
    s.lines(1033,661,['Example: 15 mm crank, 30 mm knee lever,','170 mm rod and 170 mm pivot separation.',f'Calculated output sweep: only {linkage_range():.1f}°.', 'That example is not selected for Tinfox.'],'caption',26)
    s.text(1015,811,'Parts and details to engineer','section')
    s.lines(1015,850,['Metal rod with pinned or rod-end joints.','Knee axle supported on both sides.','Crank connection sized for rod forces.','Stops before linkage alignment or collision.','Actual travel and torque ratio across every pose.'],'caption',29)
    s.save('02-knee-linkage.svg')


def clearances():
    s=Sheet('03','Clearance with 170 mm links','Level body • 70 mm hip-to-skid assumption • belly clearance and stair height are different measurements',height=1200)
    scale=1.1; floor=660
    for x,angle,name in [(40,45,'Deep crouch'),(555,35,'Moderate crouch'),(1070,20,'Raised stance')]:
        s.rect(x,155,490,575)
        hip_height=340*math.cos(math.radians(angle))
        belly=hip_height-70
        hx=x+170; hy=floor-hip_height*scale
        knee=(hx+170*math.sin(math.radians(angle))*scale,hy+170*math.cos(math.radians(angle))*scale)
        foot=(hx,floor)
        s.text(x+25,198,name,'section')
        s.text(x+25,228,f'{angle}° link inclination from vertical','caption')
        target=floor-304.8*scale
        s.line(x+20,target,x+470,target,ORANGE,1.5,'6 7')
        s.text(x+464,target-9,'12 in reference','small','end',ORANGE)
        s.rect(hx-87,hy-49,195,98,'#dce6e5',INK,18)
        s.rect(hx-63,hy+5,150,70*scale-5,'#f4d9c5',ORANGE,8)
        s.line(hx-71,hy+70*scale,hx+95,hy+70*scale,INK,4)
        organic_link(s,(hx,hy),knee,23)
        organic_link(s,knee,foot,17,'#e9eee5')
        s.circle(hx,hy,29,'#c6dfde',TEAL,2)
        s.joint(hx,hy)
        s.joint(*knee,9)
        s.circle(*foot,9,INK)
        s.line(x+20,floor,x+470,floor,LINE,2)
        s.dim(x+415,hy+70*scale,x+415,floor,f'{belly:.0f} mm',x+413,(hy+70*scale+floor)/2)
        s.text(x+245,703,f'{belly/25.4:.1f} in beneath skid plate','section','middle')
    s.rect(40,750,1520,395)
    s.text(65,792,'THE HOUSEHOLD STAIR CASE STILL NEEDS A MOTION STUDY','section')
    sx,base,ss=400,1090,1.1
    rise,run=197*ss,254*ss
    s.path(f'M 85 {base} H {sx} V {base-rise} H {sx+run} V {base-rise-25}', 'none',INK,4)
    s.path(f'M {sx-15} {base-rise+8} H {sx+25}', 'none',ORANGE,6)
    s.dim(350,base-rise,350,base,'197 mm',289,base-rise/2)
    s.dim(sx,base-rise-24,sx+run,base-rise-24,'254 mm tread')
    s.text(88,1122,'Reference staircase; no climbing pose has been validated.','small')
    s.lines(770,850,['249 mm raised belly clearance does not mean a','249 mm obstacle can be stepped over.','The foot must clear the nose, land on the tread,','and support the body without link or battery contact.'],'label',30)
    s.lines(770,1005,['Straight-leg geometric limit: 270 mm / 10.6 in beneath skid.','A deeper battery enclosure reduces all values equally.','Knee linkage travel and self-righting remain unverified.'],'caption',30)
    s.save('03-clearance-and-stairs.svg')


if __name__ == '__main__':
    layout()
    knee()
    clearances()
    print('Generated three standalone SVG concept sheets.')
