"""
Convert every MathML expression in the books and write the LaTeX to
data/check/latex.json, for scripts/check_latex.mjs to render.

Taken from the converter directly rather than fished out of the corpus
text with a regex, because word problems contain literal dollar signs
that a regex would mistake for maths delimiters.
"""

import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoformer.mathml import M, mathml_to_latex  # noqa: E402

modules = sorted((ROOT / "data" / "raw" / "openstax-algebra" / "modules").glob("*/index.cnxml"))
out = []
for path in modules:
    for el in ET.parse(path).getroot().iter(M + "math"):
        out.append({"module": path.parent.name, "latex": mathml_to_latex(el)})

dest = ROOT / "data" / "check" / "latex.json"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(out, ensure_ascii=False))
print(f"{len(out)} expressions from {len(modules)} modules -> {dest.relative_to(ROOT)}")
