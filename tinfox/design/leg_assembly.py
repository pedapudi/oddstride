"""Structural leg proposal. Illustrations do not specify production dimensions."""

from studio_vector import definitions, bolt, ellipse


def assembly(Drawing):
    d=Drawing('the leg, inside the silhouette',
              'Proposed assembly: proximal motors, rigid knee drive, structural shell halves and supported metal pivots.', 1500)
    definitions(d)
    d.text(1735,65,'CONSTRUCTION / 07',15,'mono',anchor='end')
    d.rect(55,235,800,1135,'#f7f6f0','#d2d4c8',14)
    d.rect(885,235,860,580,'#f7f6f0','#d2d4c8',14)
    d.rect(885,845,860,525,'#f7f6f0','#d2d4c8',14)
    d.text(85,280,'01 / proximal actuation + rigid linkage',22,'mono')
    d.text(85,315,'Side schematic. Outer shell removed; pose is illustrative.',18,'muted')
    d.group('translate(120 340)')
    # A split thigh box carries the proximal knee motor and both knee bearings.
    d.path('M 128 54 Q 163 24 206 43 L 359 85 Q 414 101 421 152 Q 425 193 392 224 L 141 410 Q 99 436 70 459 Q 40 480 19 450 Q 4 429 19 401 L 115 186 Q 93 120 128 54 Z', 'url(#v-side)', '#a3ab99', 1.5)
    d.path('M 134 74 L 194 62 L 351 105 Q 396 119 400 153 Q 407 177 381 203 L 122 392 L 61 433 L 39 420 L 140 188 Z', '#e4e6da', '#b3bbab', 1)
    # Raised ribs share load between metal bearing/motor carriers and the shell flange.
    for p in ['M 169 159 L 58 417','M 169 159 L 340 157','M 340 186 L 84 405','M 147 226 L 267 237','M 113 304 L 175 305']:
        d.path(p,'none','#bdc5b3',15)
        d.path(p,'none','#f6f8ed',7)
    d.path('M 29 428 L 200 726 Q 208 742 190 751 Q 172 760 160 743 L 17 456 Z', 'url(#v-shin)', '#1d281c', 2)
    d.path('M 43 468 L 176 725', 'none', '#8b9482', 2)
    d.path('M 161 733 Q 181 726 197 734 L 211 760 Q 213 770 190 774 Q 164 775 150 767 Z','url(#v-rubber)','#182315',1)
    # Opposed bearings support the hip hub. Actuator stator is attached to the roll cradle.
    d.path('M 108 75 L 128 47 L 203 42 L 233 72 L 242 155 L 211 196 L 134 191 L 105 157 Z','url(#silver)','#71816a',1.5)
    d.circle(172,119,65,'url(#v-ring)','#34412d',1)
    d.circle(172,119,53,'url(#v-disc)','#ebeee2',1)
    d.circle(172,119,22,'url(#v-bevel)','#75836a',1)
    d.circle(172,119,9,'#4b5a40')
    d.text(172,104,'HIP',12,'mono',anchor='middle')
    # Knee actuator sits on the moving thigh root, not at the knee.
    d.path('M 281 108 L 303 80 L 370 87 L 404 123 L 402 178 L 370 207 L 303 197 L 278 166 Z','url(#silver)','#71816a',1.5)
    d.circle(341,149,56,'url(#v-ring)','#34412d',1)
    d.circle(341,149,47,'url(#v-disc)','#eef0e4',1)
    d.text(341,128,'KNEE',11,'mono',anchor='middle')
    # A closed four-bar: input crank, rigid rod, knee rocker and the thigh.
    d.path('M 341 149 L 318 211','none','#323c2d',19)
    d.path('M 341 149 L 318 211','none','#adb6a3',12)
    d.path('M 318 211 L 98 389','none','#6d7962',13)
    d.path('M 318 211 L 98 389','none','#c9d0bf',7)
    d.path('M 40 430 L 98 389','none','#39472f',22)
    d.path('M 40 430 L 98 389','none','#87977a',14)
    for x,y in [(341,149),(318,211),(98,389),(40,430)]:
        d.circle(x,y,10,'url(#v-bevel)','#526448',1)
        d.circle(x,y,4,'#293b20')
    for x,y in [(133,69),(213,75),(129,168),(292,122),(378,180),(159,219),(114,308),(40,405)]:
        bolt(d,x,y,3)
    # Leaders stay outside the mechanism.
    for x,y,label,rows in [
        (172,119,'A / hip pitch',['Motor fixed to roll cradle.','Hub drives the thigh box.']),
        (341,149,'B / knee actuator',['Motor fixed to thigh root.','Moves with the upper leg.']),
        (219,291,'C / metal drive rod',['Pinned joints at both ends.','A cover encloses its sweep.']),
        (40,430,'D / supported knee',['Rocker fixed to the shin.','Axle carried on both sides.'])]:
        yy={'A / hip pitch':18,'B / knee actuator':150,'C / metal drive rod':300,'D / supported knee':450}[label]
        d.path(f'M {x+12} {y} L 452 {y} L 452 {yy+5} L 472 {yy+5}', 'none', '#94a18a',1)
        d.text(486,yy+10,label,17,'mono')
        d.lines(486,yy+37,rows,15,23)
    d.text(250,585,'170 mm',19,'mono')
    d.text(250,610,'nominal shank',15,'muted')
    d.end()
    d.text(85,1180,'The shell is part of the load path.',22)
    d.lines(85,1215,['Ribs and bolted edge flanges join the two curved halves into a box.',
                     'Metal carriers spread pivot and motor loads into both halves.',
                     'Rod clearance, knee travel and leverage require a full motion sweep.',
                     'No constant reduction ratio or payload capacity is established.'],18,30)
    # Section diagram: both skins carry load; discrete metal sleeves prevent crushing.
    d.text(915,280,'02 / structural sandwich section',22,'mono')
    d.text(915,315,'Section across the thigh. Fasteners and rod occupy separate stations.',18,'muted')
    d.group('translate(945 355)')
    d.path('M 20 30 Q 130 -14 258 30 L 258 49 Q 130 7 20 49 Z','url(#v-thigh)','#a1ad97',1.2)
    d.path('M 20 224 Q 130 268 258 224 L 258 205 Q 130 247 20 205 Z','url(#v-thigh)','#a1ad97',1.2)
    # Mating flanges close the section without a separate cosmetic cover.
    for x in [20,239]:
        d.rect(x,45,19,80,'#d9dfd0','#9faa92',1)
        d.rect(x,129,19,80,'#c5ceba','#9faa92',1)
        d.rect(x+3,117,13,18,'#afbca1','#718666',1)
    # Compression sleeves and through-bolts at rib stations.
    for x in [65,207]:
        d.rect(x-9,42,18,170,'url(#silver)','#7a8970',2)
        d.rect(x-3,25,6,207,'#6d7c62',radius=1)
        d.rect(x-14,20,28,11,'#89987c','#566a49',2)
        d.rect(x-13,223,26,12,'#89987c','#566a49',2)
        d.line(x-3,50,x-3,206,'#f5f6eb',1)
    d.path('M 39 77 L 57 77 M 74 69 L 198 69 M 216 77 L 239 77 M 39 185 L 57 185 M 74 191 L 198 191 M 216 185 L 239 185','none','#b4c1a6',8)
    # Hollow center contains the rod; dashed envelope is reserved clearance.
    d.raw('<ellipse cx="136" cy="133" rx="39" ry="38" fill="none" stroke="#d58a51" stroke-width="1.4" stroke-dasharray="5 4"/>')
    d.circle(136,133,12,'url(#silver)','#55674b',1)
    d.circle(136,133,6,'#c0cbb6')
    for x,y,yy,title,body in [(147,11,0,'Curved structural skins','Continuous ribs join each skin to its flange.'),
                             (219,127,78,'Sleeves + through-bolts','Clamp metal, limiting compression of plastic.'),
                             (175,145,156,'Rod clearance envelope','Allow for motion, deflection and tolerances.')]:
        d.path(f'M {x} {y} L 317 {y} L 317 {yy+14} L 337 {yy+14}','none','#99a88e',1)
        d.text(355,yy+20,title,19)
        d.text(355,yy+48,body,16,'muted')
    d.end()
    d.lines(915,687,['The skins are removable structural parts; both must be installed for operation.',
                    'Metal bearing carriers bridge the halves at each pivot. Captured nuts and',
                    'compression sleeves carry joint clamping loads. Shell thickness, rib spacing',
                    'and print orientation remain subject to load and fatigue tests.'],18,29)
    # Knee bearing stack with an independent shaft and fastener load path.
    d.text(915,890,'03 / pivot support + motor mounting',22,'mono')
    d.text(915,925,'Knee section: a fork supports the shin hub on both sides.',18,'muted')
    d.group('translate(965 952)')
    for x in [90,410]:
        d.rect(x,10,42,160,'url(#v-thigh)','#a1ad97',5)
        d.rect(x-9,42,60,98,'url(#silver)','#738668',4)
        d.rect(x+1,58,40,66,'#46593b','#243b1b',2)
        d.rect(x+9,69,24,44,'#bac8ae','#829475',2)
        for yy in [66,116]:d.circle(x+21,yy,5,'#e1e7d8','#7c8e6e',1)
    d.rect(45,81,460,20,'url(#silver)','#6b805f',1)
    d.rect(34,74,17,34,'#637a56','#3f5a32',2)
    d.rect(500,74,18,34,'#637a56','#3f5a32',2)
    d.rect(155,69,234,44,'#394e2e','#1c3513',3)
    d.path('M 232 68 L 232 22 L 308 22 L 308 161 L 232 161 L 232 113 Z','url(#v-shin)','#334b28',1)
    d.rect(162,68,17,46,'#aab99e','#4a673e',2)
    d.rect(365,68,17,46,'#aab99e','#4a673e',2)
    d.text(111,198,'carrier + bearing',15,'mono',anchor='middle')
    d.text(272,198,'shin hub',15,'mono',anchor='middle')
    d.text(432,198,'bearing + carrier',15,'mono',anchor='middle')
    d.text(585,58,'Metal axle',18)
    d.text(585,86,'Retained independently',16,'muted')
    d.text(585,111,'of shell fasteners.',16,'muted')
    d.path('M 512 89 L 558 89 L 558 54 L 570 54','none','#97a98a',1)
    d.end()
    d.lines(915,1200,['At the hip: a supported roll cradle carries the hip-pitch motor.',
                     'The proximal knee motor bolts to a metal plate on the thigh root.',
                     'Use motor mounting faces, bearing carriers and a conductive heat path.',
                     'Resolve bolt access, cable loops, cooling and housing clearance in CAD.'],18,30)
    d.save('07-leg-assembly.svg')
