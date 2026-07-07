"""Render de la red como grafo D3 force-directed en canvas, embebido en
Streamlit. Portado de 5. Taller/taller-redes RedRealCanvas.tsx:

- fuerza dirigida (link/charge/center/collide) con las mismas constantes,
- aristas dirigidas vendedor→comprador con punta de flecha en el comprador,
- rampa de calor por COMPRAS (azul claro → rojo = acumula tierra),
- hover con resaltado de vecinos + etiqueta, zoom/pan, botón centrar.

Los datos se preparan en Python (una sola fuente de verdad: la red curada) y
se inyectan como JSON; d3 se carga por CDN dentro del iframe del componente.
"""
from __future__ import annotations

import json
import math

import networkx as nx
import streamlit.components.v1 as components

from lib.red import bonito

# Rampa de calor por compras (idéntica a RedRealExplorer.tsx)
_RAMPA = [(186, 220, 250), (96, 165, 250), (245, 158, 11), (194, 30, 30)]


def _color_por_grado(g: int, gmax: int) -> str:
    t = min(1.0, math.sqrt(g / gmax)) if gmax > 0 else 0.0
    x = t * (len(_RAMPA) - 1)
    i = min(len(_RAMPA) - 2, int(math.floor(x)))
    f = x - i
    a, b = _RAMPA[i], _RAMPA[i + 1]
    return "rgb(%d,%d,%d)" % (
        round(a[0] + (b[0] - a[0]) * f),
        round(a[1] + (b[1] - a[1]) * f),
        round(a[2] + (b[2] - a[2]) * f),
    )


def datos_canvas(res: dict, filtro: str = "conectados"):
    """res -> (nodos, aristas) listos para el canvas.
    filtro: 'todos' | 'conectados' (comp>=3) | 'nucleos' (comp>=4)."""
    G: nx.DiGraph = res["G"]
    tabla = res["tabla"].set_index("actor")
    comp: dict[str, int] = {}
    for c in nx.connected_components(G.to_undirected()):
        for n in c:
            comp[n] = len(c)

    if filtro == "conectados":
        visibles = {n for n in G if comp.get(n, 1) >= 3}
    elif filtro == "nucleos":
        visibles = {n for n in G if comp.get(n, 1) >= 4}
    else:
        visibles = set(G.nodes())

    compras = {n: int(tabla.at[n, "compras"]) if n in tabla.index else 0
               for n in visibles}
    ventas = {n: int(tabla.at[n, "ventas"]) if n in tabla.index else 0
              for n in visibles}
    gmax = max(list(compras.values()) or [1]) or 1

    nodos = [{
        "id": n,
        "label": bonito(n),
        "c": compras[n],
        "v": ventas[n],
        "size": 12 + compras[n] * 3,
        "color": _color_por_grado(compras[n], gmax),
    } for n in visibles]
    aristas = [{"source": u, "target": v} for u, v in G.edges()
               if u in visibles and v in visibles]
    return nodos, aristas, len(visibles), G.number_of_nodes()


def _html(nodos, aristas, height: int) -> str:
    datos = json.dumps({"nodos": nodos, "aristas": aristas})
    return _PLANTILLA.replace("__DATOS__", datos).replace("__H__", str(height))


def red_canvas(res: dict, filtro: str = "conectados", height: int = 560):
    nodos, aristas, nvis, ntot = datos_canvas(res, filtro)
    components.html(_html(nodos, aristas, height), height=height + 4,
                    scrolling=False)
    return nvis, ntot


_PLANTILLA = r"""
<!doctype html><html><head><meta charset="utf-8">
<style>
  html,body{margin:0;padding:0;font-family:ui-sans-serif,system-ui,sans-serif;}
  #wrap{position:relative;width:100%;height:__H__px;border:1px solid #e2e8f0;
        border-radius:10px;overflow:hidden;background:#fff;}
  canvas{display:block;cursor:grab;}
  canvas:active{cursor:grabbing;}
  .btn{position:absolute;right:10px;top:10px;z-index:5;background:rgba(255,255,255,.92);
       border:1px solid #e2e8f0;border-radius:7px;padding:5px 9px;font-size:12px;
       color:#475569;cursor:pointer;box-shadow:0 1px 2px rgba(0,0,0,.06);}
  .btn:hover{background:#fff;}
  .leg{position:absolute;left:10px;bottom:10px;z-index:5;background:rgba(255,255,255,.92);
       border:1px solid #e2e8f0;border-radius:7px;padding:7px 10px;font-size:11px;
       color:#475569;box-shadow:0 1px 2px rgba(0,0,0,.06);}
  .leg .dots{display:flex;align-items:center;gap:5px;margin-bottom:3px;}
  .dot{display:inline-block;border-radius:50%;}
  .sub{color:#94a3b8;}
</style></head><body>
<div id="wrap">
  <button class="btn" id="centrar">⤢ Centrar</button>
  <div class="leg">
    <div class="dots">
      <span class="dot" style="width:8px;height:8px;background:rgb(186,220,250)"></span>
      <span class="dot" style="width:13px;height:13px;background:rgb(245,158,11)"></span>
      <span class="dot" style="width:18px;height:18px;background:rgb(194,30,30)"></span>
      <span style="margin-left:4px">compras: pocas → muchas (acumula tierra)</span>
    </div>
    <div class="sub">cada círculo = un actor · la flecha va del vendedor al comprador</div>
  </div>
  <canvas id="cv"></canvas>
</div>
<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
<script>
const DATA = __DATOS__;
const wrap = document.getElementById('wrap');
const canvas = document.getElementById('cv');
const ctx = canvas.getContext('2d');
let W = wrap.clientWidth, H = wrap.clientHeight, DPR = Math.min(2, window.devicePixelRatio||1);
let transform = d3.zoomIdentity, hov = null, neigh = new Set(), fitDone = false;

const nodes = DATA.nodos.map(n => ({...n, x: W/2 + (Math.random()-.5)*260, y: H/2 + (Math.random()-.5)*260}));
const links = DATA.aristas.map(a => ({source:a.source, target:a.target}));
const adj = new Map();
for (const a of DATA.aristas){
  if(!adj.has(a.source)) adj.set(a.source,new Set());
  if(!adj.has(a.target)) adj.set(a.target,new Set());
  adj.get(a.source).add(a.target); adj.get(a.target).add(a.source);
}

function resize(){
  DPR = Math.min(2, window.devicePixelRatio||1);
  W = wrap.clientWidth; H = wrap.clientHeight;
  canvas.width = W*DPR; canvas.height = H*DPR;
  canvas.style.width = W+'px'; canvas.style.height = H+'px';
  sim.force('x').x(W/2); sim.force('y').y(H/2);
  draw();
}

function roundRect(x,y,w,h,r){ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);
  ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath();}

function draw(){
  const t = transform;
  ctx.save();
  ctx.clearRect(0,0,W*DPR,H*DPR);
  ctx.scale(DPR,DPR); ctx.translate(t.x,t.y); ctx.scale(t.k,t.k);
  // aristas dirigidas con flecha en el comprador
  for(const l of links){
    const s=l.source, g=l.target;
    if(s.x==null||g.x==null) continue;
    const inc = hov ? (s.id===hov||g.id===hov) : false;
    const color = hov ? (inc ? '#0d9488' : '#eef2f6') : '#b8c2cf';
    ctx.beginPath(); ctx.moveTo(s.x,s.y); ctx.lineTo(g.x,g.y);
    ctx.strokeStyle=color; ctx.lineWidth=(inc?2.2:0.9)/t.k; ctx.stroke();
    const dx=g.x-s.x, dy=g.y-s.y, len=Math.hypot(dx,dy)||1, ux=dx/len, uy=dy/len;
    const tipX=g.x-ux*(g.size/2+0.5), tipY=g.y-uy*(g.size/2+0.5);
    const ah=7/t.k, ang=Math.atan2(dy,dx);
    ctx.beginPath(); ctx.moveTo(tipX,tipY);
    ctx.lineTo(tipX-ah*Math.cos(ang-0.42),tipY-ah*Math.sin(ang-0.42));
    ctx.lineTo(tipX-ah*Math.cos(ang+0.42),tipY-ah*Math.sin(ang+0.42));
    ctx.closePath(); ctx.fillStyle=color; ctx.fill();
  }
  // nodos
  for(const n of nodes){
    if(n.x==null) continue;
    const dim = hov && n.id!==hov && !neigh.has(n.id);
    ctx.globalAlpha = dim ? 0.2 : 1;
    ctx.beginPath(); ctx.arc(n.x,n.y,n.size/2,0,2*Math.PI);
    ctx.fillStyle=n.color; ctx.fill();
    ctx.lineWidth=(n.id===hov?2:1)/t.k;
    ctx.strokeStyle = n.id===hov ? '#1e3a8a' : 'rgba(15,23,42,0.35)';
    ctx.stroke();
  }
  ctx.globalAlpha=1; ctx.restore();
  // etiqueta bajo el cursor (coords de pantalla)
  if(hov){
    const n = nodes.find(x=>x.id===hov);
    if(n && n.x!=null){
      const sx=t.x+n.x*t.k, sy=t.y+n.y*t.k;
      const texto = n.label + '  ·  ' + n.c + ' compras · ' + n.v + ' ventas';
      ctx.save(); ctx.scale(DPR,DPR);
      ctx.font='600 12px ui-sans-serif,system-ui,sans-serif';
      const tw=ctx.measureText(texto).width, pad=7;
      let bx=sx-tw/2-pad, by=sy-n.size/2-28;
      bx=Math.max(4,Math.min(W-tw-2*pad-4,bx)); by=Math.max(4,by);
      ctx.fillStyle='rgba(15,23,42,0.92)'; roundRect(bx,by,tw+pad*2,20,5); ctx.fill();
      ctx.fillStyle='#fff'; ctx.textBaseline='middle'; ctx.fillText(texto,bx+pad,by+10);
      ctx.restore();
    }
  }
}

const sim = d3.forceSimulation(nodes)
  .force('link', d3.forceLink(links).id(d=>d.id).distance(38).strength(0.75))
  .force('charge', d3.forceManyBody().strength(-70).distanceMax(260))
  .force('x', d3.forceX(W/2).strength(0.06))
  .force('y', d3.forceY(H/2).strength(0.06))
  .force('collide', d3.forceCollide().radius(d=>d.size/2+2))
  .on('tick', draw)
  .on('end', ()=>{ if(!fitDone){ fitDone=true; fit(); }});

const zoomB = d3.zoom().scaleExtent([0.12,4]).on('zoom', e=>{ transform=e.transform; draw(); });
d3.select(canvas).call(zoomB);

function fit(){
  const ns = nodes.filter(n=>n.x!=null);
  if(!ns.length) return;
  let a=Infinity,b=Infinity,c=-Infinity,d=-Infinity;
  for(const n of ns){a=Math.min(a,n.x);b=Math.min(b,n.y);c=Math.max(c,n.x);d=Math.max(d,n.y);}
  const gw=Math.max(1,c-a), gh=Math.max(1,d-b);
  const k=Math.min(2,0.85*Math.min(W/gw,H/gh));
  const tx=W/2-((a+c)/2)*k, ty=H/2-((b+d)/2)*k;
  d3.select(canvas).transition().duration(450)
    .call(zoomB.transform, d3.zoomIdentity.translate(tx,ty).scale(k));
}
document.getElementById('centrar').onclick = fit;

canvas.addEventListener('mousemove', e=>{
  const rect=canvas.getBoundingClientRect(), t=transform;
  const gx=(e.clientX-rect.left-t.x)/t.k, gy=(e.clientY-rect.top-t.y)/t.k;
  let found=null, best=Infinity;
  for(const n of nodes){
    if(n.x==null) continue;
    const dx=n.x-gx, dy=n.y-gy, dd=dx*dx+dy*dy, r=n.size/2+3;
    if(dd<r*r && dd<best){best=dd; found=n.id;}
  }
  if(found!==hov){ hov=found; neigh=found?(adj.get(found)||new Set()):new Set(); draw(); }
});
canvas.addEventListener('mouseleave', ()=>{ if(hov!==null){hov=null; neigh=new Set(); draw();} });

new ResizeObserver(resize).observe(wrap);
resize();
sim.alpha(0.9).restart();
</script>
</body></html>
"""
