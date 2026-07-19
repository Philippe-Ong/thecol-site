#!/usr/bin/env python3
"""Build the dependency-free Swiss canton map used by the sales-points page."""
from __future__ import annotations

import json
import math
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

SOURCE_URL = "https://upload.wikimedia.org/wikipedia/commons/f/f8/Suisse_cantons.svg"
CANTONS = ("ZH", "BE", "LU", "UR", "SZ", "OW", "NW", "GL", "ZG", "FR", "SO", "BS", "BL", "SH", "AR", "AI", "SG", "GR", "AG", "TG", "TI", "VD", "VS", "NE", "GE", "JU")
LOCATIONS = (
    ("Fribourg", 46.806, 7.162, "FR"), ("Marly", 46.777, 7.160, "FR"),
    ("Treyvaux", 46.727, 7.139, "FR"), ("Prez-vers-Noréaz", 46.788, 7.019, "FR"),
    ("Courtepin", 46.866, 7.122, "FR"), ("Praz (Vully)", 46.956, 7.099, "FR"),
    ("Domdidier", 46.868, 7.014, "FR"), ("Châtel-Saint-Denis", 46.524, 6.903, "FR"),
    ("Romont", 46.694, 6.917, "FR"), ("Rossens", 46.720, 7.106, "FR"),
    ("Ponthaux", 46.816, 7.043, "FR"), ("Villaz-St-Pierre", 46.721, 6.958, "FR"),
    ("Rueyres-St-Laurent", 46.718, 7.034, "FR"), ("Ependes", 46.756, 7.144, "FR"),
    ("Neyruz", 46.766, 7.063, "FR"), ("Givisiez", 46.812, 7.124, "FR"),
    ("Charmey", 46.619, 7.164, "FR"), ("Belfaux", 46.821, 7.106, "FR"),
    ("La Joux", 46.624, 6.998, "FR"), ("Lossy", 46.834, 7.114, "FR"),
    ("Arconciel", 46.744, 7.121, "FR"), ("Posieux", 46.769, 7.106, "FR"),
    ("Cugy", 46.815, 6.892, "FR"), ("Yverdon-les-Bains", 46.779, 6.641, "VD"),
    ("Crissier", 46.551, 6.576, "VD"), ("Champoussin", 46.209, 6.865, "VS"),
    ("Delémont", 47.365, 7.344, "JU"),
)
TOKEN_RE = re.compile(r"[AaCcHhLlMmQqSsTtVvZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
PARAMS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}


def multiply(a, b):
    return (a[0]*b[0]+a[2]*b[1], a[1]*b[0]+a[3]*b[1],
            a[0]*b[2]+a[2]*b[3], a[1]*b[2]+a[3]*b[3],
            a[0]*b[4]+a[2]*b[5]+a[4], a[1]*b[4]+a[3]*b[5]+a[5])


def parse_transform(text):
    result = (1, 0, 0, 1, 0, 0)
    for name, raw in re.findall(r"([A-Za-z]+)\s*\(([^)]*)\)", text or ""):
        v = [float(x) for x in re.findall(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?", raw)]
        if name == "matrix": t = tuple(v)
        elif name == "translate": t = (1, 0, 0, 1, v[0], v[1] if len(v)>1 else 0)
        elif name == "scale": t = (v[0], 0, 0, v[1] if len(v)>1 else v[0], 0, 0)
        elif name == "rotate":
            r=math.radians(v[0]); c=math.cos(r); s=math.sin(r); t=(c,s,-s,c,0,0)
            if len(v)>2: t=multiply(multiply((1,0,0,1,v[1],v[2]),t),(1,0,0,1,-v[1],-v[2]))
        elif name == "skewX": t=(1,0,math.tan(math.radians(v[0])),1,0,0)
        elif name == "skewY": t=(1,math.tan(math.radians(v[0])),0,1,0,0)
        else: continue
        result = multiply(result, t)
    return result


def apply(m, p): return (m[0]*p[0]+m[2]*p[1]+m[4], m[1]*p[0]+m[3]*p[1]+m[5])
def lerp(a, b, t): return a+(b-a)*t


def flatten_path(d, matrix, curve_steps=5):
    """Convert SVG commands to absolute polylines; curves are sampled before RDP."""
    tok=TOKEN_RE.findall(d); i=0; cmd=None; cur=(0.,0.); start=cur; prev_ctrl=None; rings=[]; ring=[]
    def point(x,y,rel): return (cur[0]+x,cur[1]+y) if rel else (x,y)
    def add(p):
        nonlocal cur
        cur=p; ring.append(apply(matrix,p))
    while i<len(tok):
        if tok[i].isalpha(): cmd=tok[i]; i+=1
        if cmd is None: raise ValueError("Path data starts without command")
        up=cmd.upper(); rel=cmd.islower()
        if up=="Z":
            if ring:
                if ring[-1]!=ring[0]: ring.append(ring[0])
                rings.append(ring); ring=[]
            cur=start; prev_ctrl=None; cmd=None; continue
        n=PARAMS[up]
        if i+n>len(tok): raise ValueError(f"Incomplete {cmd}")
        v=list(map(float,tok[i:i+n])); i+=n; old=cur
        if up=="M":
            p=point(v[0],v[1],rel)
            if ring: rings.append(ring); ring=[]
            add(p); start=p; cmd="l" if rel else "L"; prev_ctrl=None
        elif up=="L": add(point(v[0],v[1],rel)); prev_ctrl=None
        elif up=="H": add((cur[0]+v[0],cur[1]) if rel else (v[0],cur[1])); prev_ctrl=None
        elif up=="V": add((cur[0],cur[1]+v[0]) if rel else (cur[0],v[0])); prev_ctrl=None
        elif up in ("C","S"):
            if up=="C": c1=point(v[0],v[1],rel); c2=point(v[2],v[3],rel); end=point(v[4],v[5],rel)
            else:
                c1=(2*old[0]-prev_ctrl[0],2*old[1]-prev_ctrl[1]) if prev_ctrl else old
                c2=point(v[0],v[1],rel); end=point(v[2],v[3],rel)
            for k in range(1,curve_steps+1):
                t=k/curve_steps; u=1-t
                add((u**3*old[0]+3*u*u*t*c1[0]+3*u*t*t*c2[0]+t**3*end[0],u**3*old[1]+3*u*u*t*c1[1]+3*u*t*t*c2[1]+t**3*end[1]))
            prev_ctrl=c2
        elif up in ("Q","T"):
            if up=="Q": c=point(v[0],v[1],rel); end=point(v[2],v[3],rel)
            else: c=(2*old[0]-prev_ctrl[0],2*old[1]-prev_ctrl[1]) if prev_ctrl else old; end=point(v[0],v[1],rel)
            for k in range(1,curve_steps+1):
                t=k/curve_steps; u=1-t; add((u*u*old[0]+2*u*t*c[0]+t*t*end[0],u*u*old[1]+2*u*t*c[1]+t*t*end[1]))
            prev_ctrl=c
        elif up=="A":
            # Canton source does not use arcs; linear fallback still guarantees valid output.
            add(point(v[5],v[6],rel)); prev_ctrl=None
    if ring: rings.append(ring)
    return [r for r in rings if len(r)>=3]


def dist_line(p,a,b):
    dx=b[0]-a[0]; dy=b[1]-a[1]
    if dx==dy==0: return math.dist(p,a)
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)))
    return math.dist(p,(a[0]+t*dx,a[1]+t*dy))


def rdp(points, eps):
    closed=points[0]==points[-1]; p=points[:-1] if closed else points
    if len(p)<4: return points
    # Split a closed polygon at a point far from the first to avoid a degenerate chord.
    if closed:
        j=max(range(1,len(p)),key=lambda i: math.dist(p[0],p[i])); p=p[j:]+p[:j+1]
    def rec(q):
        if len(q)<=2:return q
        ds=[dist_line(q[k],q[0],q[-1]) for k in range(1,len(q)-1)]; m=max(ds,default=0); j=ds.index(m)+1 if ds else 0
        return rec(q[:j+1])[:-1]+rec(q[j:]) if m>eps else [q[0],q[-1]]
    out=rec(p)
    if closed and out[-1]!=out[0]: out.append(out[0])
    return out


def inside(point, rings):
    x,y=point; hit=False
    for poly in rings:
        j=len(poly)-1
        for i in range(len(poly)):
            xi,yi=poly[i]; xj,yj=poly[j]
            if (yi>y)!=(yj>y) and x < (xj-xi)*(y-yi)/(yj-yi)+xi: hit=not hit
            j=i
    return hit


def nearest_inside(p,rings,max_r=180):
    if inside(p,rings): return p,0.0
    for r in range(1,max_r+1):
        for k in range(max(16,int(2*math.pi*r/2))):
            a=2*math.pi*k/max(16,int(2*math.pi*r/2)); q=(p[0]+r*math.cos(a),p[1]+r*math.sin(a))
            if inside(q,rings): return q,float(r)
    raise RuntimeError(f"No interior point near {p}")


def bbox_of(rings):
    xs=[x for ring in rings for x,y in ring]; ys=[y for ring in rings for x,y in ring]
    return min(xs), min(ys), max(xs), max(ys)


def point_segment_distance(p, a, b):
    """Distance euclidienne entre p et le segment [a,b]."""
    dx=b[0]-a[0]; dy=b[1]-a[1]
    if dx==dy==0: return math.dist(p,a)
    t=max(0.0,min(1.0,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)))
    return math.dist(p,(a[0]+t*dx, a[1]+t*dy))


def distance_to_polygon_border(p, rings):
    """Distance minimum entre p et n'importe quel côté de n'importe quel anneau."""
    best=math.inf
    for ring in rings:
        n=len(ring)-1 if ring[0]==ring[-1] else len(ring)
        for i in range(n):
            d=point_segment_distance(p, ring[i], ring[(i+1)%n])
            if d<best: best=d
    return best


def best_label_point(rings, obstacles, step=2.0, margin=8.0):
    """Pole-of-inaccessibility approché.

    Pour chaque canton, échantillonne une grille de candidats dans la bbox
    (avec marge), rejette ceux hors polygone, puis garde le candidat qui
    maximise min(distance aux obstacles, distance au bord du polygone).
    `obstacles` est une liste de points (x,y) ; si vide, on retombe sur
    la distance au bord uniquement (cas GE/NE sans pins).
    """
    minx, miny, maxx, maxy = bbox_of(rings)
    minx+=margin; miny+=margin; maxx-=margin; maxy-=margin
    if minx>=maxx or miny>=maxy:
        raise RuntimeError("bbox trop petite pour placer un label")
    best=(None, -1.0)
    y=miny
    while y<=maxy:
        x=minx
        while x<=maxx:
            p=(x,y)
            if inside(p, rings):
                d_border=distance_to_polygon_border(p, rings)
                d_obs=min((math.dist(p, o) for o in obstacles), default=math.inf)
                score=min(d_border, d_obs)
                if score>best[1]:
                    best=(p, score)
            x+=step
        y+=step
    if best[0] is None:
        # Fallback: centroïde approximatif (centroïde du bbox)
        cx=(minx+maxx)/2; cy=(miny+maxy)/2
        # Clamp au polygone (utilise le 1er point intérieur trouvé par scan radial)
        cx, _ = nearest_inside((cx, cy), rings)
        best=((cx, cy), 0.0)
    return best[0]


def fmt(v):
    v=round(v,1)
    if v==0: v=0
    return f"{v:.1f}".rstrip("0").rstrip(".")


def path_string(rings):
    return "".join("M"+" ".join((fmt(x)+","+fmt(y)) for x,y in r[:-1])+"Z" for r in rings)


def download(path):
    req=urllib.request.Request(SOURCE_URL,headers={"User-Agent":"SiteThecol-map-build/1.0 (contact: dev)"})
    with urllib.request.urlopen(req) as src, path.open("wb") as out: out.write(src.read())


def main():
    root_dir=Path(__file__).resolve().parents[1]; tmp=Path.home()/"AppData/Local/Temp/opencode"; tmp.mkdir(parents=True,exist_ok=True)
    svg=Path(sys.argv[1]) if len(sys.argv)>1 else tmp/"Suisse_cantons.svg"
    if not svg.exists(): download(svg)
    root=ET.parse(svg).getroot(); parent={c:p for p in root.iter() for c in p}
    nodes={e.get("id"):e for e in root.iter() if e.tag.rsplit("}",1)[-1]=="path" and e.get("id") in CANTONS}
    print("IDs canton trouvés:", " ".join(nodes))
    missing=set(CANTONS)-set(nodes)
    if missing: raise RuntimeError(f"Cantons manquants: {sorted(missing)}")
    raw={}
    for code,node in nodes.items():
        chain=[]; n=node
        while n is not None: chain.append(n); n=parent.get(n)
        matrix=(1,0,0,1,0,0)
        for elem in reversed(chain): matrix=multiply(matrix,parse_transform(elem.get("transform")))
        raw[code]=flatten_path(node.get("d"),matrix)
    pts=[p for rings in raw.values() for ring in rings for p in ring]
    minx=min(x for x,y in pts); maxx=max(x for x,y in pts); miny=min(y for x,y in pts); maxy=max(y for x,y in pts)
    margin=12.0
    usable_width=1000-2*margin; usable_height=700-2*margin
    scale=min(usable_width/(maxx-minx),usable_height/(maxy-miny))
    tx=(1000-(maxx-minx)*scale)/2-minx*scale
    ty=(700-(maxy-miny)*scale)/2-miny*scale
    scaled={c:[[(x*scale+tx,y*scale+ty) for x,y in ring] for ring in rings] for c,rings in raw.items()}
    simplified={c:[rdp(r,0.8) for r in rings] for c,rings in scaled.items()}
    allpts=[p for rings in scaled.values() for ring in rings for p in ring]
    bx=(min(x for x,y in allpts),max(x for x,y in allpts)); by=(min(y for x,y in allpts),max(y for x,y in allpts))
    finalpts=[p for rings in simplified.values() for ring in rings for p in ring]
    final_bbox=(min(x for x,y in finalpts),max(x for x,y in finalpts),min(y for x,y in finalpts),max(y for x,y in finalpts))
    print(f"BBox source: {minx:.3f},{miny:.3f} – {maxx:.3f},{maxy:.3f}; scale={scale:.6f}")
    print(f"BBox transformée: x={final_bbox[0]:.3f}..{final_bbox[1]:.3f}, y={final_bbox[2]:.3f}..{final_bbox[3]:.3f}")
    if final_bbox[0] < margin-0.001 or final_bbox[1] > 1000-margin+0.001 or final_bbox[2] < margin-0.001 or final_bbox[3] > 700-margin+0.001:
        raise AssertionError(f"BBox hors marge: {final_bbox}")
    for c in CANTONS: print(f"POINTS {c}: {sum(len(r) for r in scaled[c])} -> {sum(len(r) for r in simplified[c])}")
    projected={}; placed={}; adjustments=[]
    for name,lat,lon,code in LOCATIONS:
        p=(lerp(bx[0],bx[1],(lon-5.956)/(10.492-5.956)),lerp(by[1],by[0],(lat-45.818)/(47.808-45.818)))
        projected[name]=p
        if not inside(p,simplified[code]):
            raise AssertionError(f"Projection réelle de {name} hors {code}: {p}")
        placed[name]=(p,code)

    # Anti-chevauchement doux : conserve les projections réelles sauf quand une
    # distance inférieure à 10 unités l'impose. Pour chaque conflit, cherche le
    # déplacement minimal dans une spirale courte, sans jamais dépasser 7 unités.
    min_distance=10.0; max_offset=7.0
    names=[name for name,_,_,_ in LOCATIONS]
    # Résolution globale déterministe par relaxation : chaque paire trop proche
    # exerce une répulsion symétrique, suivie d'un clamp à 7 unités de la vraie
    # projection. Les pins non concernés restent strictement à leur projection.
    active={name for i,a in enumerate(names) for b in names[i+1:] if math.dist(projected[a],projected[b]) < min_distance for name in (a,b)}
    for _ in range(2000):
        forces={name:[0.0,0.0] for name in active}; conflicts=0
        for i,a in enumerate(names):
            for b in names[i+1:]:
                pa=placed[a][0]; pb=placed[b][0]; d=math.dist(pa,pb)
                if d >= min_distance-1e-4: continue
                conflicts+=1
                if d<1e-9: ux,uy=1.0,0.0
                else: ux=(pb[0]-pa[0])/d; uy=(pb[1]-pa[1])/d
                push=(min_distance-d)/2+0.01
                if a in active: forces[a][0]-=ux*push; forces[a][1]-=uy*push
                if b in active: forces[b][0]+=ux*push; forces[b][1]+=uy*push
        if not conflicts: break
        changed=False
        for name,(fx,fy) in forces.items():
            p,code=placed[name]; q=(p[0]+fx,p[1]+fy); origin=projected[name]
            delta=math.dist(q,origin)
            if delta>max_offset:
                q=(origin[0]+(q[0]-origin[0])*max_offset/delta,origin[1]+(q[1]-origin[1])*max_offset/delta)
            if inside(q,simplified[code]): placed[name]=(q,code); changed=True
        if not changed: raise RuntimeError("Relaxation anti-chevauchement bloquée")
    else: raise RuntimeError("Anti-chevauchement doux non convergent")

    offsets={}
    for name,_,_,code in LOCATIONS:
        p=placed[name][0]; delta=math.dist(p,projected[name]); offsets[name]=delta
        if not inside(p,simplified[code]): raise AssertionError(f"{name} hors {code}")
        if delta > max_offset+1e-6: raise AssertionError(f"Écart excessif pour {name}: {delta:.3f}")
        if delta > 0.05: adjustments.append((name,"chevauchement",delta))
        print(f"ÉCART {name} [{code}]: {delta:.3f} unité ({delta*0.37:.3f} km), final=({p[0]:.1f},{p[1]:.1f})")

    minimum=(999,None,None)
    for i,a in enumerate(names):
        for b in names[i+1:]:
            d=math.dist(placed[a][0],placed[b][0])
            if d<minimum[0]: minimum=(d,a,b)
    if minimum[0] < min_distance-1e-6: raise AssertionError(f"Distance insuffisante: {minimum}")
    print(f"DISTANCE MIN: {minimum[1]} / {minimum[2]} = {minimum[0]:.2f}")
    print("AJUSTEMENTS:", ", ".join(f"{n} ({delta:.3f})" for n,_,delta in adjustments) or "aucun")
    canton_json=",\n".join(f'    {json.dumps(c)}: {json.dumps(path_string(simplified[c]))}' for c in CANTONS)
    loc_json=",\n".join(f'    {json.dumps(n,ensure_ascii=False)}: [{fmt(placed[n][0][0])}, {fmt(placed[n][0][1])}]' for n,_,_,_ in LOCATIONS)

    # Calcule les positions optimales des labels pour FR, VD, VS, JU, GE, NE :
    # on maximise min(distance au pin le plus proche, distance au bord du polygone).
    # Pour GE/NE qui n'ont pas de pins dans POS, on maximise uniquement la distance au bord.
    label_cantons=("FR","VD","VS","JU","GE","NE")
    labels={}
    for code in label_cantons:
        obstacles=[]
        for name,_,_,oc in LOCATIONS:
            if oc==code and name in placed:
                obstacles.append(placed[name][0])
        pt=best_label_point(simplified[code], obstacles, step=2.0, margin=10.0)
        d_obs=min((math.dist(pt, o) for o in obstacles), default=math.inf) if obstacles else None
        d_border=distance_to_polygon_border(pt, simplified[code])
        print(f"LABEL {code}: ({pt[0]:.1f},{pt[1]:.1f}) d_pin={('-inf' if d_obs is None else f'{d_obs:.1f}')} d_border={d_border:.1f}")
        labels[code]=(round(pt[0],1), round(pt[1],1))
    label_json=",\n".join(f'    {json.dumps(c)}: [{fmt(labels[c][0])}, {fmt(labels[c][1])}]' for c in label_cantons)

    fr_points=[placed[name][0] for name,_,_,code in LOCATIONS if code=="FR"]
    zoom_minx=max(12.0,min(x for x,y in fr_points)-22.0)
    zoom_maxx=min(988.0,max(x for x,y in fr_points)+22.0)
    zoom_miny=max(38.0,min(y for x,y in fr_points)-22.0)
    zoom_maxy=min(662.0,max(y for x,y in fr_points)+22.0)
    zoom_viewbox=f"{fmt(zoom_minx)} {fmt(zoom_miny)} {fmt(zoom_maxx-zoom_minx)} {fmt(zoom_maxy-zoom_miny)}"
    print(f"ZOOM FR: {zoom_viewbox}")

    content='/* Carte simplifiée de la Suisse — adapté de « Suisse cantons.svg » par Pymouss44, Wikimedia Commons, CC BY-SA 4.0 (https://commons.wikimedia.org/wiki/File:Suisse_cantons.svg) */\nwindow.THECOL_GEO = {\n  viewBox: "0 0 1000 700",\n  cantons: {\n'+canton_json+'\n  },\n  labels: {\n'+label_json+'\n  },\n  loc: {\n'+loc_json+'\n  },\n  zoom: { viewBox: '+json.dumps(zoom_viewbox)+' }\n};\n'
    out=root_dir/"js/map-suisse.js"; out.write_text(content,encoding="utf-8")
    # Re-parse exactly the rounded path representation written to JavaScript.
    written=[]
    for code in CANTONS:
        values=[float(v) for v in re.findall(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?",path_string(simplified[code]))]
        written.extend(zip(values[::2],values[1::2]))
    written_bbox=(min(x for x,y in written),max(x for x,y in written),min(y for x,y in written),max(y for x,y in written))
    if not (0 <= written_bbox[0] <= written_bbox[1] <= 1000 and 0 <= written_bbox[2] <= written_bbox[3] <= 700):
        raise AssertionError(f"BBox JS hors viewBox: {written_bbox}")
    print(f"BBox JS arrondie: x={written_bbox[0]:.1f}..{written_bbox[1]:.1f}, y={written_bbox[2]:.1f}..{written_bbox[3]:.1f}")
    print(f"Écrit: {out} ({out.stat().st_size} octets)")

if __name__=="__main__": main()
