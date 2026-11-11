"""Editable SVG exterior studies. Styling geometry is not production CAD."""

import math
from html import escape
from pathlib import Path
from studio_vector import studio_robot

OUT=Path(__file__).resolve().parent


class Drawing:
    def __init__(self, title, subtitle, height=1200):
        self.parts=[f'''<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="{height}" viewBox="0 0 1800 {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(subtitle)} Exterior concept only; motor packaging, transmission and structural performance are unverified.</desc>
<defs>
 <linearGradient id="shell" x1="0" y1="0" x2="0.4" y2="1"><stop stop-color="#faf9f4"/><stop offset=".45" stop-color="#e3e2da"/><stop offset="1" stop-color="#bcbeb7"/></linearGradient>
 <linearGradient id="silver" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#f4f3ed"/><stop offset=".5" stop-color="#cecfca"/><stop offset="1" stop-color="#aaaea9"/></linearGradient>
 <linearGradient id="dark" x1="0" y1="0" x2="1" y2=".3"><stop stop-color="#131917"/><stop offset=".35" stop-color="#434b46"/><stop offset=".65" stop-color="#303832"/><stop offset="1" stop-color="#141a17"/></linearGradient>
 <linearGradient id="inset" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#080e0c"/><stop offset=".5" stop-color="#26382f"/><stop offset="1" stop-color="#101916"/></linearGradient>
 <radialGradient id="glass"><stop stop-color="#3d6059"/><stop offset=".35" stop-color="#172922"/><stop offset=".65" stop-color="#070c0a"/><stop offset="1" stop-color="#202824"/></radialGradient>
 <filter id="shadow" x="-.5" y="-2" width="2" height="5"><feGaussianBlur stdDeviation="10"/></filter>
</defs>
<style>text{{font-family:Arial,Helvetica,sans-serif;fill:#242b26}}.mono{{font-family:'Liberation Mono',monospace;letter-spacing:.7px}}.muted{{fill:#777e75}}.tiny{{font-size:15px}}.small{{font-size:19px}}.medium{{font-size:26px}}.large{{font-size:50px;font-weight:400}}</style>
<rect width="1800" height="{height}" fill="#edede6"/>''']
        self.rect(55,52,14,14,'#fc5c18',radius=1)
        self.text(85,65,'oddstride / industrial design',16,'mono')
        self.text(55,145,title,62)
        self.text(58,183,subtitle,20,'muted')
        self.line(55,height-63,1745,height-63,'#bdc3b8',1)
        self.text(55,height-30,'tinfox · design development',16,'mono')
        self.text(1745,height-30,'170 mm links / all RS-02 / concept, not validated CAD',15,'mono',anchor='end')

    def raw(self,s): self.parts.append(s)
    def group(self,t): self.raw(f'<g transform="{t}">')
    def end(self): self.raw('</g>')
    def path(self,d,fill='none',stroke='none',width=1): self.raw(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')
    def line(self,x1,y1,x2,y2,color='#444d45',width=1): self.raw(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>')
    def rect(self,x,y,w,h,fill,stroke='none',radius=4,width=1): self.raw(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
    def circle(self,x,y,r,fill,stroke='none',width=1): self.raw(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
    def text(self,x,y,t,size=20,cls='',anchor='start',fill=None): self.raw(f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}" text-anchor="{anchor}"'+(f' style="fill:{fill}"' if fill else '')+f'>{escape(t)}</text>')
    def lines(self,x,y,rows,size=20,spacing=30,cls='muted'):
        for i,t in enumerate(rows):self.text(x,y+i*spacing,t,size,cls)
    def screw(self,x,y,r=2):
        self.circle(x,y,r,'#a4aaa0','#687269',.5)
        self.line(x-r*.5,y,x+r*.5,y,'#3f4941',.55)
    def save(self,name): (OUT/name).write_text('\n'.join(self.parts)+'\n</svg>\n')


def tapered(d,p,q,upper=True):
    dx,dy=q[0]-p[0],q[1]-p[1];length=math.hypot(dx,dy);nx,ny=-dy/length,dx/length
    def at(t,w):return f'{p[0]+dx*t+nx*w:.3f} {p[1]+dy*t+ny*w:.3f}'
    if upper:
        outline=f'M {at(0,23)} C {at(.16,31)} {at(.64,17)} {at(1,9)} Q {at(1.07,0)} {at(1,-9)} C {at(.72,-13)} {at(.28,-29)} {at(0,-25)} Z'
        d.path(outline,'url(#shell)','#9da69c',.8)
        d.path(f'M {at(.23,23)} C {at(.40,19)} {at(.71,13)} {at(.91,7)}','none','#ffffff',1)
        d.path(f'M {at(.29,-22)} C {at(.56,-14)} {at(.83,-9)} {at(.95,-5)}','none','#8e988c',.55)
        for t,w in [(.36,-16),(.83,-7)]:
            x,y=map(float,at(t,w).split());d.screw(x,y,1.5)
    else:
        outline=f'M {at(0,9)} C {at(.27,14)} {at(.70,10)} {at(1,7)} L {at(1,-7)} C {at(.65,-5)} {at(.20,-6)} {at(0,-9)} Z'
        d.path(outline,'url(#dark)','#172019',.8)
        d.path(f'M {at(.12,7)} C {at(.4,9)} {at(.75,6)} {at(.93,4)}','none','#737f72',1.4)
        d.path(f'M {at(.15,-1)} C {at(.45,2)} {at(.78,0)} {at(.90,-1)}','none','#101811',1.4)


def motor(d,x,y,label):
    d.circle(x,y,44,'#252e27','#141e16',.8)
    d.circle(x,y,40,'url(#silver)','#91998f',.6)
    d.circle(x,y,35.4,'none','#a4ada1',.5)
    # A restrained datum line and service index replace decorative accent rings.
    d.line(x-25,y+12,x+24,y-12,'#889382',.65)
    d.circle(x,y,8,'url(#silver)','#8c9788',.7)
    d.line(x+24,y-28,x+29,y-34,'#fa5b18',2.8)
    for a in [110,230,350]:
        r=math.radians(a);d.screw(x+31*math.cos(r),y+31*math.sin(r),1.3)
    d.text(x-21,y-12,label,5,'mono')
    d.text(x+8,y+22,'RS02',3.6,'mono')


def robot_side(d,tx,ty,scale=1.8):
    d.group(f'translate({tx} {ty}) scale({scale})')
    h=340*math.cos(math.radians(35)); dx=170*math.sin(math.radians(35))
    d.raw(f'<ellipse cx="190" cy="{h+8}" rx="258" ry="7" fill="#707969" opacity=".24" filter="url(#shadow)"/>')
    # Dark understructure and a recessed fore-aft battery cassette.
    d.path('M -52 -34 Q -59 -60 -26 -63 L 420 -63 Q 465 -63 470 -28 L 468 29 Q 459 53 431 56 L -21 56 Q -50 51 -52 24 Z','url(#dark)','#182219',1)
    d.path('M 65 38 L 340 38 Q 353 40 350 54 L 339 70 L 84 70 Q 70 66 65 54 Z','#252e26','#151e17',.8)
    d.path('M 81 61 L 334 61','none','#515d4f',.6)
    d.rect(88,48,18,5,'#ff5e18',radius=1)
    d.text(118,53,'battery / release',4,'mono',fill='#b7bfb1')
    for x in [78,343]:d.screw(x,48,1.4)
    # A flat, radiused enclosure with a shallow waist: printed, removable clamshells.
    d.path('M -52 -31 Q -53 -59 -25 -65 C 74 -70 327 -69 420 -64 Q 462 -62 465 -32 L 463 13 Q 457 31 434 32 L 329 20 Q 199 7 85 20 L -23 32 Q -51 26 -52 4 Z','url(#shell)','#adb5a9',.85)
    d.path('M -28 -60 C 108 -66 315 -65 421 -59 Q 445 -58 452 -43','none','#ffffff',1.3)
    d.path('M 92 -51 L 309 -51 Q 321 -51 321 -38 L 321 12','none','#a7afa2',.6)
    d.line(90,15,310,15,'#8f9b89',.6)
    d.text(110,-17,'tinfox',19)
    d.text(111,-5,'quadruped / 170',4.5,'mono')
    d.text(292,-17,'01',12,'mono')
    d.circle(290,-4,1.5,'#fa5b18')
    for x,y in [(96,-43),(307,-43),(95,7),(307,7)]:d.screw(x,y,1.3)
    # Functional cooling apertures, visible only between the main shells and hip covers.
    for x in [51,336]:
        for j in range(5):d.rect(x+j*3,-20,1.2,17,'#313e32',radius=.6)
    # Low upper controls and optical window; optical coverage remains unresolved.
    d.rect(190,-71,57,7,'#263329',radius=2)
    d.rect(257,-73,10,8,'#ff5a13',radius=2)
    d.rect(433,-38,25,43,'#152019','#6c7767',5,.7)
    for y in [-27,-6]:
        d.circle(445,y,7,'#090f0b','#53624d',.7)
        d.circle(445,y,4.8,'url(#glass)')
        d.circle(443,y-2,1,'#8fa59c')
    for x in [0,400]:
        p=(x,0);k=(x-dx,h/2);f=(x,h)
        tapered(d,p,k,True)
        # End the structural shank inside its rubber foot, above the contact point.
        shank_end=(k[0]+.96*(f[0]-k[0]),k[1]+.96*(f[1]-k[1]))
        tapered(d,k,shank_end,False)
        d.circle(*k,10,'#263127','#0c150e',.7)
        d.circle(*k,5.7,'url(#silver)','#77836f',.5)
        d.screw(*k,2)
        d.path(f'M {x-10} {h-15} Q {x} {h-21} {x+10} {h-15} L {x+14} {h-4} Q {x+15} {h} {x+8} {h} L {x-10} {h} Q {x-16} {h-1} {x-14} {h-6} Z','#202b21','#111a12',.5)
        d.line(x-9,h-4,x+9,h-4,'#485441',.7)
        motor(d,x,0,'03' if x==0 else '01')
    d.end()


def exterior():
    d=Drawing('tinfox / 170','Studio silhouette translated into editable surfaces. Structural shell concept with concentrated hip volumes.')
    d.text(1735,65,'EXTERIOR / 03',15,'mono',anchor='end')
    studio_robot(d)
    d.text(80,1095,'THREE-QUARTER VIEW',14,'mono')
    d.text(1730,1095,'Leg construction → 07 / assembly study',15,'mono',anchor='end')
    d.save('04-refined-exterior.svg')


def details():
    d=Drawing('surface, interface, service','A precision-instrument aesthetic: restrained surfaces, legible controls and functional details.')
    for x in [55,625,1195]:d.rect(x,245,550,685,'#f8f8f1','#d5dacd',15,1)
    d.text(80,289,'01 / sensor face',19,'mono')
    # Front face and shoulder housings, deliberately sparse and symmetric.
    d.group('translate(330 500)')
    d.rect(-160,-89,320,193,'url(#dark)','#8c9981',32)
    d.rect(-153,-101,306,180,'url(#shell)','#a2ae98',32)
    for x in [-190,190]:
        d.rect(x-37,-13,74,112,'url(#dark)',radius=24)
        d.circle(x,20,43,'url(#silver)','#929e88',1)
        d.line(x-18,-8,x+13,42,'#8e9a83',1)
    d.rect(-112,-65,224,67,'#132017','#77876c',14)
    for x in [-70,70]:
        d.circle(x,-31,20,'#070e09','#5f7254',1)
        d.circle(x,-31,13,'url(#glass)')
        d.circle(x-4,-35,3,'#7a9388')
    d.line(-19,-31,19,-31,'#435c44',2)
    d.text(-105,39,'tinfox',21)
    d.text(102,39,'01',12,'mono',anchor='end')
    d.circle(99,55,3,'#fc5c18')
    d.rect(-76,80,152,26,'#233125',radius=9)
    for x in [-126,126]:d.screw(x,57,3)
    d.end()
    d.lines(80,755,['A single optical window.','Flush graphics and visible service screws.','Rounded shell over a dark structural frame.','Sensor coverage requires engineering.'],19,31)
    d.text(650,289,'02 / actuator cover',19,'mono')
    d.group('translate(900 505) scale(3.3)')
    motor(d,0,0,'01')
    d.end()
    d.lines(650,755,['Plain circular covers with a datum mark.','One short orange index; no glowing rings.','Tiny identifiers support assembly and service.','This is a cover, not an extra knee actuator.'],19,31)
    d.text(1220,289,'03 / access & controls',19,'mono')
    d.rect(1240,370,460,250,'url(#silver)','#a2af97',22)
    d.rect(1270,402,126,71,'#15261a','#7b8f70',8)
    d.text(1282,429,'ready',20,'mono',fill='#e0e8d5')
    d.text(1282,455,'01   ·   idle',12,'mono',fill='#a6b99a')
    d.rect(1605,408,42,42,'#ff5c17','#d04813',9)
    d.circle(1626,429,9,'none','#6d2910',1)
    d.line(1626,416,1626,429,'#6d2910',2)
    d.text(1605,478,'power',12,'mono')
    d.line(1259,512,1682,512,'#8e9e83',1)
    d.rect(1290,541,276,46,'#293a2c',radius=7)
    d.rect(1302,551,67,26,'#ff5c17',radius=3)
    d.text(1312,570,'pull →',12,'mono',fill='#50220e')
    d.text(1394,570,'battery',13,'mono',fill='#d1ddc5')
    for x in [1258,1682]:
        for y in [390,600]:d.screw(x,y,3)
    d.lines(1220,755,['Color identifies a control or release.','Small display stays flush with the top.','The battery latch is recessed beneath.','Interface graphics are illustrative.'],19,31)
    d.text(60,995,'REFERENCE TRANSLATION',16,'mono')
    d.lines(60,1032,['Restrained surfaces, legible controls and deliberate details. Compact sensing and concentrated hip volumes.',
                     'Tinfox: curved printed shells, remote knee actuation, replaceable slim legs and underside tool-battery access.'],20,32)
    d.save('05-materials-and-details.svg')


if __name__=='__main__':
    exterior()
    details()
    from leg_assembly import assembly
    assembly(Drawing)
    print('Generated exterior, details and leg assembly SVG studies.')
