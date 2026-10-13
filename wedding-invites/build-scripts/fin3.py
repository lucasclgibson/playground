import sys, pikepdf
MM = 72/25.4; SLUG = 12.0; B = 3.0
ICC = sys.argv[1]
for path in sys.argv[2:]:
    import re; TW, TH = (127.0, 178.0) if '5x7' in path else map(float, re.search(r'_(\d+)x(\d+)mm', path).groups())
    pdf = pikepdf.open(path, allow_overwriting_input=True)
    icc = pdf.make_stream(open(ICC, 'rb').read()); icc.N = 4
    pdf.Root.OutputIntents = pikepdf.Array([pikepdf.Dictionary(Type=pikepdf.Name.OutputIntent, S=pikepdf.Name.GTS_PDFX,
        OutputConditionIdentifier=pikepdf.String('FOGRA51'), OutputCondition=pikepdf.String('PSO Coated v3'),
        RegistryName=pikepdf.String('http://www.color.org'), DestOutputProfile=icc)])
    for page in pdf.pages:
        page.TrimBox = pikepdf.Array([SLUG*MM, SLUG*MM, (SLUG+TW)*MM, (SLUG+TH)*MM])
        page.BleedBox = pikepdf.Array([(SLUG-B)*MM, (SLUG-B)*MM, (SLUG+TW+B)*MM, (SLUG+TH+B)*MM])
    pdf.save(path)
