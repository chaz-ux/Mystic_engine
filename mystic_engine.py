

import cv2
import mediapipe as mp
import numpy as np
import time, math, random, sys
from collections import deque

# ─────────────────────────────────────────────────────────────────────────────
# PALETTE  (BGR)
# ─────────────────────────────────────────────────────────────────────────────
C_GOLD        = (0,   200, 255)
C_ORANGE_HOT  = (0,   140, 255)
C_ORANGE_CORE = (40,  210, 255)
C_ORANGE_DIM  = (0,    80, 160)
C_BLUE_COLD   = (255, 100,  40)
C_BLUE_BRIGHT = (255, 180,  80)
C_CYAN        = (255, 220,  80)
C_RED_BAND    = (0,     0, 200)
C_RED_BRIGHT  = (60,   60, 255)
C_GREEN_STONE = (0,   255,  80)
C_GREEN_DIM   = (0,   120,  30)
C_PURPLE      = (200,  40, 160)
C_PURPLE_DIM  = (120,  20,  80)
C_YELLOW      = (0,   220, 255)
C_WHITE       = (255, 255, 255)
C_UI_BG       = (12,    5,  20)


# ══════════════════════════════════════════════════════════════════════════════
# 1.  MATH
# ══════════════════════════════════════════════════════════════════════════════
class M:
    @staticmethod
    def rot3(x, y, z, ax, ay, az):
        cx,sx = math.cos(ax),math.sin(ax)
        y1=y*cx-z*sx; z1=y*sx+z*cx
        cy,sy = math.cos(ay),math.sin(ay)
        x2=x*cy+z1*sy; z2=-x*sy+z1*cy
        cz,sz = math.cos(az),math.sin(az)
        return x2*cz-y1*sz, x2*sz+y1*cz, z2

    @staticmethod
    def proj(x,y,z,fov=260,vd=420):
        d=vd+z; f=fov/d if d else 1
        return int(x*f),int(y*f),f

    @staticmethod
    def bezier(p0,p1,p2,p3,n=24):
        pts=[]
        for i in range(n):
            t=i/(n-1); u=1-t
            pts.append((int(u**3*p0[0]+3*u**2*t*p1[0]+3*u*t**2*p2[0]+t**3*p3[0]),
                        int(u**3*p0[1]+3*u**2*t*p1[1]+3*u*t**2*p2[1]+t**3*p3[1])))
        return pts

    @staticmethod
    def lerp(a,b,t): return a+(b-a)*t


# ══════════════════════════════════════════════════════════════════════════════
# 2.  PARTICLE
# ══════════════════════════════════════════════════════════════════════════════
class Spark:
    __slots__=('x','y','vx','vy','life','max_life','size','grav','drag','pal')

    FIRE  =[(255,255,255),(160,220,255),(60,160,255),(0,100,220),(0,40,120),(0,10,40)]
    TRACE =[(255,255,220),(80,210,255),(0,160,255),(0,80,180),(0,20,60)]
    GREEN =[(220,255,220),(80,255,150),(0,200,80),(0,100,30),(0,30,10)]
    ELEC  =[(255,255,255),(200,255,255),(100,200,255),(40,100,200),(10,30,80)]
    SHIELD=[(255,255,255),(200,220,255),(100,160,255),(40,80,200),(0,20,80)]
    WIND  =[(255,255,255),(200,200,255),(120,100,200),(60,40,120),(20,10,50)]

    def __init__(self,x,y,vx,vy,life,size=2,grav=0.5,drag=0.93,pal=None):
        self.x,self.y=float(x),float(y)
        self.vx,self.vy=float(vx),float(vy)
        self.life=self.max_life=float(life)
        self.size=size; self.grav=grav; self.drag=drag
        self.pal=pal or self.FIRE

    def tick(self):
        self.x+=self.vx; self.y+=self.vy
        self.vy+=self.grav; self.vx*=self.drag; self.vy*=self.drag
        self.life-=random.uniform(0.6,1.9)
        return self.life>0

    def col(self):
        idx=int((1-self.life/self.max_life)*(len(self.pal)-1))
        return self.pal[min(idx,len(self.pal)-1)]

    def draw(self,layer):
        cv2.circle(layer,(int(self.x),int(self.y)),self.size,self.col(),-1)


# ══════════════════════════════════════════════════════════════════════════════
# 3.  SLING RING TRACE
# ══════════════════════════════════════════════════════════════════════════════
class SlingRingTrace:
    MAX_PTS = 90

    def __init__(self):
        self.pts    = deque(maxlen=self.MAX_PTS)
        self.sparks = []
        self.active = False

    def add(self,x,y):
        self.pts.append((x,y))
        self.active = True
        for _ in range(3):
            self.sparks.append(Spark(x,y,random.gauss(0,2),random.gauss(0,2),
                                     random.randint(6,16),random.randint(1,3),
                                     grav=0.0,drag=0.82,pal=Spark.TRACE))

    def draw(self,layer):
        pts=list(self.pts); n=len(pts)
        if n<2: return
        for i in range(1,n):
            af=i/n
            thick_out=max(1,int(af*9)); thick_in=max(1,int(af*4))
            col_out=(int(C_GOLD[0]*af),int(C_GOLD[1]*af),int(C_GOLD[2]*af))
            cv2.line(layer,pts[i-1],pts[i],col_out,thick_out,cv2.LINE_AA)
            cv2.line(layer,pts[i-1],pts[i],C_WHITE,thick_in,cv2.LINE_AA)
        tx,ty=pts[-1]
        cv2.circle(layer,(tx,ty),14,C_ORANGE_CORE,-1)
        cv2.circle(layer,(tx,ty),20,C_GOLD,2,cv2.LINE_AA)
        cv2.circle(layer,(tx,ty),26,(0,100,160),1,cv2.LINE_AA)
        alive=[]
        for s in self.sparks:
            if s.tick(): s.draw(layer); alive.append(s)
        self.sparks=alive

    def consume(self):
        pts=list(self.pts)
        self.pts.clear(); self.sparks.clear(); self.active=False
        return pts


# ══════════════════════════════════════════════════════════════════════════════
# 4.  PORTAL GATEWAY
# ══════════════════════════════════════════════════════════════════════════════
class PortalGateway:
    STARS=[(random.gauss(0,0.35),random.gauss(0,0.35),
            random.uniform(0.4,1.5),random.randint(1,3)) for _ in range(120)]

    def __init__(self,cx,cy,target_r):
        self.cx,self.cy=cx,cy
        self.target_r=float(target_r)
        self.radius=6.0
        self.angle=random.uniform(0,math.pi*2)
        self.born=time.time()
        self.duration=13.0
        self.closing=False
        self.iris_angle=0.0
        self.ring_sparks=[]
        self.flare_sparks=[]

    def _draw_interior(self,frame,r):
        h,w=frame.shape[:2]
        cx,cy=self.cx,self.cy
        y0=max(0,cy-r-2); y1=min(h,cy+r+2)
        x0=max(0,cx-r-2); x1=min(w,cx+r+2)
        if y1<=y0 or x1<=x0: return
        ys=np.arange(y0,y1,dtype=np.float32)
        xs=np.arange(x0,x1,dtype=np.float32)
        xg,yg=np.meshgrid(xs,ys)
        nx=(xg-cx)/r; ny=(yg-cy)/r
        dist2=nx*nx+ny*ny
        inside=(dist2<=1.0)
        k=0.4; barrel=1.0-k*dist2
        t_=time.time()
        sx=nx*barrel+math.sin(t_*0.3)*0.15
        sy=ny*barrel+math.cos(t_*0.2)*0.08
        map_x=np.clip((sx*r+cx).astype(np.float32),0,w-1)
        map_y=np.clip((sy*r+cy).astype(np.float32),0,h-1)
        roi_h=y1-y0; roi_w=x1-x0
        warped=cv2.remap(frame,map_x[:roi_h,:roi_w],map_y[:roi_h,:roi_w],
                         cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
        tint=np.zeros_like(warped); tint[:]=(30,8,50)
        warped=cv2.addWeighted(warped,0.45,tint,0.55,0)
        d_norm=np.sqrt((xg-cx)**2+(yg-cy)**2)/r
        alpha=np.clip(1.0-d_norm,0,1)*inside.astype(np.float32)
        alpha3=np.stack([alpha]*3,axis=2)
        orig=frame[y0:y1,x0:x1].astype(np.float32)
        frame[y0:y1,x0:x1]=(orig*(1-alpha3)+warped.astype(np.float32)*alpha3).astype(np.uint8)
        t2=time.time()
        for sx2,sy2,bright,sz in self.STARS:
            px=cx+int(sx2*r*0.85); py=cy+int(sy2*r*0.85)
            if 0<=px<w and 0<=py<h:
                b=int(bright*160*(0.6+0.4*math.sin(t2*bright*4)))
                cv2.circle(frame,(px,py),sz,(b,b,b),-1)

    def _draw_ring(self,layer,r):
        t=time.time()
        specs=[( 0,0,  0,  C_WHITE,      1),
               ( 3,3,1.1,  C_ORANGE_CORE,3),
               ( 8,5,0.8,  C_ORANGE_HOT, 4),
               (14,7,1.4,  C_GOLD,       3),
               (20,4,0.6,  C_ORANGE_DIM, 5),
               (26,8,1.7,  (0,40,100),   6)]
        for offset,amp,freq,col,thick in specs:
            pts=[]
            for i in range(128):
                a=2*math.pi*i/128+self.angle
                w_=1.0+(amp/r)*math.sin(freq*a+t*3) if r>0 else 1.0
                pr=(r+offset)*w_
                pts.append([self.cx+int(math.cos(a)*pr),self.cy+int(math.sin(a)*pr)])
            cv2.polylines(layer,[np.array(pts)],True,col,thick,cv2.LINE_AA)

    def _iris_close(self,layer,r):
        for i in range(8):
            a=self.iris_angle+i*math.pi/4
            cv2.ellipse(layer,(self.cx,self.cy),(max(1,r),max(1,r)),0,
                        math.degrees(a),math.degrees(a)+40,C_ORANGE_HOT,6,cv2.LINE_AA)
        self.iris_angle+=0.15

    def update_and_draw(self,layer,frame):
        alive=(time.time()-self.born)<self.duration
        if not alive: self.closing=True
        if not self.closing:
            self.radius+=(self.target_r-self.radius)*0.09
            draw_r=int(self.radius+math.sin(time.time()*1.4)*4)
        else:
            self.radius*=0.80; draw_r=int(self.radius)
        self.angle+=0.10; r=max(0,draw_r)
        if r>12:
            if not self.closing: self._draw_interior(frame,r)
            else: self._iris_close(layer,r)
            self._draw_ring(layer,r)
            # ── ring sparks (tangential) ─────────────────────────────────
            for _ in range(20):
                ea=random.uniform(0,math.pi*2)
                px_=self.cx+math.cos(ea)*r; py_=self.cy+math.sin(ea)*r
                tang=ea+math.pi/2; spd=random.uniform(5,24)
                self.ring_sparks.append(
                    Spark(px_,py_,math.cos(tang)*spd+random.gauss(0,3),
                                  math.sin(tang)*spd+random.gauss(0,3),
                          random.randint(15,55),random.randint(1,4)))
            # ── flare sparks (radial) ────────────────────────────────────
            if random.random()>0.7:
                ea=random.uniform(0,math.pi*2); spd=random.uniform(15,35)
                self.flare_sparks.append(
                    Spark(self.cx+math.cos(ea)*r,self.cy+math.sin(ea)*r,
                          math.cos(ea)*spd,math.sin(ea)*spd,
                          random.randint(20,40),random.randint(2,5),grav=0.3,drag=0.90))
        # ── update + draw sparks ONCE ────────────────────────────────────
        next_ring=[]; 
        for s in self.ring_sparks:
            if s.tick(): s.draw(layer); next_ring.append(s)
        self.ring_sparks=next_ring
        next_flare=[]
        for s in self.flare_sparks:
            if s.tick(): s.draw(layer); next_flare.append(s)
        self.flare_sparks=next_flare
        return self.radius>4 or len(self.ring_sparks)+len(self.flare_sparks)>0


# ══════════════════════════════════════════════════════════════════════════════
# 5.  TIME STONE  (index-only gesture — point at screen)
# ══════════════════════════════════════════════════════════════════════════════
class TimeStone:
    def __init__(self):
        self.history=deque(maxlen=120)
        self.particles=[]
        self.rewind_cnt=0

    def store(self,frame):
        self.history.append(frame.copy())

    def _draw_eye(self,layer,cx,cy,t):
        ew,eh=90,35
        ctrl_top=[(cx-ew,cy),(cx-ew//2,cy-eh*2),(cx+ew//2,cy-eh*2),(cx+ew,cy)]
        ctrl_bot=[(cx-ew,cy),(cx-ew//2,cy+eh),(cx+ew//2,cy+eh),(cx+ew,cy)]
        cv2.polylines(layer,[np.array(M.bezier(*ctrl_top,32))],False,C_GREEN_STONE,2,cv2.LINE_AA)
        cv2.polylines(layer,[np.array(M.bezier(*ctrl_bot,32))],False,C_GREEN_STONE,2,cv2.LINE_AA)
        pr=int(22+math.sin(t*4)*5)
        cv2.circle(layer,(cx,cy),pr,C_GREEN_STONE,2,cv2.LINE_AA)
        cv2.circle(layer,(cx,cy),pr-8,(0,180,60),2,cv2.LINE_AA)
        cv2.circle(layer,(cx,cy),6,(150,255,150),-1)
        for i,(spd,ax_,ay_) in enumerate([(1.0,70,22),(0.7,70,22),(0.4,90,30)]):
            cv2.ellipse(layer,(cx,cy),(ax_,ay_),math.degrees(t*spd)+i*60,0,360,
                        C_GREEN_STONE if i==0 else C_GREEN_DIM,1,cv2.LINE_AA)
        for i in range(8):
            a=-t*1.8+i*math.pi/4
            px=cx+int(math.cos(a)*120); py=cy+int(math.sin(a)*120)
            cv2.circle(layer,(px,py),int(4+2*math.sin(t*3+i)),C_GREEN_STONE,-1)
            cv2.line(layer,(cx,cy),(px,py),(0,60,20),1,cv2.LINE_AA)

    def _warp(self,frame,t):
        h,w=frame.shape[:2]
        result=frame.copy()
        # subtle green tint
        green=np.zeros_like(frame); green[:,:,1]=55
        result=cv2.addWeighted(result,0.80,green,0.20,0)
        # per-row displacement — FIXED: clamp shift to valid range
        for y in range(0,h,2):
            shift=int(math.sin(y*0.08+t*8)*14+math.sin(y*0.03+t*5)*8+random.gauss(0,2))
            shift=max(-(w-1),min(w-1,shift))  # clamp
            if shift==0: continue
            if shift>0:
                result[y,shift:w]=frame[y,0:w-shift]
                result[y,0:shift]=0
            else:
                s=abs(shift)
                result[y,0:w-s]=frame[y,s:w]
                result[y,w-s:w]=0
        # occasional glitch row
        if random.random()>0.88:
            gy=random.randint(0,h-1); result[gy]=result[gy][::-1]
        # green scanlines
        for y in range(0,h,14):
            if random.random()>0.6:
                alpha=random.uniform(0.3,0.8)
                row=result[y].astype(np.float32)
                row[:,1]=np.clip(row[:,1]+150*alpha,0,255)
                result[y]=row.astype(np.uint8)
        return result

    def process(self,frame,layer,cx,cy,t,active):
        self.rewind_cnt=0
        if active and self.history:
            self.rewind_cnt=len(self.history)
            frame[:]=self._warp(self.history.pop(),t)
            self._draw_eye(layer,cx,cy,t)
            if random.random()>0.5:
                for _ in range(4):
                    a=random.uniform(0,math.pi*2); spd=random.uniform(2,8)
                    self.particles.append(
                        Spark(cx+random.gauss(0,20),cy+random.gauss(0,20),
                              math.cos(a)*spd,math.sin(a)*spd,
                              random.randint(12,30),random.randint(1,3),
                              grav=-0.1,drag=0.88,pal=Spark.GREEN))
        alive=[]
        for p in self.particles:
            if p.tick(): p.draw(layer); alive.append(p)
        self.particles=alive
        return self.rewind_cnt


# ══════════════════════════════════════════════════════════════════════════════
# 6.  WAND OF WATOOMB  (index-only pointing gesture → lightning)
# ══════════════════════════════════════════════════════════════════════════════
class WandOfWatoomb:
    def __init__(self):
        self.target=None
        self.target_life=0
        self.sparks=[]

    def _lightning_seg(self,layer,p1,p2,depth=4,spread=18):
        """Recursive branching lightning between two points."""
        if depth==0:
            cv2.line(layer,p1,p2,C_WHITE,1,cv2.LINE_AA)
            return
        mid=((p1[0]+p2[0])//2+(random.randint(-spread,spread)),
             (p1[1]+p2[1])//2+(random.randint(-spread,spread)))
        col=C_BLUE_BRIGHT if depth>2 else (100,180,255)
        thick=depth
        cv2.line(layer,p1,mid,col,thick,cv2.LINE_AA)
        cv2.line(layer,mid,p2,col,thick,cv2.LINE_AA)
        self._lightning_seg(layer,p1,mid,depth-1,spread//2)
        self._lightning_seg(layer,mid,p2,depth-1,spread//2)
        # branch
        if depth==3 and random.random()>0.5:
            branch_end=(mid[0]+random.randint(-60,60),mid[1]+random.randint(-60,60))
            self._lightning_seg(layer,mid,branch_end,depth-2,spread//3)

    def draw(self,layer,tip_x,tip_y,t,W,H):
        # Refresh target occasionally
        self.target_life-=1
        if self.target_life<=0:
            self.target=(random.randint(W//4,3*W//4),random.randint(H//4,3*H//4))
            self.target_life=random.randint(8,20)

        tx,ty=self.target
        # Draw main bolt
        self._lightning_seg(layer,(tip_x,tip_y),(tx,ty),depth=5,spread=25)
        # Hot tip
        cv2.circle(layer,(tip_x,tip_y),12,(200,230,255),-1)
        cv2.circle(layer,(tip_x,tip_y),20,C_BLUE_BRIGHT,2,cv2.LINE_AA)
        # Impact glow
        cv2.circle(layer,(tx,ty),15,C_WHITE,-1)
        cv2.circle(layer,(tx,ty),25,(150,200,255),3,cv2.LINE_AA)
        # Sparks from impact
        if random.random()>0.3:
            for _ in range(6):
                a=random.uniform(0,math.pi*2); spd=random.uniform(3,12)
                self.sparks.append(
                    Spark(tx,ty,math.cos(a)*spd,math.sin(a)*spd,
                          random.randint(8,20),2,grav=0.4,drag=0.88,pal=Spark.ELEC))
        alive=[]
        for s in self.sparks:
            if s.tick(): s.draw(layer); alive.append(s)
        self.sparks=alive


# ══════════════════════════════════════════════════════════════════════════════
# 7.  SHIELD OF THE SERAPHIM  (palm-up cupped hand)
# ══════════════════════════════════════════════════════════════════════════════
class ShieldSeraphim:
    def __init__(self):
        self.radius=0.0
        self.sparks=[]
        self.hit_sparks=[]
        self.t=0.0

    def draw(self,layer,cx,cy,t):
        self.t=t
        # Expanding pulsing rings
        pulse=math.sin(t*3)*8
        for i,frac in enumerate([1.0,0.85,0.65,0.45]):
            r=int(110*frac+pulse)
            alpha=0.4+0.6*frac
            col=(int(C_BLUE_COLD[0]*alpha),int(C_BLUE_COLD[1]*alpha),int(C_BLUE_COLD[2]*alpha))
            thick=3 if i==0 else 1
            cv2.circle(layer,(cx,cy),r,col,thick,cv2.LINE_AA)

        # Hex grid pattern on surface
        outer_r=110
        for i in range(6):
            a=t*0.5+i*math.pi/3
            hx=cx+int(math.cos(a)*outer_r*0.6)
            hy=cy+int(math.sin(a)*outer_r*0.6)
            for j in range(6):
                a2=j*math.pi/3
                ex=hx+int(math.cos(a2)*30)
                ey=hy+int(math.sin(a2)*30)
                cv2.line(layer,(hx,hy),(ex,ey),(100,140,200),1,cv2.LINE_AA)

        # Orbiting energy nodes
        for i in range(8):
            a=-t*1.2+i*math.pi/4
            nx=cx+int(math.cos(a)*110)
            ny=cy+int(math.sin(a)*110)
            cv2.circle(layer,(nx,ny),6,C_BLUE_BRIGHT,-1)
            cv2.circle(layer,(nx,ny),10,C_BLUE_COLD,1,cv2.LINE_AA)

        # Central core
        cv2.circle(layer,(cx,cy),12,(200,220,255),-1)

        # Ambient sparks
        if random.random()>0.6:
            a=random.uniform(0,math.pi*2)
            r_=random.uniform(80,120)
            px=cx+math.cos(a)*r_; py=cy+math.sin(a)*r_
            self.sparks.append(
                Spark(px,py,math.cos(a+math.pi/2)*random.uniform(1,4),
                           math.sin(a+math.pi/2)*random.uniform(1,4),
                      random.randint(8,18),2,grav=0.0,drag=0.85,pal=Spark.SHIELD))
        alive=[]
        for s in self.sparks:
            if s.tick(): s.draw(layer); alive.append(s)
        self.sparks=alive


# ══════════════════════════════════════════════════════════════════════════════
# 8.  MIRROR DIMENSION  (rebuilt — emanates from hands outward)
# ══════════════════════════════════════════════════════════════════════════════
def draw_mirror_dimension(frame,layer,poses,t):
    """
    Prismatic triangle fans grow outward from each hand's palm.
    Much more coherent than random screen triangles.
    """
    h,w=frame.shape[:2]
    for p in poses:
        cx,cy=p['palm']
        # Fan of triangles radiating outward
        n_fans=12
        for i in range(n_fans):
            base_a=t*0.4+i*(2*math.pi/n_fans)
            # Inner triangle
            dist1=int(80+40*math.sin(t*2+i))
            dist2=int(dist1+50+20*math.cos(t*1.5+i))
            spread=math.pi/n_fans*1.4

            p1=(cx+int(math.cos(base_a-spread)*dist1),
                cy+int(math.sin(base_a-spread)*dist1))
            p2=(cx+int(math.cos(base_a)*dist2),
                cy+int(math.sin(base_a)*dist2))
            p3=(cx+int(math.cos(base_a+spread)*dist1),
                cy+int(math.sin(base_a+spread)*dist1))
            pts=np.array([p1,p2,p3])

            hue=int((t*30+i*25)%180)
            col=cv2.cvtColor(np.uint8([[[hue,200,180]]]),cv2.COLOR_HSV2BGR)[0][0].tolist()
            # Draw on frame (fill) and layer (outline)
            overlay=frame.copy()
            cv2.fillPoly(overlay,[pts],col)
            frame[:]=cv2.addWeighted(frame,0.92,overlay,0.08,0)
            cv2.polylines(layer,[pts],True,C_WHITE,1,cv2.LINE_AA)

        # Central vortex
        for ring in range(3):
            r=int(30+ring*25+math.sin(t*3+ring)*8)
            cv2.circle(layer,(cx,cy),r,C_PURPLE,1,cv2.LINE_AA)


# ══════════════════════════════════════════════════════════════════════════════
# 9.  WINDS OF WATOOMB  (both hands open, shockwave)
# ══════════════════════════════════════════════════════════════════════════════
class WindsOfWatoomb:
    def __init__(self):
        self.shockwaves=[]  # each: [cx,cy,r,max_r,life]

    def trigger(self,cx,cy):
        self.shockwaves.append([cx,cy,10,350,40])

    def draw(self,frame,layer,t):
        h,w=frame.shape[:2]
        next_sw=[]
        for sw in self.shockwaves:
            cx,cy,r,max_r,life=sw
            if life<=0: continue
            frac=r/max_r
            # Distort pixels radially outward from shockwave front
            ring_w=30
            y0=max(0,cy-r-ring_w); y1=min(h,cy+r+ring_w)
            x0=max(0,cx-r-ring_w); x1=min(w,cx+r+ring_w)
            if y1>y0 and x1>x0:
                roi=frame[y0:y1,x0:x1].copy()
                rh,rw=roi.shape[:2]
                ys_=np.arange(y0,y1,dtype=np.float32)
                xs_=np.arange(x0,x1,dtype=np.float32)
                xg,yg=np.meshgrid(xs_,ys_)
                dx=xg-cx; dy=yg-cy
                dist=np.sqrt(dx*dx+dy*dy)+1e-6
                # Push pixels away from shockwave ring
                ring_dist=np.abs(dist-r)
                strength=np.exp(-ring_dist**2/(ring_w**2*0.3))*20*(life/40)
                nx=np.clip(xg+dx/dist*strength,0,w-1).astype(np.float32)
                ny=np.clip(yg+dy/dist*strength,0,h-1).astype(np.float32)
                warped=cv2.remap(frame,nx[:rh,:rw],ny[:rh,:rw],
                                 cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
                frame[y0:y1,x0:x1]=warped
            # Draw the ring itself
            alpha=int(255*(life/40)*(1-frac)*2)
            alpha=max(0,min(255,alpha))
            col=(alpha//4,alpha//2,alpha)
            if r>0:
                cv2.circle(layer,(cx,cy),r,col,max(1,int(6*(1-frac))),cv2.LINE_AA)
                cv2.circle(layer,(cx,cy),int(r*1.05),C_WHITE,1,cv2.LINE_AA)
            sw[2]=r+12; sw[4]=life-1
            next_sw.append(sw)
        self.shockwaves=next_sw


# ══════════════════════════════════════════════════════════════════════════════
# 10.  TAO MANDALA
# ══════════════════════════════════════════════════════════════════════════════
class EldritchMandala:
    @staticmethod
    def draw(img,cx,cy,t,radius,color=C_BLUE_COLD):
        r=radius
        tx=math.sin(t*0.47)*0.9; ty=math.cos(t*0.31)*0.6
        pts=[]
        for deg in range(0,360,8):
            rad=math.radians(deg)+t*0.6
            x3,y3,z3=M.rot3(math.cos(rad)*r*1.15,math.sin(rad)*r*1.15,0,tx,ty,0)
            px,py,_=M.proj(x3,y3,z3); pts.append([cx+px,cy+py])
        cv2.polylines(img,[np.array(pts)],True,color,1,cv2.LINE_AA)
        for frac in (1.0,0.88,0.20):
            cv2.circle(img,(cx,cy),int(r*frac),color,2 if frac!=0.88 else 1,cv2.LINE_AA)
        sq1,sq2=[],[]
        for i in range(4):
            a1=t+i*math.pi/2; a2=-t+i*math.pi/2+math.pi/4
            sq1.append([cx+int(math.cos(a1)*r),cy+int(math.sin(a1)*r)])
            sq2.append([cx+int(math.cos(a2)*int(r*.88)),cy+int(math.sin(a2)*int(r*.88))])
        cv2.polylines(img,[np.array(sq1)],True,color,2,cv2.LINE_AA)
        cv2.polylines(img,[np.array(sq2)],True,color,2,cv2.LINE_AA)
        oct_pts=[]
        for i in range(8):
            a=t*2+i*math.pi/4
            oct_pts.append([cx+int(math.cos(a)*int(r*.5)),cy+int(math.sin(a)*int(r*.5))])
        cv2.polylines(img,[np.array(oct_pts)],True,color,1,cv2.LINE_AA)
        for i in range(12):
            a=-t*1.5+i*math.pi/6
            cv2.line(img,(cx+int(math.cos(a)*int(r*.2)),cy+int(math.sin(a)*int(r*.2))),
                        (cx+int(math.cos(a)*int(r*.5)),cy+int(math.sin(a)*int(r*.5))),color,1,cv2.LINE_AA)
        for i in range(8):
            a=t+i*math.pi/4; gx=cx+int(math.cos(a)*r); gy=cy+int(math.sin(a)*r)
            cv2.circle(img,(gx,gy),5,C_CYAN,-1,cv2.LINE_AA)
            cv2.circle(img,(gx,gy),8,color,1,cv2.LINE_AA)
        pts2=[]
        for deg in range(0,360,10):
            rad=math.radians(deg)-t*0.4
            x3,y3,z3=M.rot3(math.cos(rad)*r*.7,0,math.sin(rad)*r*.7,0,t*.3,t*.2)
            px,py,_=M.proj(x3,y3,z3); pts2.append([cx+px,cy+py])
        cv2.polylines(img,[np.array(pts2)],True,(180,120,60),1,cv2.LINE_AA)


# ══════════════════════════════════════════════════════════════════════════════
# 11.  CRIMSON BANDS
# ══════════════════════════════════════════════════════════════════════════════
def draw_crimson_bands(layer,p1,p2,t):
    dist=math.hypot(p1[0]-p2[0],p1[1]-p2[1])
    if dist<1: return
    cv2.line(layer,p1,p2,(0,0,120),8,cv2.LINE_AA)
    cv2.line(layer,p1,p2,C_RED_BAND,4,cv2.LINE_AA)
    cv2.line(layer,p1,p2,C_RED_BRIGHT,1,cv2.LINE_AA)
    steps=max(3,int(dist/40))
    for s in range(1,steps):
        f=s/steps
        sx=int(p1[0]+(p2[0]-p1[0])*f); sy=int(p1[1]+(p2[1]-p1[1])*f)
        jx=sx+int(math.sin(t*(4+s)+f*10)*18); jy=sy+int(math.cos(t*(3+s)+f*7)*18)
        cv2.circle(layer,(jx,jy),random.randint(2,5),C_WHITE,-1)
    om=dist*0.45
    for i in range(6):
        phase=t*(1.8+i*0.3)
        c1=(p1[0]+int(math.cos(phase)*om),p1[1]+int(math.sin(phase)*om))
        c2=(p2[0]+int(math.cos(phase+math.pi)*om),p2[1]+int(math.sin(phase+math.pi)*om))
        curve=M.bezier(p1,c1,c2,p2,18)
        for j in range(1,len(curve)):
            cv2.line(layer,curve[j-1],curve[j],C_RED_BAND,2,cv2.LINE_AA)


# ══════════════════════════════════════════════════════════════════════════════
# 12.  BLOOM
# ══════════════════════════════════════════════════════════════════════════════
def apply_bloom(magic_u8):
    src=magic_u8.astype(np.float32)
    gray=cv2.cvtColor(magic_u8,cv2.COLOR_BGR2GRAY)
    _,mask=cv2.threshold(gray,55,255,cv2.THRESH_BINARY)
    mask3=np.stack([mask]*3,axis=2).astype(np.float32)/255.0
    bright=src*mask3
    g_near=cv2.GaussianBlur(bright,(11,11),0)
    g_wide=cv2.GaussianBlur(bright,(51,51),0)
    g_super=cv2.GaussianBlur(src,(101,101),0)
    return np.clip(src+g_near+g_wide*0.65+g_super*0.20,0,255).astype(np.uint8)


# ══════════════════════════════════════════════════════════════════════════════
# 13.  GESTURE ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class Debounce:
    def __init__(self,hold=5):
        self._c={}; self._s={}; self._hold=hold

    def update(self,name,raw):
        c=min(self._c.get(name,0)+1,self._hold+2) if raw else max(self._c.get(name,0)-1,0)
        self._c[name]=c
        if c>=self._hold: self._s[name]=True
        elif c<=1:        self._s[name]=False
        return self._s.get(name,False)


def analyze_hand(lm,w,h):
    """
    FIXED: thumb uses X-axis (horizontal) comparison, not Y-axis.
    All others use Y-axis (finger curled = tip above knuckle in screen coords).
    """
    # Thumb: tip is to the LEFT of IP joint for right hand (after mirror flip)
    thumb_up  = lm[4].x < lm[3].x   # after flip: extended = tip further from palm
    index_up  = lm[8].y  < lm[6].y
    middle_up = lm[12].y < lm[10].y
    ring_up   = lm[16].y < lm[14].y
    pinky_up  = lm[20].y < lm[18].y

    is_sling  = index_up and middle_up and not ring_up and not pinky_up
    is_open   = index_up and middle_up and ring_up and pinky_up
    is_fist   = not index_up and not middle_up and not ring_up and not pinky_up
    is_point  = index_up and not middle_up and not ring_up and not pinky_up  # index only
    # Shield: thumb up, all others curled (like a "thumbs up but sideways")
    is_shield = thumb_up and not index_up and not middle_up and not ring_up and not pinky_up
    # Time stone: index + pinky up (horns gesture \m/)
    is_horns  = index_up and pinky_up and not middle_up and not ring_up
    pinch_d   = math.hypot(lm[4].x-lm[8].x,lm[4].y-lm[8].y)
    wrist_y   = lm[0].y

    return {
        'sling'  : is_sling,
        'open'   : is_open,
        'fist'   : is_fist,
        'point'  : is_point,
        'shield' : is_shield,
        'horns'  : is_horns,
        'pinched': pinch_d<0.055,
        'idx_tip': (int(lm[8].x*w),int(lm[8].y*h)),
        'palm'   : (int(lm[9].x*w),int(lm[9].y*h)),
        'wrist_y': wrist_y,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 14.  SPELLBOOK HUD  (rebuilt — wider, legible, colour-coded rows)
# ══════════════════════════════════════════════════════════════════════════════
SPELL_DEFS=[
    # (name, gesture-glyph, row-colour)
    ("SLING RING",       "II__",  C_GOLD),
    ("TAO MANDALA",      "IIIII", C_BLUE_COLD),
    ("TIME STONE",       "I___I", C_GREEN_STONE),
    ("WAND WATOOMB",     "I____", (100,180,255)),
    ("SHIELD SERAPHIM",  "T____", C_BLUE_BRIGHT),
    ("CRIMSON BANDS",    "::+::", C_RED_BRIGHT),
    ("MIRROR DIM.",      "ooooo", C_PURPLE),
    ("WINDS WATOOMB",    "IIIII", C_CYAN),
]

class GrimoireHUD:
    def __init__(self):
        self.energy=0.0; self.power=0.0; self.wave_t=0.0
        self.fps_buf=deque(maxlen=30); self._lt=time.time()
        self.active_name=None

    def render(self,frame,active_spell,is_drawing,rewind_cnt=0):
        h,w=frame.shape[:2]
        self.wave_t+=0.16
        PW=380   # wider panel

        # fps
        now=time.time()
        self.fps_buf.append(1.0/(now-self._lt+1e-9)); self._lt=now
        fps=int(sum(self.fps_buf)/len(self.fps_buf))

        # ── Panel ─────────────────────────────────────────────────────────
        panel=np.full((h,PW,3),C_UI_BG,dtype=np.uint8)
        for y in range(0,h,30): cv2.line(panel,(0,y),(PW,y),(28,12,42),1)
        roi=frame[:,:PW]
        frame[:,:PW]=cv2.addWeighted(roi,0.08,panel,0.92,0)

        # ── Header ────────────────────────────────────────────────────────
        cv2.putText(frame,"CODEX OF CAGLIOSTRO",(14,36),
                    cv2.FONT_HERSHEY_COMPLEX,0.65,(255,240,120),1,cv2.LINE_AA)
        cv2.line(frame,(14,50),(PW-14,50),C_ORANGE_HOT,2)
        cv2.putText(frame,f"FPS {fps}",(PW-70,22),
                    cv2.FONT_HERSHEY_PLAIN,1.0,(70,70,70),1)

        # ── Waveform ──────────────────────────────────────────────────────
        tgt=60 if (active_spell or is_drawing) else 7
        self.energy+=(tgt-self.energy)*0.12
        pts=[]
        for x in range(14,PW-14,3):
            n=random.uniform(0.88,1.12) if active_spell else 1.0
            pts.append([x,76+int(math.sin(x*0.06+self.wave_t)*self.energy*n)])
        cv2.polylines(frame,[np.array(pts)],False,C_GREEN_STONE,2,cv2.LINE_AA)

        # ── Power bar ─────────────────────────────────────────────────────
        tgt_p=1.0 if active_spell else 0.04
        self.power+=(tgt_p-self.power)*0.09
        bx,by,bw_,bh_=14,96,PW-28,10
        cv2.rectangle(frame,(bx,by),(bx+bw_,by+bh_),(40,20,55),-1)
        fill=int(bw_*self.power)
        for i in range(fill):
            frac=i/max(fill,1)
            cv2.line(frame,(bx+i,by),(bx+i,by+bh_),
                     (int(150+105*frac),int(40+160*frac),int(5+250*frac)),1)
        cv2.rectangle(frame,(bx,by),(bx+bw_,by+bh_),C_CYAN,1)

        # ── Rewind indicator ──────────────────────────────────────────────
        if rewind_cnt>0:
            cv2.putText(frame,f"REWINDING -{rewind_cnt:03d}",(14,120),
                        cv2.FONT_HERSHEY_PLAIN,1.1,C_GREEN_STONE,1,cv2.LINE_AA)

        # ── Spell list  ──────────────────────────────────────────────────
        y0=132 if rewind_cnt==0 else 145
        cv2.putText(frame,"  SPELL        GESTURE   STATUS",(8,y0),
                    cv2.FONT_HERSHEY_PLAIN,0.95,(180,180,180),1)
        y0+=6; cv2.line(frame,(8,y0),(PW-8,y0),(55,35,75),1); y0+=4

        mastered=0
        for name,glyph,row_col in SPELL_DEFS:
            y0+=36
            is_on=(active_spell==name) or (name=="SLING RING" and is_drawing)
            if is_on: mastered+=1

            # Active row: solid colour highlight box
            if is_on:
                overlay=frame.copy()
                cv2.rectangle(overlay,(8,y0-24),(PW-8,y0+14),row_col,-1)
                frame[:]=cv2.addWeighted(frame,0.75,overlay,0.25,0)
                cv2.rectangle(frame,(8,y0-24),(PW-8,y0+14),row_col,1)
                name_col = C_WHITE          # white text on coloured bg
                glyph_col= C_WHITE
                tag_col  = C_WHITE
            else:
                # Inactive: bright enough to read against near-black panel
                name_col = (200, 200, 200)  # light grey — clearly visible
                glyph_col= (140, 140, 140)
                tag_col  = (100, 100, 100)
                # Subtle row separator
                cv2.line(frame,(8,y0-24),(PW-8,y0-24),(50,35,65),1)

            cv2.putText(frame,name,(14,y0),cv2.FONT_HERSHEY_DUPLEX,0.58,name_col,1,cv2.LINE_AA)
            cv2.putText(frame,glyph,(230,y0),cv2.FONT_HERSHEY_PLAIN,1.0,glyph_col,1,cv2.LINE_AA)
            status="[ON]" if is_on else "[ ]"
            cv2.putText(frame,status,(PW-52,y0),cv2.FONT_HERSHEY_PLAIN,1.0,tag_col,1)

        # ── Legend ────────────────────────────────────────────────────────
        y0+=20
        cv2.line(frame,(8,y0),(PW-8,y0),(55,35,75),1); y0+=14
        cv2.putText(frame,"GESTURES: I=up _=down T=thumb",(8,y0),
                    cv2.FONT_HERSHEY_PLAIN,0.85,(130,130,130),1)
        y0+=16
        cv2.putText(frame,"::+:: = both hands pinched apart",(8,y0),
                    cv2.FONT_HERSHEY_PLAIN,0.85,(130,130,130),1)

        # ── Bottom ornament ───────────────────────────────────────────────
        ox,oy=PW//2,h-52
        cv2.circle(frame,(ox,oy),32,C_ORANGE_HOT,1,cv2.LINE_AA)
        cv2.ellipse(frame,(ox,oy),(32,10),math.degrees(self.wave_t*0.38),0,360,C_GOLD,1)
        pa=(ox+int(math.cos(self.wave_t*0.5)*32),oy+int(math.sin(self.wave_t*0.5)*32))
        pb=(ox-int(math.cos(self.wave_t*0.5)*32),oy-int(math.sin(self.wave_t*0.5)*32))
        cv2.line(frame,pa,pb,C_ORANGE_HOT,1)


# ══════════════════════════════════════════════════════════════════════════════
# 15.  MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    cap=cv2.VideoCapture(0,cv2.CAP_DSHOW) if sys.platform=='win32' else cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
    W,H=1280,720

    mp_hands=mp.solutions.hands.Hands(
        max_num_hands=2,
        min_detection_confidence=0.75,
        min_tracking_confidence=0.75,
    )

    portals    =[]
    trace      =SlingRingTrace()
    ts         =TimeStone()
    wand       =WandOfWatoomb()
    shield     =ShieldSeraphim()
    winds      =WindsOfWatoomb()
    deb        =Debounce(hold=5)
    hud        =GrimoireHUD()
    global_t   =0.0
    winds_cd   =0   # cooldown so it doesn't spam

    print("\n  ╔══════════════════════════════════════════╗")
    print("  ║   MYSTIC ARTS ENGINE v4.0               ║")
    print("  ║   Sorcerer Supreme Edition              ║")
    print("  ╠══════════════════════════════════════════╣")
    print("  ║  II___  Index+Mid up   → SLING RING     ║")
    print("  ║  IIIII  Open palm      → TAO MANDALA    ║")
    print("  ║  I___I  Horns \\m/      → TIME STONE     ║")
    print("  ║  I____  Point          → WAND WATOOMB   ║")
    print("  ║  T____  Thumbs up      → SHIELD SERAPH  ║")
    print("  ║  ::+::  Both pinch/pull→ CRIMSON BANDS  ║")
    print("  ║  ooooo  Fist           → MIRROR DIM.    ║")
    print("  ║  IIIII  Both open low  → WINDS WATOOMB  ║")
    print("  ║  [ESC]  exit                            ║")
    print("  ╚══════════════════════════════════════════╝\n")

    while cap.isOpened():
        ok,raw=cap.read()
        if not ok: break

        raw=cv2.flip(cv2.resize(raw,(W,H)),1)
        global_t+=0.07

        magic=np.zeros((H,W,3),dtype=np.uint8)
        frame=raw.copy()

        results=mp_hands.process(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
        poses=[]
        if results.multi_hand_landmarks:
            for hl in results.multi_hand_landmarks:
                poses.append(analyze_hand(hl.landmark,W,H))

        active_spell=None
        is_drawing=False
        rewind_cnt=0

        if poses:
            sling_raw=any(p['sling'] for p in poses)
            sling=deb.update('sling',sling_raw)

            # ── SLING RING ────────────────────────────────────────────────
            sling_hand=next((p for p in poses if p['sling']),None)
            if sling and sling_hand:
                is_drawing=True
                hand=sling_hand
                trace.add(*hand['idx_tip'])
                trace.draw(magic)
            else:
                if trace.active:
                    pts=trace.consume()
                    if len(pts)>28:
                        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
                        cx_=int(sum(xs)/len(xs)); cy_=int(sum(ys)/len(ys))
                        rad=int(math.hypot(max(xs)-min(xs),max(ys)-min(ys))/1.7)
                        if rad>45:
                            portals.append(PortalGateway(cx_,cy_,rad))

            # ── TAO MANDALA ───────────────────────────────────────────────
            if deb.update('open', all(p['open'] for p in poses) and not sling):
                active_spell="TAO MANDALA"
                for p in poses:
                    EldritchMandala.draw(magic,p['palm'][0],p['palm'][1],global_t,160)

            # ── TIME STONE (horns \m/) ────────────────────────────────────
            horns_raw=any(p['horns'] for p in poses) and not sling
            horns_hand=next((p for p in poses if p['horns']),None)
            if deb.update('horns',horns_raw) and horns_hand:
                active_spell="TIME STONE"
                rewind_cnt=ts.process(frame,magic,horns_hand['palm'][0],horns_hand['palm'][1],global_t,True)
            else:
                ts.store(raw)
                ts.process(frame,magic,0,0,global_t,False)

            # ── WAND OF WATOOMB (index only) ──────────────────────────────
            point_raw=any(p['point'] for p in poses) and not sling
            point_hand=next((p for p in poses if p['point']),None)
            if deb.update('point',point_raw) and point_hand:
                active_spell="WAND WATOOMB"
                wand.draw(magic,point_hand['idx_tip'][0],point_hand['idx_tip'][1],global_t,W,H)

            # ── SHIELD OF SERAPHIM (thumbs up) ────────────────────────────
            shield_raw=any(p['shield'] for p in poses) and not sling
            if deb.update('shield',shield_raw):
                active_spell="SHIELD SERAPHIM"
                for p in poses:
                    if p['shield']:
                        shield.draw(magic,p['palm'][0],p['palm'][1],global_t)

            # ── MIRROR DIMENSION (fist) ───────────────────────────────────
            fist_raw=any(p['fist'] for p in poses) and not sling
            if deb.update('fist',fist_raw):
                active_spell="MIRROR DIM."
                draw_mirror_dimension(frame,magic,poses,global_t)

            # ── TWO-HAND SPELLS ───────────────────────────────────────────
            if len(poses)==2:
                p1,p2=poses[0],poses[1]
                dist=math.hypot(p1['palm'][0]-p2['palm'][0],p1['palm'][1]-p2['palm'][1])

                # CRIMSON BANDS
                if deb.update('dual_pinch',p1['pinched'] and p2['pinched']) and dist>180:
                    active_spell="CRIMSON BANDS"
                    draw_crimson_bands(magic,p1['palm'],p2['palm'],global_t)

                # WINDS OF WATOOMB — both hands open, wrists are low in frame (pointing out)
                both_open=p1['open'] and p2['open']
                wrists_low=p1['wrist_y']>0.6 and p2['wrist_y']>0.6
                if deb.update('winds',both_open and wrists_low) and winds_cd<=0:
                    active_spell="WINDS WATOOMB"
                    mx=(p1['palm'][0]+p2['palm'][0])//2
                    my=(p1['palm'][1]+p2['palm'][1])//2
                    winds.trigger(mx,my); winds_cd=20

            if winds_cd>0: winds_cd-=1

        else:
            ts.store(raw)
            if trace.active: trace.consume()
            for g in ('sling','open','fist','horns','point','shield','dual_pinch','winds'):
                deb.update(g,False)

        # Always update/draw winds (shockwaves persist after trigger)
        winds.draw(frame,magic,global_t)

        # ── Portals ───────────────────────────────────────────────────────
        portals=[p for p in portals if p.update_and_draw(magic,frame)]

        # ── Bloom ─────────────────────────────────────────────────────────
        magic=apply_bloom(magic)

        # ── Composite ────────────────────────────────────────────────────
        frame=cv2.add(frame,magic)

        # ── HUD ───────────────────────────────────────────────────────────
        hud.render(frame,active_spell,is_drawing,rewind_cnt)

        cv2.imshow("MYSTIC ARTS ENGINE v4.0 — SORCERER SUPREME",frame)
        if cv2.waitKey(1)&0xFF==27: break

    cap.release()
    cv2.destroyAllWindows()


if __name__=="__main__":
    main()