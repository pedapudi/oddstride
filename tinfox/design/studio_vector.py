"""Editable paths for the selected studio silhouette; not dimensioned CAD."""


def ellipse(d, x, y, rx, ry, fill, stroke='none', width=1):
    d.raw(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')


def definitions(d):
    d.raw('''<defs>
      <linearGradient id="v-top" x1="0" y1="0" x2=".15" y2="1"><stop stop-color="#fffefa"/><stop offset=".5" stop-color="#e8e5df"/><stop offset="1" stop-color="#c7c4bd"/></linearGradient>
      <linearGradient id="v-side" x1="0" y1="0" x2=".25" y2="1"><stop stop-color="#e9e6df"/><stop offset=".45" stop-color="#d4d1ca"/><stop offset="1" stop-color="#aaa9a3"/></linearGradient>
      <linearGradient id="v-front" x1="0" y1="0" x2="1" y2=".7"><stop stop-color="#e5e2db"/><stop offset=".35" stop-color="#f1eee7"/><stop offset="1" stop-color="#bab9b3"/></linearGradient>
      <linearGradient id="v-thigh" x1="0" y1=".3" x2="1" y2=".65"><stop stop-color="#faf8f1"/><stop offset=".25" stop-color="#e4e1d9"/><stop offset=".65" stop-color="#c7c4bd"/><stop offset="1" stop-color="#a5a49e"/></linearGradient>
      <linearGradient id="v-bevel" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fffefa"/><stop offset=".45" stop-color="#dedbd4"/><stop offset="1" stop-color="#999b97"/></linearGradient>
      <linearGradient id="v-disc" x1="0" y1="0" x2=".9" y2="1"><stop stop-color="#f1efe9"/><stop offset=".35" stop-color="#d4d1ca"/><stop offset=".75" stop-color="#bdbbb4"/><stop offset="1" stop-color="#d6d4cd"/></linearGradient>
      <linearGradient id="v-ring" x1="0" y1="0" x2="1" y2=".3"><stop stop-color="#141615"/><stop offset=".3" stop-color="#474945"/><stop offset=".47" stop-color="#202321"/><stop offset=".8" stop-color="#0e1110"/><stop offset="1" stop-color="#424641"/></linearGradient>
      <linearGradient id="v-shin" x1="0" y1=".6" x2="1" y2=".3"><stop stop-color="#151817"/><stop offset=".3" stop-color="#424541"/><stop offset=".52" stop-color="#242826"/><stop offset=".74" stop-color="#4a4d48"/><stop offset="1" stop-color="#151817"/></linearGradient>
      <linearGradient id="v-belly" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#41433f"/><stop offset=".55" stop-color="#292c29"/><stop offset="1" stop-color="#121613"/></linearGradient>
      <radialGradient id="v-rubber" cx=".35" cy=".2" r=".9"><stop stop-color="#4b4d48"/><stop offset=".5" stop-color="#292c29"/><stop offset="1" stop-color="#101411"/></radialGradient>
      <linearGradient id="v-glass" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#272e2c"/><stop offset=".5" stop-color="#090d0c"/><stop offset="1" stop-color="#1c2320"/></linearGradient>
      <filter id="v-ground" x="-.4" y="-2" width="1.8" height="5"><feGaussianBlur stdDeviation="18"/></filter>
      <filter id="v-contact" x="-.5" y="-1" width="2" height="3"><feGaussianBlur stdDeviation="4"/></filter>
    </defs>''')


def bolt(d, x, y, r=4, dark=False):
    ellipse(d, x, y, r*.78, r, '#71746c' if dark else '#b5b5ad', '#383d36', .8)
    ellipse(d, x, y, r*.36, r*.48, '#141a15')
    d.path(f'M {x-r*.55} {y-r*.3} Q {x-r*.4} {y-r*.8} {x} {y-r*.8}', 'none', '#e2e0d7', .6)


def shin(d, stretch=1):
    # Structural graphite shell halves meet along the raised outer seam.
    d.group(f'translate(-200 220) scale({stretch} 1)')
    d.path('M -18 -3 C -22 28 -11 46 16 69 C 62 110 105 183 137 264 L 141 280 Q 144 292 158 287 L 191 276 C 151 207 108 123 63 67 C 43 41 30 19 24 -5 Z', 'url(#v-shin)', '#171c18', 1.6)
    d.path('M -3 26 C 10 55 39 71 67 109 C 100 154 134 218 154 270 L 174 265 C 142 199 108 134 74 91 C 47 57 28 37 19 15', 'none', '#666b61', 1.5)
    d.path('M 15 58 C 48 93 78 136 104 186 C 117 211 128 235 133 247 Q 137 254 142 251 C 128 206 94 141 64 102 C 44 77 27 58 20 56 Z', '#101612', '#4f564c', .9)
    d.path('M 30 78 C 69 121 106 184 130 239', 'none', '#7a8075', .75)
    d.path('M 29 14 Q 22 41 43 56 Q 48 63 44 67 Q 36 70 27 60 C 8 40 10 26 14 15 Z', '#0c120f', '#4f554d', 1)
    ellipse(d, 146, 263, 5, 9, '#0a100d')
    bolt(d, 146, 280, 4, True)
    bolt(d, 22, 50, 4, True)
    # Compact replaceable rubber foot; the shin ends above the contact surface.
    d.path('M 151 286 Q 166 276 187 282 Q 195 284 198 295 L 211 323 Q 216 336 199 340 Q 173 348 143 339 Q 125 335 129 324 L 139 299 Q 142 290 151 286 Z', 'url(#v-rubber)', '#111813', 1.3)
    d.path('M 131 326 Q 170 339 212 325 M 181 283 Q 190 302 194 327 Q 197 336 195 341', 'none', '#080e0a', 1.4)
    d.path('M 146 295 Q 151 290 163 289', 'none', '#71766b', 1)
    d.end()


def leg(d, x, y, scale=1, stretch=1, far=False):
    d.group(f'translate({x} {y}) scale({scale})')
    shin(d, stretch)
    # Small supported knee, not a distal motor. Outer cheek overlaps the shin fork.
    ellipse(d, -201, 223, 24, 34, 'url(#v-ring)', '#1b201b', 1)
    ellipse(d, -208, 224, 19, 27, '#292e28', '#676b60', .8)
    # Two curved load-bearing shell halves, split behind the visible face.
    d.path('M -37 -64 C -74 -61 -92 -31 -117 12 C -145 61 -179 117 -210 169 C -219 183 -223 194 -217 205 Q -206 222 -196 225 Q -181 229 -172 215 L -139 169 Q -117 158 -104 158 C -78 128 -51 98 -15 78 Q 35 52 40 16 Q 42 -32 9 -53 Z', 'url(#v-thigh)', '#aaa9a1', 1.2)
    d.path('M -42 -58 C -77 -53 -94 -17 -119 26 L -204 173 Q -217 195 -210 201', 'none', '#fffdf5', 2)
    d.path('M -104 158 C -81 132 -46 97 -13 76 Q 24 54 32 31', 'none', '#898d83', 1)
    d.path('M -172 215 Q -158 190 -139 169 Q -122 161 -105 158', 'none', '#8c9085', 1.1)
    d.path('M -171 219 Q -164 179 -137 170 L -149 201 Q -155 227 -143 248 L -151 267 Q -154 277 -162 270 C -188 244 -177 234 -171 219 Z', 'url(#v-ring)', '#151d15', 1)
    bolt(d, -38, 77, 5)
    bolt(d, -91, 125, 3)
    bolt(d, -186, 196, 3)
    bolt(d, -141, 178, 2.5, True)
    ellipse(d, -208, 224, 11, 16, 'url(#v-bevel)', '#0e150e', 1.4)
    ellipse(d, -208, 224, 4.5, 7, '#1b221b', '#b8bcb1', .8)
    if not far:
        # The broad shoulder volume is intentional; internal motor packing is unresolved.
        d.group('rotate(-14)')
        ellipse(d, 30, -4, 84, 100, 'url(#v-ring)', '#1b201b', 1.5)
        ellipse(d, 23, -4, 76, 95, 'none', '#656a60', 1)
        ellipse(d, 14, -2, 74, 93, 'url(#v-ring)', '#191f18', 1)
        ellipse(d, 4, 0, 72, 91, '#cccac2', '#62665b', 1)
        ellipse(d, -3, 0, 68, 88, 'url(#v-bevel)', '#fffdf6', 1)
        ellipse(d, -9, 0, 61, 81, 'url(#v-disc)', '#a1a396', 1)
        d.path('M -58 -38 Q -48 -75 -17 -78 Q 20 -81 43 -43', 'none', '#fffdf7', 1.4)
        d.path('M -49 52 L 44 -27', 'none', '#6b7164', 1.2)
        d.line(-41, -62, -42, -54, '#545e4d', .9)
        d.text(-29, 65, '170', 12, fill='#4c5545')
        d.path('M 79 -34 L 86 -32 L 86 -7 L 79 -8 Z', '#ff6c21', '#aa471b', .8)
        d.path('M 57 -76 L 67 -67', 'none', '#d87b42', 1.2)
        d.end()
    d.end()


def studio_robot(d):
    definitions(d)
    d.group('translate(70 155) scale(1.09)')
    d.raw('<g id="ground-shadow" opacity=".22" filter="url(#v-ground)">')
    ellipse(d, 783, 759, 538, 47, '#68685f')
    d.end()
    for x, y, rx in [(300, 769, 55), (632, 714, 46), (1310, 801, 51), (910, 879, 59)]:
        d.raw('<g opacity=".3" filter="url(#v-contact)">')
        ellipse(d, x, y, rx, 9, '#363b31')
        d.end()
    # Far legs are complete parts, occluded by the belly rather than detached strokes.
    d.raw('<g id="far-legs">')
    leg(d, 660, 253, .86, 1, True)
    leg(d, 1284, 314, .9, 1.2, True)
    d.end()
    d.raw('<g id="body-and-mounting-envelope">')
    # Upper far shoulder silhouettes and roll-module volume.
    d.path('M 536 111 Q 579 86 629 94 Q 667 89 695 114 L 735 145 L 572 151 Z', 'url(#v-top)', '#babbb2', 1)
    d.path('M 551 112 Q 591 87 645 104 L 675 129 L 555 131 Z', 'url(#v-ring)', '#797e73', 1)
    d.path('M 1040 159 Q 1091 128 1140 140 Q 1193 143 1220 184 L 1110 207 Z', 'url(#v-ring)', '#4a5246', 1)
    # Low structural belly: batteries recessed between the shoulder modules.
    d.path('M 417 250 L 1118 356 L 1306 360 Q 1288 392 1239 419 Q 1150 449 993 442 L 501 351 Q 437 339 417 302 Z', 'url(#v-belly)', '#1d251b', 1.4)
    d.path('M 473 291 L 822 352 L 806 409 L 500 351 Q 469 338 463 316 Z', '#20261e', '#5c6356', 1)
    d.path('M 549 309 Q 554 303 570 307 L 752 342 Q 774 348 781 363 L 795 399 Q 788 412 773 407 L 585 374 Q 557 368 551 347 Z', 'url(#v-belly)', '#090f0a', 2)
    d.path('M 559 313 L 746 349 Q 766 353 771 367 L 785 395', 'none', '#72786b', 1)
    d.path('M 678 318 L 730 327 L 730 338 L 681 329 Z', '#fd6a1c', '#823713', .8)
    d.path('M 685 321 L 724 328', 'none', '#ffb16c', 1)
    for x, y in [(501, 307), (562, 328), (755, 363), (804, 361), (1005, 419), (1214, 401)]:
        bolt(d, x, y, 5, True)
    # Side panel with deeper integrated shoulder arches.
    d.path('M 366 139 Q 424 118 490 134 L 1137 215 Q 1177 224 1182 266 L 1166 376 Q 1164 403 1130 407 L 1066 404 C 1082 346 1079 280 1039 237 C 1000 198 938 190 891 214 C 838 239 823 292 829 345 L 494 284 C 494 249 486 185 449 151 Q 416 128 366 139 Z', 'url(#v-side)', '#979b8e', 1.2)
    # Top crown, broad shallow chamfer and upper panel split.
    d.path('M 367 139 Q 407 119 491 111 Q 555 98 629 111 L 1062 150 Q 1121 147 1186 170 L 1298 203 Q 1331 213 1345 237 L 1164 264 Q 1115 230 1060 222 L 580 162 L 550 189 L 485 181 Q 474 146 446 136 Q 404 124 367 139 Z', 'url(#v-top)', '#c4c5b9', 1)
    d.path('M 582 161 L 1057 218 Q 1127 227 1163 259 L 1344 234', 'none', '#fffdf5', 1.6)
    d.path('M 638 124 Q 595 135 580 155 L 550 189 L 489 182 M 550 189 L 550 294', 'none', '#858e7c', .9)
    d.path('M 638 126 L 654 120', 'none', '#5e9495', 2)
    # Satin front shell and a recessed horizontal stereo window.
    d.path('M 1183 237 L 1324 218 Q 1349 220 1360 253 Q 1371 284 1365 326 Q 1362 359 1337 379 L 1180 401 Q 1133 408 1128 377 L 1127 289 Q 1131 248 1183 237 Z', 'url(#v-front)', '#979e8e', 1)
    d.path('M 1180 244 L 1323 226 Q 1346 229 1354 254', 'none', '#fffef6', 2)
    d.path('M 1175 282 L 1330 264 Q 1351 262 1351 282 L 1348 325 Q 1346 339 1333 341 L 1179 356 Q 1159 358 1158 340 L 1158 307 Q 1159 287 1175 282 Z', '#6e7569', '#f5f2e9', 2)
    d.path('M 1178 287 L 1328 270 Q 1344 268 1344 284 L 1342 322 Q 1340 334 1329 335 L 1182 350 Q 1166 352 1165 336 L 1165 307 Q 1166 291 1178 287 Z', 'url(#v-glass)', '#0c150d', 3)
    d.path('M 1180 290 L 1328 274 Q 1338 272 1339 281', 'none', '#4a5548', 1)
    for x, y in [(1200, 316), (1310, 302)]:
        ellipse(d, x, y, 15, 24, '#080e0a', '#3f4c3e', 1)
        ellipse(d, x, y, 10, 17, '#262f27', '#717d6b', .8)
        ellipse(d, x, y, 7, 12, 'url(#glass)', '#080f09', 1)
        ellipse(d, x-2, y-5, 2.2, 3.4, '#9cae9b')
    ellipse(d, 1260, 323, 3.5, 5, '#3d483b', '#727c69', .6)
    for x, y in [(1160, 264), (1152, 376), (1336, 353), (1342, 242), (850, 208), (500, 162), (500, 260), (1080, 392)]:
        bolt(d, x, y, 5)
    # Service graphics live on the side panel, not on the shoulder's moving surface.
    d.group('matrix(1 .14 0 1 568 274)')
    d.text(0, 0, 'tinfox', 25, fill='#3e4836')
    d.text(229, 9, '01', 14, fill='#49543f')
    d.end()
    ellipse(d, 530, 263, 4, 6, '#f47a2c', '#a85f25', .7)
    # Top display and low protected lidar turret.
    d.path('M 909 173 L 946 158 Q 955 155 970 157 L 1058 171 Q 1065 172 1058 177 L 1032 189 Z', '#242d27', '#fffdf5', 1)
    ellipse(d, 967, 170, 23, 5, 'none', '#a3c0ba', .8)
    d.path('M 959 168 L 972 169 M 1009 181 L 1018 182 M 1030 173 L 1035 174', 'none', '#a3c0ba', .7)
    ellipse(d, 1063, 194, 14, 5, '#ef7228', '#fff5d9', 1)
    ellipse(d, 1063, 193, 4, 1.5, 'none', '#fce2c4', .6)
    ellipse(d, 1095, 200, 4, 1.7, '#263026', '#fbf8ec', .7)
    d.path('M 1091 175 Q 1082 159 1107 151 L 1202 160 L 1263 192 Q 1274 200 1263 203 L 1196 198 Z', 'url(#v-ring)', '#9b9e92', 1)
    ellipse(d, 1164, 179, 61, 12, '#0b110c', '#5e6958', 1)
    d.path('M 1111 137 L 1111 171 Q 1116 183 1168 184 Q 1206 184 1216 176 L 1212 138 Z', 'url(#v-ring)', '#080e09', 1)
    for x in [1118, 1140, 1188, 1205]:
        d.path(f'M {x} 144 L {x+1} 173', 'none', '#6d7566', 2 if x==1140 else 1)
    ellipse(d, 1162, 137, 51, 8, 'url(#v-top)', '#fbf8ee', 1.4)
    ellipse(d, 1236, 196, 5, 2.3, '#0d170e', '#707c64', .8)
    d.end()
    d.raw('<g id="near-rear-leg">')
    leg(d, 350, 223, 1, .8)
    d.end()
    d.raw('<g id="near-front-leg">')
    leg(d, 935, 314, 1.03, 1.1)
    d.end()
    d.end()
