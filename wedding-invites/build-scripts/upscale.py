import torch, numpy as np, sys, time
from PIL import Image
from spandrel import ModelLoader
torch.set_num_threads(4)
m=ModelLoader().load_from_file('models/RealESRGAN_x4plus.pth').eval()
src,dst=sys.argv[1],sys.argv[2]
img=np.asarray(Image.open(src).convert('RGB')).astype(np.float32)/255
H,W,_=img.shape; S=4; T=256; P=16
out=np.zeros((H*S,W*S,3),np.float32)
t0=time.time(); ys=list(range(0,H,T)); xs=list(range(0,W,T))
for i,y in enumerate(ys):
  for x in xs:
    y0,x0=max(y-P,0),max(x-P,0); y1,x1=min(y+T+P,H),min(x+T+P,W)
    t=torch.from_numpy(img[y0:y1,x0:x1].transpose(2,0,1))[None]
    with torch.no_grad(): r=m(t)[0].numpy().transpose(1,2,0)
    oy,ox=(y-y0)*S,(x-x0)*S; h,w=min(T,H-y)*S,min(T,W-x)*S
    out[y*S:y*S+h,x*S:x*S+w]=r[oy:oy+h,ox:ox+w]
  print(f'row {i+1}/{len(ys)} {time.time()-t0:.0f}s',flush=True)
Image.fromarray((np.clip(out,0,1)*255+0.5).astype(np.uint8)).save(dst)
print('done')
