"""Adds Trim/Bleed boxes and a CMYK output intent (PSO Coated v3 / FOGRA51) to the built PDFs."""
import sys, pikepdf
from build import SLUG, MM, TW, TH, B, ICC

for path in sys.argv[1:]:
    pdf = pikepdf.open(path, allow_overwriting_input=True)
    icc = pdf.make_stream(open(ICC, 'rb').read())
    icc.N = 4
    oi = pikepdf.Dictionary(Type=pikepdf.Name.OutputIntent, S=pikepdf.Name.GTS_PDFX,
                            OutputConditionIdentifier=pikepdf.String('FOGRA51'),
                            OutputCondition=pikepdf.String('PSO Coated v3 (ISO 12647-2:2013, paper type 1)'),
                            RegistryName=pikepdf.String('http://www.color.org'),
                            Info=pikepdf.String('PSO Coated v3'),
                            DestOutputProfile=icc)
    pdf.Root.OutputIntents = pikepdf.Array([oi])
    t = [SLUG * MM, SLUG * MM, (SLUG + TW) * MM, (SLUG + TH) * MM]
    bl = [(SLUG - B) * MM, (SLUG - B) * MM, (SLUG + TW + B) * MM, (SLUG + TH + B) * MM]
    for page in pdf.pages:
        page.TrimBox = pikepdf.Array(t)
        page.BleedBox = pikepdf.Array(bl)
    pdf.save(path)
    print('finalized', path)
