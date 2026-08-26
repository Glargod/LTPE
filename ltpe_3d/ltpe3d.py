"""LTPE v6.0 — 3D voxel reference core.

Same locked formulas as ltpe_core/ltpe.py. Geometry is 6-connected voxels
with 3D Bresenham line-of-sight. Coordinates: (z, y, x), z = elevation.
"""
from __future__ import annotations
import math, random
from dataclasses import dataclass, field
from typing import Optional

ALPHA = 0.25
K = 5
LAMBDA = 0.15
T_PERIOD = 100
SIGMA = 0.40
BETA = 1.4
W1, W2, W3, W4 = 0.40, 0.25, 0.20, 0.15
JUMP_PROBABILITY = 0.35
MAX_SCAN_RANGE = 6

DIRS6 = ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))

def manhattan(a,b):
    return abs(a[0]-b[0])+abs(a[1]-b[1])+abs(a[2]-b[2])

def chebyshev(a,b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]), abs(a[2]-b[2]))

@dataclass
class Grid3D:
    walls: list
    elevation: Optional[list] = None
    hazard: Optional[list] = None
    @property
    def d(self): return len(self.walls)
    @property
    def h(self): return len(self.walls[0]) if self.walls else 0
    @property
    def w(self): return len(self.walls[0][0]) if self.walls and self.walls[0] else 0
    def in_bounds(self,p):
        z,y,x=p
        return 0<=z<self.d and 0<=y<self.h and 0<=x<self.w
    def free(self,p):
        return self.in_bounds(p) and self.walls[p[0]][p[1]][p[2]]==0
    def elev(self,p):
        if self.elevation is None:
            return p[0]/max(1,self.d-1)
        return self.elevation[p[0]][p[1]][p[2]]
    def haz(self,p):
        if self.hazard is None:
            return 0.0
        return self.hazard[p[0]][p[1]][p[2]]
    def neighbors6(self,p):
        z,y,x=p
        out=[]
        for dz,dy,dx in DIRS6:
            q=(z+dz,y+dy,x+dx)
            if self.free(q): out.append(q)
        return out

def bresenham3(a,b):
    z0,y0,x0=a; z1,y1,x1=b
    dz,dy,dx=abs(z1-z0),abs(y1-y0),abs(x1-x0)
    sz=1 if z0<z1 else -1; sy=1 if y0<y1 else -1; sx=1 if x0<x1 else -1
    cells=[]; z,y,x=z0,y0,x0
    if dx>=dy and dx>=dz:
        py=2*dy-dx; pz=2*dz-dx
        for _ in range(dx+1):
            cells.append((z,y,x))
            if (z,y,x)==(z1,y1,x1): break
            if py>=0: y+=sy; py-=2*dx
            if pz>=0: z+=sz; pz-=2*dx
            x+=sx; py+=2*dy; pz+=2*dz
    elif dy>=dx and dy>=dz:
        px=2*dx-dy; pz=2*dz-dy
        for _ in range(dy+1):
            cells.append((z,y,x))
            if (z,y,x)==(z1,y1,x1): break
            if px>=0: x+=sx; px-=2*dy
            if pz>=0: z+=sz; pz-=2*dy
            y+=sy; px+=2*dx; pz+=2*dz
    else:
        px=2*dx-dz; py=2*dy-dz
        for _ in range(dz+1):
            cells.append((z,y,x))
            if (z,y,x)==(z1,y1,x1): break
            if px>=0: x+=sx; px-=2*dz
            if py>=0: y+=sy; py-=2*dz
            z+=sz; px+=2*dx; py+=2*dy
    return cells

def has_los3d(grid,p,h):
    if not grid.free(p) or not grid.free(h): return False
    cells=bresenham3(p,h)
    for c in cells[1:-1]:
        if not grid.free(c): return False
    return True

def line_of_sight_scan3d(grid,p,max_range=MAX_SCAN_RANGE):
    visible={p}; z0,y0,x0=p
    for z in range(max(0,z0-max_range), min(grid.d,z0+max_range+1)):
        for y in range(max(0,y0-max_range), min(grid.h,y0+max_range+1)):
            for x in range(max(0,x0-max_range), min(grid.w,x0+max_range+1)):
                q=(z,y,x)
                if q==p or not grid.free(q): continue
                if chebyshev(p,q)>max_range: continue
                if has_los3d(grid,p,q): visible.add(q)
    return visible

def is_dead_end3d(grid,n,visited,goal):
    if n==goal: return False
    opens=grid.neighbors6(n)
    if not opens: return True
    return all(q in visited for q in opens)

def branch_potential(grid,n,visited,dead):
    raw=sum(1 for q in grid.neighbors6(n) if q not in visited and q not in dead)
    return raw/6.0

def survival_bias_A(grid,n,current):
    return max(0.0, min(1.0, grid.elev(n)-grid.elev(current)+0.5))

def hazard_H(grid,n):
    return max(0.0, min(1.0, grid.haz(n)))

def score_node(grid,n,current,g_hat,visited,dead,rng):
    goal_term=1.0/(manhattan(n,g_hat)+1.0)
    A=survival_bias_A(grid,n,current)
    B=branch_potential(grid,n,visited,dead)
    Hn=hazard_H(grid,n)
    eps=rng.uniform(0.0,SIGMA)
    return W1*goal_term + W2*A + W3*B - W4*Hn + eps

def ritual_nudge(scores_sorted_desc,m,k,lam=LAMBDA):
    out=[]; kk=max(1,k); logm=math.log(1.0+m)
    for i,s in enumerate(scores_sorted_desc):
        factor=1.0-lam*logm*(i/kk)
        out.append(s*max(0.05,factor))
    return out

def weighted_lottery(items,beta,rng):
    weights=[max(1e-9,s)**beta for s,_n in items]
    total=sum(weights); pick=rng.random()*total; acc=0.0
    for w,(_s,n) in zip(weights,items):
        acc+=w
        if pick<=acc: return n
    return items[-1][1]

@dataclass
class Result3D:
    success: bool
    steps: float
    path: list
    ritual_count: int
    reason: str

@dataclass
class LTPE3D:
    grid: Grid3D
    start: tuple
    goal: tuple
    use_ritual: bool=True
    max_steps: int=3000
    seed: Optional[int]=None
    jump_probability: float=JUMP_PROBABILITY
    alpha: float=ALPHA
    k: int=K
    lam: float=LAMBDA
    beta: float=BETA
    rng: random.Random=field(init=False)
    def __post_init__(self):
        self.rng=random.Random(self.seed)
    def run(self)->Result3D:
        current=self.start
        H={current}; S={current}; D=set()
        g_hat=(self.grid.d-2, self.grid.h-2, self.grid.w-2)
        steps=0.0; ritual_count=0; path=[current]; integer_steps=0
        while integer_steps<self.max_steps:
            integer_steps+=1
            H |= line_of_sight_scan3d(self.grid, current)
            hubs=[h for h in H if h!=current and has_los3d(self.grid,current,h)]
            if hubs and self.rng.random()<self.jump_probability:
                h=min(hubs, key=lambda q: manhattan(q,g_hat))
                cost=self.alpha*manhattan(current,h)
                current=h; steps+=cost; S.add(current); path.append(current)
                if current==self.goal:
                    return Result3D(True,steps,path,ritual_count,"goal")
            for n in self.grid.neighbors6(current):
                if is_dead_end3d(self.grid,n,S,self.goal): D.add(n)
            candidates=[]
            for n in self.grid.neighbors6(current):
                if n in D: continue
                candidates.append((score_node(self.grid,n,current,g_hat,S,D,self.rng), n))
            if not candidates:
                back=[q for q in self.grid.neighbors6(current) if q in S]
                if not back:
                    return Result3D(False,steps,path,ritual_count,"trapped")
                current=back[self.rng.randrange(len(back))]; steps+=1.0; path.append(current)
                continue
            candidates.sort(key=lambda t:t[0], reverse=True)
            top_k=candidates[:min(self.k,len(candidates))]
            if self.use_ritual and (integer_steps%T_PERIOD==0 or len(top_k)>=4):
                if len(top_k)>=4:
                    ritual_count+=1
                    nudged=ritual_nudge([s for s,_ in top_k], ritual_count, len(top_k), self.lam)
                    top_k=[(nudged[i], top_k[i][1]) for i in range(len(top_k))]
            chosen=weighted_lottery(top_k,self.beta,self.rng)
            if manhattan(chosen,self.goal)<manhattan(g_hat,self.goal):
                g_hat=chosen
            current=chosen; steps+=1.0; S.add(current); path.append(current)
            if current==self.goal:
                return Result3D(True,steps,path,ritual_count,"goal")
        return Result3D(False,steps,path,ritual_count,"max_steps")

def make_cave3d(w=21,h=17,d=9,seed=0,wall_p=0.32):
    rng=random.Random(seed)
    walls=[[[1 if rng.random()<wall_p else 0 for _ in range(w)] for _ in range(h)] for _ in range(d)]
    for z in range(d):
        for y in range(h):
            walls[z][y][0]=walls[z][y][w-1]=1
        for x in range(w):
            walls[z][0][x]=walls[z][h-1][x]=1
    for y in range(h):
        for x in range(w):
            walls[0][y][x]=walls[d-1][y][x]=1
    start=(1,1,1); goal=(d-2,h-2,w-2)
    z,y,x=start; walls[z][y][x]=0
    while (z,y,x)!=goal:
        r=rng.random()
        if r<0.34 and x<goal[2]: x+=1
        elif r<0.62 and y<goal[1]: y+=1
        elif r<0.80 and z<goal[0]: z+=1
        elif r<0.88 and x>1: x-=1
        elif r<0.94 and y>1: y-=1
        elif z>1: z-=1
        else: x=min(w-2,x+1)
        walls[z][y][x]=0
    walls[goal[0]][goal[1]][goal[2]]=0
    walls[start[0]][start[1]][start[2]]=0
    elevation=[[[zz/max(1,d-1) for _x in range(w)] for _y in range(h)] for zz in range(d)]
    hazard=[[[0.18 if walls[zz][yy][xx]==0 and rng.random()<0.07 else 0.0 for xx in range(w)] for yy in range(h)] for zz in range(d)]
    return Grid3D(walls,elevation,hazard), start, goal
