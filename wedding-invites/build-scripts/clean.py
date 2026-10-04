from PIL import Image
import numpy as np, cv2, sys
n=sys.argv[1]
img=np.asarray(Image.open(f'src/{n}.png').convert('RGB'))
a=img.astype(int); H,W=a.shape[:2]
R,G,B=a[...,0],a[...,1],a[...,2]
core=((B-R>60)&(R<150)).astype(np.uint8)
fx0,fy0,fx1,fy1={'day':(725,110,805,200),'evening':(825,155,905,235)}[n]
core[fy0:fy1,fx0:fx1]=0
weak=((B-R>6)&(B>=G)).astype(np.uint8); weak[fy0:fy1,fx0:fx1]=0
k3=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
m=core.copy()
for i in range(5): m=cv2.dilate(m,k3)&np.maximum(weak,core)
m=cv2.dilate(m,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
# explicit frame lines (geometry from profile analysis)
lines={'day':dict(cols=[1431,2166,2242,3009],rows=[(171,1420,3020),(1977,1420,3020)],extra=[(560,1945,830,1965)]),
       'evening':dict(cols=[35,1501,1553,2232,2305,3023],rows=[(22,25,1512),(2024,25,1512),(177,1545,3035),(1976,1545,3035)],extra=[])}[n]
for c in lines['cols']: m[:,c-6:c+7]=1
for r,xa,xb in lines['rows']:
  m[r-6:r+7,xa:xb]=1
for x0,y0,x1,y1 in lines['extra']: m[y0:y1,x0:x1]=1
# hearts / divider columns
bg=cv2.medianBlur(img,61).astype(int)
dev=(np.abs(a-bg).max(2)>10).astype(np.uint8)
cols={'day':[(736,1150,1950),(1796,620,1640),(2532,500,1560)],
      'evening':[(794,1200,1950),(1880,620,1620),(2564,500,1580)]}[n]
for cx,y0,y1 in cols:
  z=np.zeros_like(m); z[y0:y1,cx-75:cx+75]=1
  d=cv2.dilate(dev*z,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
  m=np.maximum(m,d*z)
m[fy0:fy1,fx0:fx1]=0
cv2.imwrite(f'clean/{n}_mask.png',m*255)
# fill: normalized convolution of unmasked pixels (smooth paper), then add matched grain
f=img.astype(np.float32); w=(1-m).astype(np.float32)
num=f*w[...,None]; out=f.copy()
for s in (8,20,50):
  sn=cv2.GaussianBlur(num,(0,0),s); sw=cv2.GaussianBlur(w,(0,0),s)
  est=sn/np.maximum(sw,1e-6)[...,None]
  if s==8: fill=est; have=sw>0.05
  else: fill=np.where(have[...,None],fill,est); have=have|(sw>0.05)
# grain: std of paper high-pass in clean area
hp=f-cv2.GaussianBlur(f,(0,0),3)
pm=(w>0)&(np.abs(a-bg).max(2)<6)
sd=hp[pm].std(0); print(n,'grain sd',sd)
rng=np.random.default_rng(1)
g=cv2.GaussianBlur(rng.normal(0,1,(H,W)).astype(np.float32),(0,0),0.8); g/=g.std()
fill=fill+g[...,None]*sd.mean()
mm=cv2.GaussianBlur(m.astype(np.float32),(0,0),1.5)[...,None]
mm=np.maximum(mm,m[...,None])
out=f*(1-mm)+fill*mm
Image.fromarray(np.clip(out,0,255).astype(np.uint8)).save(f'clean/{n}_clean.png')
