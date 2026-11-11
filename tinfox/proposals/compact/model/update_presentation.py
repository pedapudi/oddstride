"""Embed the CAD-derived studio image in the browser presentation."""
import base64,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
image=base64.b64encode((root/'design/09-cad-studio.png').read_bytes()).decode()
fingerprint=json.loads((root/'model/output/studio-provenance.json').read_text())['model_sha256']
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1550" viewBox="0 0 1800 1550" role="img" aria-labelledby="title desc">
<title id="title">Tinfox — CAD studio review</title><desc id="desc">Studio rendering of the exported solid assembly, with flange-driven hip roll and one pushrod per knee. Flexible shoulder seals are provisional neutral envelopes.</desc>
<rect width="1800" height="1550" fill="#eeeee7"/>
<rect x="45" y="36" width="12" height="12" fill="#f47732"/>
<text x="72" y="49" font-family="monospace" font-size="17" fill="#28392f">oddstride / tinfox 170</text>
<text x="45" y="107" font-family="Arial,sans-serif" font-size="36" fill="#28392f">Proximal actuation. Curved structural limbs.</text>
<image x="0" y="125" width="1800" height="1330" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{image}"/>
<text x="45" y="1478" font-family="Arial,sans-serif" font-size="20" fill="#28392f">12 × RS-02 · independent hip roll · 170 mm links · 1 kg cargo target</text>
<text x="45" y="1510" font-family="Arial,sans-serif" font-size="15" fill="#505b53">Rendered from CAD. Flexible seals are provisional. Load performance and manufacturing details remain unqualified.</text>
<!-- CAD SHA256 {fingerprint} -->
</svg>'''
(root/'design/06-studio-concept.svg').write_text(svg)
