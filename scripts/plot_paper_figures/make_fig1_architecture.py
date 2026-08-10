"""High-fidelity Fig. 1 reconstruction for the frozen v1.9 PCRF-R2 line.

The provided four-panel reference supplies only the visual master layout.
All scientific labels and blocks are reconstructed from the PCRF-R2 theory
freeze, the F1 protocol, and the current source-separated implementation.
No training/F2 artifact is read by this script.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle


C = {
    "scout": "#0B559F", "relay": "#357A38", "attacker": "#C92828", "target": "#733F9D",
    "p": "#165DAA", "c": "#3D843D", "conflict": "#B4671D", "critic": "#7B42A0",
    "ink": "#121212", "gray": "#777777", "pale": "#F8FAFC", "pale_blue": "#EEF5FC",
    "pale_green": "#F0F8F0", "pale_gold": "#FFF7EA", "pale_purple": "#F5EEFA",
}
mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 8,
})


def txt(ax, x, y, s, size=8, color=None, weight="normal", ha="center", va="center", **kw):
    ax.text(x, y, s, fontsize=size, color=color or C["ink"], weight=weight, ha=ha, va=va, **kw)


def rounded(ax, x, y, w, h, s, fc="white", ec="#555555", size=7.3, lw=.75, weight="normal"):
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=.008,rounding_size=.018",
                           facecolor=fc, edgecolor=ec, linewidth=lw)
    ax.add_patch(patch); txt(ax, x + w/2, y + h/2, s, size=size, weight=weight)
    return patch


def arr(ax, a, b, color=C["ink"], lw=1.1, ls="-", alpha=1.0, rad=0.0, scale=9):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=scale, color=color,
                                 linewidth=lw, linestyle=ls, alpha=alpha,
                                 connectionstyle=f"arc3,rad={rad}"))


def init(ax, label, title):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, facecolor="white", edgecolor="#222222", linewidth=.72))
    txt(ax, .014, .965, f"({label})", size=12.5, weight="bold", ha="left", va="top")
    txt(ax, .067, .965, title, size=10.7, weight="bold", ha="left", va="top")


def fixed_wing(ax, x, y, color, label=None, s=.037, antenna=False, failed=False):
    wing = Polygon([(x-1.35*s,y), (x-.25*s,y+.63*s), (x+.9*s,y+.15*s), (x+1.5*s,y),
                    (x+.9*s,y-.15*s), (x-.25*s,y-.63*s)], closed=True, facecolor=color,
                   edgecolor="white", linewidth=.55, zorder=4)
    tail = Polygon([(x-.64*s,y), (x-1.03*s,y+.36*s), (x-.82*s,y), (x-1.03*s,y-.36*s)],
                   closed=True, facecolor=color, edgecolor="white", linewidth=.45, zorder=4)
    ax.add_patch(wing); ax.add_patch(tail)
    if antenna:
        ax.plot([x, x], [y+.3*s, y+1.25*s], color=color, lw=1.1)
        for r in (.38, .62, .87):
            ax.add_patch(Circle((x, y+1.0*s), r*s, fill=False, edgecolor=color, linewidth=.65))
    if failed:
        ax.add_patch(Circle((x, y), 1.7*s, fill=False, edgecolor="#D62728", linewidth=1.3, linestyle="--", zorder=9))
        ax.plot([x-.62*s,x+.62*s],[y-.62*s,y+.62*s], color="#D62728", lw=2.0, zorder=10)
        ax.plot([x-.62*s,x+.62*s],[y+.62*s,y-.62*s], color="#D62728", lw=2.0, zorder=10)
    if label: txt(ax, x, y-1.45*s, label, size=8.3, color=color, weight="bold", va="top")


def quadrotor(ax, x, y, color, label=None, s=.036):
    ax.add_patch(Polygon([(x-.46*s,y-.12*s),(x+.46*s,y-.12*s),(x+.28*s,y+.18*s),(x-.28*s,y+.18*s)],
                         closed=True, facecolor=color, edgecolor="white", linewidth=.5, zorder=4))
    for dx, dy in ((-.72,.48),(.72,.48),(-.72,-.48),(.72,-.48)):
        ax.plot([x, x+dx*s], [y, y+dy*s], color=color, lw=1.2, zorder=3)
        ax.add_patch(Circle((x+dx*s,y+dy*s), .27*s, fill=False, edgecolor=color, linewidth=1.0, zorder=4))
    if label: txt(ax, x, y-1.55*s, label, size=8.3, color=color, weight="bold", va="top")


def target_tower(ax, x, y, label=None, s=.043):
    ax.add_patch(Circle((x,y+.18*s), .66*s, fill=False, edgecolor=C["target"], linewidth=1.25))
    ax.add_patch(Circle((x,y+.18*s), .38*s, fill=False, edgecolor=C["target"], linewidth=.85))
    ax.plot([x,y*0+x],[y-.82*s,y+.18*s], color=C["target"], lw=1.1)
    ax.plot([x-.52*s,x+.52*s],[y-.82*s,y-.82*s], color=C["target"], lw=1.1)
    ax.plot([x-.52*s,x],[y-.82*s,y+.18*s], color=C["target"], lw=.8)
    ax.plot([x+.52*s,x],[y-.82*s,y+.18*s], color=C["target"], lw=.8)
    if label: txt(ax, x+.06, y-1.25*s, label, size=8.3, color=C["target"], weight="bold", va="top")


def mountains(ax):
    for base, height, left in ((.13,.16,.03), (.11,.12,.21), (.12,.15,.58)):
        ax.add_patch(Polygon([(left,.09),(left+base/2,.09+height),(left+base,.09)], closed=True,
                             facecolor="#EEF1F4", edgecolor="#D8DDE2", linewidth=.5, alpha=.9, zorder=0))
        ax.add_patch(Polygon([(left+base*.25,.09+height*.43),(left+base/2,.09+height),(left+base*.66,.09+height*.25)],
                             closed=True, facecolor="#FFFFFF", edgecolor="none", alpha=.8, zorder=0))
    ax.plot([.01,.75],[.09,.09], color="#DCE2E8", lw=1.0, alpha=.8, zorder=0)


def panel_a(ax):
    init(ax, "a", "Heterogeneous task scenario")
    mountains(ax)
    quadrotor(ax, .23,.76,C["scout"],"Scout\n(S)",.043)
    fixed_wing(ax,.54,.76,C["relay"],"Relay\n(R)",.050,antenna=True)
    fixed_wing(ax,.23,.33,C["attacker"],"Attacker\n(A)",.052)
    target_tower(ax,.58,.27,"Target\n(T)",.055)
    # Preserve reference geometry; only P/C semantics occupy its relation slots.
    arr(ax,(.27,.77),(.50,.77),C["p"],1.55,":")
    arr(ax,(.25,.72),(.55,.32),C["p"],1.45,":")
    arr(ax,(.52,.70),(.25,.38),C["c"],1.35,"--")
    arr(ax,(.54,.69),(.54,.34),C["c"],1.35,"--")
    rounded(ax,.75,.14,.21,.39,"Legal evidence sources\n\nP  direct perception\n\nC  delivered +\ncache-valid communication",fc="white",ec="#7A7A7A",size=7.8,lw=.8)
    ax.plot([.77,.86],[.53,.53],color=C["p"],lw=1.5,linestyle=":")
    ax.plot([.77,.86],[.37,.37],color=C["c"],lw=1.5,linestyle="--")


def chain(ax,x,y,w=.40,broken=False):
    vals=[("S",C["scout"]),("R",C["relay"]),("A",C["attacker"]),("T",C["target"])]
    xs=[x+w*t for t in (.18,.40,.62,.84)]
    for (name,col),xx in zip(vals,xs):
        if broken and name=="R":
            ax.add_patch(Circle((xx,y),.036,fill=False,edgecolor="#BFBFBF",linestyle="--",linewidth=1.0))
        else:
            ax.add_patch(Circle((xx,y),.036,facecolor="#F9FBFD",edgecolor=col,linewidth=1.0))
            txt(ax,xx,y,name,size=7.0,color=col,weight="bold")
    for i in range(3):
        arr(ax,(xs[i]+.04,y),(xs[i+1]-.04,y),"#222222" if not(broken and i<2) else "#BDBDBD",.95,"-",alpha=1 if not(broken and i<2) else .5,scale=7)
    if broken:
        ax.plot([xs[2]-.035,xs[2]+.035],[y-.035,y+.035],color="#D62728",lw=1.5)
        ax.plot([xs[2]-.035,xs[2]+.035],[y+.035,y-.035],color="#D62728",lw=1.5)


def panel_b(ax):
    init(ax,"b","Failure disrupts coordination")
    txt(ax,.27,.85,"Before failure (normal)",size=8.6,weight="bold")
    txt(ax,.74,.85,"After relay failure",size=8.6,weight="bold")
    for x in (.03,.53): ax.add_patch(Rectangle((x,.35),.40,.41,facecolor="white",edgecolor="#9B9B9B",linewidth=.7))
    quadrotor(ax,.09,.66,C["scout"],s=.026); fixed_wing(ax,.31,.67,C["relay"],s=.032,antenna=True)
    fixed_wing(ax,.10,.45,C["attacker"],s=.032); target_tower(ax,.37,.43,s=.033)
    arr(ax,(.12,.66),(.29,.67),C["p"],1.1,":",scale=7); arr(ax,(.11,.64),(.36,.46),C["p"],1.0,":",scale=7)
    arr(ax,(.30,.63),(.12,.48),C["c"],1.0,"--",scale=7); arr(ax,(.31,.62),(.36,.46),C["c"],1.0,"--",scale=7)
    quadrotor(ax,.59,.66,C["scout"],s=.026); fixed_wing(ax,.80,.67,C["relay"],s=.032,antenna=True,failed=True)
    fixed_wing(ax,.60,.45,C["attacker"],s=.032); target_tower(ax,.87,.43,s=.033)
    arr(ax,(.62,.64),(.86,.46),C["p"],1.0,":",scale=7); arr(ax,(.62,.65),(.79,.67),C["p"],1.0,":",alpha=.25,scale=7)
    arr(ax,(.79,.62),(.62,.48),C["c"],1.0,"--",alpha=.22,scale=7); arr(ax,(.80,.62),(.86,.46),C["c"],1.0,"--",alpha=.22,scale=7)
    rounded(ax,.03,.13,.40,.16,"Information flow (normal)",size=7.4); chain(ax,.03,.185,.40)
    rounded(ax,.53,.13,.40,.16,"Information flow (disrupted)",size=7.4); chain(ax,.53,.185,.40,True)
    rounded(ax,.55,.025,.36,.075,"Delivered communication becomes unavailable;\nlocal P may remain available",fc="#FFF1F0",ec="#EA8077",size=6.5)


def mini_graph(ax,x,y,w=.15,h=.17):
    pts=[(x+.025,y+.035),(x+w*.62,y+h*.72),(x+w*.30,y+h*.24),(x+w*.83,y+h*.28)]
    for (px,py),col in zip(pts,[C["scout"],C["relay"],C["attacker"],C["target"]]): ax.add_patch(Circle((px,py),.012,facecolor=col,edgecolor="white",lw=.4))
    arr(ax,pts[0],pts[1],C["p"],.8,":",scale=5); arr(ax,pts[1],pts[2],C["c"],.7,"--",scale=5); arr(ax,pts[1],pts[3],C["c"],.7,"--",scale=5)


def panel_c(ax):
    init(ax,"c","Overall method pipeline (PCRF-R2)")
    txt(ax,.16,.86,"Local observations",size=8.1,weight="bold")
    txt(ax,.75,.86,"Execution (Decentralized)",size=8.4,weight="bold")
    # top execution row: keep reference slots and density.
    for yy,label,col in ((.74,"Scout",C["scout"]),(.61,"Relay",C["relay"]),(.48,"Attacker",C["attacker"])):
        fixed_wing(ax,.10,yy,col,s=.020)
        txt(ax,.028,yy,label,size=6.7,ha="left")
        rounded(ax,.16,yy-.037,.06,.074,"$o_i$",size=8.0)
        arr(ax,(.13,yy),(.16,yy),scale=6)
    rounded(ax,.27,.47,.20,.39,"P/C legal-source\ngraph construction",size=8.2,weight="bold")
    mini_graph(ax,.29,.51,.16,.23)
    rounded(ax,.50,.54,.11,.20,"PCRF-R2\nencoder",fc="#EEF5FC",ec="#4C83B9",size=8.7,weight="bold")
    rounded(ax,.64,.54,.11,.20,"Actor\nPolicy\n$\\pi_i$",fc="#EEF5FC",ec="#4C83B9",size=8.6,weight="bold")
    txt(ax,.78,.67,"Actions\n$(a_i^t)$",size=7.3)
    rounded(ax,.82,.43,.14,.25,"3DOF\nEnvironment",fc="#F8FAFC",ec="#777777",size=8.0,weight="bold")
    for yy in (.74,.61,.48): arr(ax,(.22,yy),(.27,.65),scale=6)
    arr(ax,(.47,.65),(.50,.65)); arr(ax,(.61,.65),(.64,.65)); arr(ax,(.75,.65),(.81,.60)); arr(ax,(.88,.43),(.88,.33),color=C["critic"],lw=1.0,scale=6)
    # faithful CTDE separator and bottom training path.
    ax.plot([.02,.98],[.40,.40],color="#5F3B91",linewidth=1.0,linestyle="--")
    txt(ax,.72,.385,"CTDE boundary",size=8.5,color="#5F3B91",weight="bold",va="top")
    txt(ax,.84,.07,"Training (Centralized)",size=8.5,color="#5F3B91",weight="bold")
    rounded(ax,.03,.20,.16,.11,"Centralized state\n(training only)",fc="#F3FBF0",ec="#4A9652",size=7.0)
    rounded(ax,.03,.055,.16,.11,"Global reward\n(training only)",fc="#FFF8E8",ec="#C08A25",size=7.0)
    rounded(ax,.27,.05,.20,.29,"Centralized\ntraining graph",fc="#FBFBFB",size=7.7,weight="bold"); mini_graph(ax,.30,.085,.14,.18)
    rounded(ax,.50,.10,.11,.18,"Shared\ncritic\nencoder",fc=C["pale_purple"],ec="#9B63C0",size=7.6,weight="bold")
    rounded(ax,.64,.10,.13,.18,"Centralized\ncritic\n$V_\\phi(s_t)$",fc="#FFF7E7",ec="#C18B27",size=7.7,weight="bold")
    txt(ax,.81,.19,"Value\n(training only)",size=7.2,color="#3561A8",weight="bold")
    arr(ax,(.19,.255),(.27,.255)); arr(ax,(.19,.11),(.27,.11)); arr(ax,(.47,.19),(.50,.19)); arr(ax,(.61,.19),(.64,.19)); arr(ax,(.77,.19),(.81,.19),color="#3561A8")


def little_source(ax,x,y,w,h,color,title,formula=None):
    rounded(ax,x,y,w,h,title,fc="white",ec=color,size=7.1,lw=.9)
    ax.add_patch(Circle((x+w*.75,y+h*.52),.014,facecolor="white",edgecolor=color,lw=.8))
    ax.add_patch(Circle((x+w*.88,y+h*.30),.011,facecolor="white",edgecolor=color,lw=.8))
    arr(ax,(x+w*.77,y+h*.49),(x+w*.86,y+h*.33),color,.7,"-",scale=4)
    if formula: txt(ax,x+w/2,y-.027,formula,size=6.7,color=color)


def panel_d(ax):
    init(ax,"d","PCRF-R2 encoder (zoom-in)")
    # Reference-master left three slots. Third is a descriptor, not an evidence source.
    little_source(ax,.035,.70,.19,.16,C["p"],"P source\nDirect perception",r"$G_i^P$")
    little_source(ax,.035,.46,.19,.16,C["c"],"C source\nDelivered + cache-valid",r"$G_i^C$")
    rounded(ax,.035,.22,.19,.16,"Conflict descriptor\n$[a^P-a^C,d_{PC},age_C,$\n$1-confidence_C]$",fc=C["pale_gold"],ec=C["conflict"],size=6.4,lw=.9)
    # Feature blocks occupy the same visual column as reference edge features.
    rounded(ax,.255,.73,.09,.11,"P edge\nfeatures",fc=C["pale_blue"],ec=C["p"],size=6.5)
    rounded(ax,.255,.49,.09,.11,"C edge\nfeatures",fc=C["pale_green"],ec=C["c"],size=6.5)
    rounded(ax,.255,.25,.09,.11,"legal masks\n+ context",fc="#F7F7F7",ec="#777777",size=6.3)
    # One central module is visually large but explicitly contains two real encoders.
    rounded(ax,.375,.25,.28,.52,"Source-specific\nP/C encoders",fc="#F7FBFF",ec="#4C83B9",size=9.0,lw=1.0,weight="bold")
    rounded(ax,.415,.56,.20,.09,"$h_i^P=m_i^P F_P(G_i^P)$",fc=C["pale_blue"],ec=C["p"],size=7.0)
    rounded(ax,.415,.39,.20,.09,"$h_i^C=m_i^C F_C(G_i^C)$",fc=C["pale_green"],ec=C["c"],size=7.0)
    arr(ax,(.225,.78),(.255,.78),C["p"],.9); arr(ax,(.225,.54),(.255,.54),C["c"],.9); arr(ax,(.225,.30),(.255,.30),C["conflict"],.9)
    arr(ax,(.345,.78),(.375,.62),C["p"],.9); arr(ax,(.345,.54),(.375,.45),C["c"],.9); arr(ax,(.345,.30),(.375,.35),C["conflict"],.9)
    rounded(ax,.69,.43,.13,.19,"Baseline +\nconflict deviation\n$\\beta+\\Delta(c)-\\Delta(0)$\n$\\Delta(0)=0$",fc="#FFFDF7",ec=C["conflict"],size=6.8,lw=.9,weight="bold")
    rounded(ax,.845,.43,.10,.19,"Availability-\nmasked fusion",fc="#F7F7F7",ec="#555555",size=6.3)
    arr(ax,(.655,.52),(.69,.52),C["ink"],1.0); arr(ax,(.82,.52),(.845,.52),C["ink"],1.0)
    txt(ax,.955,.70,"Actor\nembedding",size=7.4,weight="bold")
    for yy,col in zip((.61,.51,.41,.31),(C["scout"],C["relay"],C["attacker"],C["target"])):
        ax.add_patch(Circle((.955,yy),.018,facecolor=col,edgecolor="#555555",lw=.5))
    txt(ax,.955,.23,"$h_i\\in\\mathbb{R}^{d_h}$",size=6.7)
    # Reference-like symbol legend, with only current operations.
    rounded(ax,.05,.055,.77,.09,"Source-preserving combination   |   Availability masking   |   Baseline + conflict deviation",fc="white",ec="#777777",size=6.3)


def legend(ax):
    ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis("off")
    ax.add_patch(FancyBboxPatch((.01,.10),.98,.78,boxstyle="round,pad=.007,rounding_size=.018",facecolor="white",edgecolor="#333333",lw=.75))
    quadrotor(ax,.035,.55,C["scout"],s=.019); txt(ax,.075,.55,"Scout (S)",size=7.6,color=C["scout"],weight="bold",ha="left")
    fixed_wing(ax,.155,.55,C["relay"],s=.021,antenna=True); txt(ax,.195,.55,"Relay (R)",size=7.6,color=C["relay"],weight="bold",ha="left")
    fixed_wing(ax,.285,.55,C["attacker"],s=.021); txt(ax,.325,.55,"Attacker (A)",size=7.6,color=C["attacker"],weight="bold",ha="left")
    target_tower(ax,.42,.54,s=.021); txt(ax,.455,.55,"Target (T)",size=7.6,color=C["target"],weight="bold",ha="left")
    ax.plot([.55,.60],[.55,.55],color=C["p"],lw=1.55,linestyle=":"); txt(ax,.61,.55,"P: direct perception",size=7.4,ha="left")
    ax.plot([.72,.77],[.55,.55],color=C["c"],lw=1.55,linestyle="--"); txt(ax,.78,.55,"C: delivered/cache-valid communication",size=7.4,ha="left")
    ax.add_patch(Circle((.87,.25),.026,fill=False,edgecolor="#D62728",linestyle="--",lw=1.0)); txt(ax,.91,.25,"failed relay",size=6.7,color="#8A3333",ha="left")


def draw(version):
    fig=plt.figure(figsize=(16.4,10.6),facecolor="white")
    # Ratios follow the visual master: left panels 52%, right panels 44%.
    top_y,top_h=.575,.385; bottom_y,bottom_h=.155,.415
    a=fig.add_axes((.025,top_y,.515,top_h)); b=fig.add_axes((.540,top_y,.435,top_h))
    c=fig.add_axes((.025,bottom_y,.515,bottom_h)); d=fig.add_axes((.540,bottom_y,.435,bottom_h))
    l=fig.add_axes((.025,.045,.95,.085))
    panel_a(a);panel_b(b);panel_c(c);panel_d(d);legend(l)
    fig.text(.025,.008,"Fig. 1 | PCRF-R2: architecture overview for heterogeneous UAV coordination under relay failure and communication constraints.",fontsize=9.6,weight="bold")
    return fig


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--version",choices=("fidelity_v1","fidelity_v2"),default="fidelity_v2")
    parser.add_argument("--output-prefix",type=Path,default=Path("paper_figures/fig1_architecture")); args=parser.parse_args()
    args.output_prefix.parent.mkdir(parents=True,exist_ok=True); fig=draw(args.version)
    fig.savefig(args.output_prefix.with_suffix(".svg"),bbox_inches="tight")
    fig.savefig(args.output_prefix.with_suffix(".pdf"),bbox_inches="tight")
    fig.savefig(args.output_prefix.with_suffix(".png"),dpi=600,bbox_inches="tight")
    plt.close(fig); print(f"FIG1_{args.version.upper()}_WRITTEN: {args.output_prefix}")


if __name__=="__main__": main()
