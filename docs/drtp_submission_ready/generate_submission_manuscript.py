"""Create a Chinese near-submission DRTP manuscript from frozen evidence.

This script intentionally contains only verified A/B, held-out OOD, and
PLR summary statistics.  It does not consume the invalid 6-UAV v1 output and
does not invent results for the running 6-UAV v2, semantic-ablation, or
runtime studies.
"""
from __future__ import annotations

from pathlib import Path
import math

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "DRTP_FINAL_MANUSCRIPT_SUBMISSION_READY.docx"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

UTR = "UTR"
DRTP = "DRTP"
PLR = "PLR-style"
COLORS = {UTR: "#7A869A", DRTP: "#167C80", PLR: "#D4862E"}

# These values were read from the completed frozen A/B and matched PLR reports.
MAIN = {
    "A": {UTR: (177.02, 181.12, 79.75, 64.53, 0.730, 0.003),
          DRTP: (216.66, 223.82, 191.49, 23.48, 0.597, 0.009),
          PLR: (203.87, 214.02, 142.02, 36.12, 0.742, 0.014)},
    "B": {UTR: (187.18, 181.42, 164.98, 21.66, 0.711, 0.000),
          DRTP: (210.34, 218.78, 172.03, 30.54, 0.602, 0.000),
          PLR: (220.03, 218.22, 201.06, 13.98, 0.699, 0.000)},
}
OOD = {
    "A": {"参数扰动": {UTR: 157.49, DRTP: 209.20}, "结构留出": {UTR: 178.31, DRTP: 201.08}},
    "B": {"参数扰动": {UTR: 185.33, DRTP: 202.82}, "结构留出": {UTR: 179.38, DRTP: 191.34}},
}


def set_font():
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 8.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.7,
    })


def save(fig, name: str):
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(FIG / f"{name}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def rounded(ax, xy, text, width=0.19, height=0.13, color="#E9F3F3", fontsize=8):
    x, y = xy
    p = FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.012,rounding_size=0.02",
                       facecolor=color, edgecolor="#39636A", linewidth=0.8)
    ax.add_patch(p)
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=fontsize, wrap=True)
    return (x + width / 2, y + height / 2)


def arrow(ax, start, end):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=10, linewidth=0.9,
                                 color="#49636A", shrinkA=4, shrinkB=5))


def fig1_motivation():
    fig, ax = plt.subplots(figsize=(7.1, 3.2))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.03, 0.94, "通信拓扑退化改变协同策略可获得的信息结构", fontsize=11, fontweight="bold", color="#173B45")
    # normal graph
    n = [(0.13, .68), (.25, .68), (.37, .68)]
    for a, b in zip(n[:-1], n[1:]): ax.plot([a[0], b[0]], [a[1], b[1]], color="#167C80", lw=2.1)
    for i, (x, y) in enumerate(n, 1):
        ax.scatter(x, y, s=520, c="#DDF0F0", edgecolors="#167C80", zorder=3)
        ax.text(x, y, f"UAV{i}", ha="center", va="center", fontsize=8, zorder=4)
    ax.text(.25, .49, "标称拓扑：信息可达与协同链完整", ha="center", fontsize=8)
    # degraded graph
    d = [(0.60, .68), (.72, .68), (.84, .68)]
    ax.plot([d[0][0], d[1][0]], [d[0][1], d[1][1]], color="#D4862E", lw=2.1)
    ax.plot([.775, .785], [.68, .68], color="#C33C54", lw=2.4)
    for i, (x, y) in enumerate(d, 1):
        ax.scatter(x, y, s=520, c="#FFF1DF", edgecolors="#D4862E", zorder=3)
        ax.text(x, y, f"UAV{i}", ha="center", va="center", fontsize=8, zorder=4)
    ax.text(.72, .49, "退化拓扑：链路断裂、信息时延或缺失", ha="center", fontsize=8)
    arrow(ax, (.45,.68), (.52,.68)); ax.text(.485, .75, "故障", ha="center", fontsize=8, color="#C33C54")
    rounded(ax, (.11,.15), "信息可获得性改变", .20, .13, "#F4F7F8")
    rounded(ax, (.40,.15), "协同决策分布偏移", .20, .13, "#F4F7F8")
    rounded(ax, (.69,.15), "需要拓扑感知的鲁棒训练", .20, .13, "#E9F3F3")
    arrow(ax, (.31,.215), (.40,.215)); arrow(ax, (.60,.215), (.69,.215))
    save(fig, "Fig1_topology_degradation_motivation")


def fig2_framework():
    fig, ax = plt.subplots(figsize=(7.2, 3.35))
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
    ax.text(.02,.94,"DRTP：以拓扑语义塑造训练阶段的故障暴露分布", fontsize=11, fontweight="bold", color="#173B45")
    boxes = [
        (.03,.56,"故障拓扑库\n标称组 + 故障组", "#F4F7F8"),
        (.245,.56,"组级难度估计\n相对标称性能退化", "#FFF1DF"),
        (.46,.56,"自适应暴露分布 q\n约束下更新", "#E9F3F3"),
        (.675,.56,"MAPPO 训练\n采样 reset 条件", "#E9F3F3"),
    ]
    centers=[]
    for x,y,t,c in boxes: centers.append(rounded(ax,(x,y),t,.18,.16,c,8))
    for a,b in zip(centers[:-1],centers[1:]): arrow(ax,(a[0]+.09,a[1]),(b[0]-.09,b[1]))
    rounded(ax,(.68,.20),"鲁棒协同策略\n固定接口部署",.19,.14,"#DDF0F0",8)
    arrow(ax,(.765,.56),(.775,.34))
    ax.text(.02,.08,"保持不变：actor、critic、PPO 目标、奖励、观测、动作接口与环境转移。\n唯一变化：reset 阶段的拓扑故障条件采样概率。", fontsize=8.3, color="#425A60")
    save(fig, "Fig2_drtp_framework")


def fig3_mechanism_layout():
    fig, axes = plt.subplots(1,2,figsize=(7.15,3.05), gridspec_kw={"width_ratios":[1.05,1]})
    ax=axes[0]
    x=[0,1,2,3,4]; uniform=[.25]*5; dynamic=[.25,.31,.38,.32,.35]
    ax.plot(x,uniform,"--",color="#7A869A",lw=1.7,label="UTR：均匀暴露")
    ax.plot(x,dynamic,"-o",color="#167C80",lw=2.0,ms=4,label="DRTP：示意的非均匀暴露")
    ax.set_xticks(x,["初期","…","中期","…","终点"]); ax.set_ylabel("组级暴露概率 q")
    ax.set_ylim(.15,.45); ax.legend(loc="upper left",fontsize=7)
    ax.set_title("(a) 训练过程中的 q 演化：由真实日志填充",fontsize=9)
    ax.text(.02,.02,"本图的曲线形状仅作版式示意；\n投稿版替换为全部 DRTP seed 的真实日志。",transform=ax.transAxes,fontsize=6.7,color="#68747A")
    ax=axes[1]
    groups=["标称","R-上游","R-下游","C-平衡","C-交叉"]
    difficulty=[.12,.39,.52,.68,.81]
    exposure=[.18,.24,.31,.38,.43]
    ax.scatter(difficulty,exposure,s=55,c="#167C80",edgecolor="white",linewidth=.8)
    for a,b,g in zip(difficulty,exposure,groups): ax.annotate(g,(a,b),xytext=(4,4),textcoords="offset points",fontsize=7)
    ax.set_xlabel("相对标称的组级难度"); ax.set_ylabel("终末暴露概率")
    ax.set_title("(b) 难度—暴露关系：由真实汇总填充",fontsize=9)
    ax.text(.02,.02,"点位为机制图的布局占位，\n不表示本研究未导出的数值。",transform=ax.transAxes,fontsize=6.7,color="#68747A")
    fig.tight_layout(); save(fig,"Fig3_exposure_mechanism")


def fig4_main():
    fig, axes=plt.subplots(1,2,figsize=(7.15,3.1),sharey=True)
    for ax, cohort in zip(axes,["A","B"]):
        methods=[UTR,DRTP,PLR]
        vals=[MAIN[cohort][m][0] for m in methods]
        sds=[MAIN[cohort][m][3] for m in methods]
        ax.bar(range(3),vals,yerr=sds,capsize=3,color=[COLORS[m] for m in methods],edgecolor="white")
        ax.set_xticks(range(3),methods); ax.set_title(f"Cohort {cohort}")
        ax.set_ylim(0,285); ax.set_ylabel("扰动条件 J（均值 ± seed SD）")
        for i,v in enumerate(vals): ax.text(i,v+7,f"{v:.1f}",ha="center",fontsize=8)
    fig.suptitle("主结果：独立 cohort 的固定终点评估",y=1.02,fontsize=10,fontweight="bold")
    fig.tight_layout(); save(fig,"Fig4_main_robustness")


def fig5_ood():
    fig,axes=plt.subplots(1,2,figsize=(7.15,3.1),sharey=True)
    width=.32
    for ax,cohort in zip(axes,["A","B"]):
        cond=list(OOD[cohort]); x=range(len(cond))
        u=[OOD[cohort][c][UTR] for c in cond]; d=[OOD[cohort][c][DRTP] for c in cond]
        ax.bar([i-width/2 for i in x],u,width,label=UTR,color=COLORS[UTR])
        ax.bar([i+width/2 for i in x],d,width,label=DRTP,color=COLORS[DRTP])
        ax.set_xticks(list(x),cond); ax.set_title(f"Cohort {cohort}"); ax.set_ylim(0,245)
        ax.set_ylabel("扰动条件 J（cohort 均值）")
        for i,(a,b) in enumerate(zip(u,d)):
            ax.text(i-width/2,a+5,f"{a:.1f}",ha="center",fontsize=7)
            ax.text(i+width/2,b+5,f"{b:.1f}",ha="center",fontsize=7)
    axes[0].legend(fontsize=8); fig.suptitle("留出扰动与未见结构条件下的终点评估",y=1.02,fontsize=10,fontweight="bold")
    fig.tight_layout(); save(fig,"Fig5_ood_generalization")


def fig6_ablation_placeholder():
    fig,ax=plt.subplots(figsize=(7.15,2.65)); ax.axis("off"); ax.set_xlim(0,1); ax.set_ylim(0,1)
    ax.text(.02,.90,"机制消融：以最小新增训练隔离语义与自适应更新",fontsize=11,fontweight="bold",color="#173B45")
    labels=[("UTR","无语义\n无自适应"),("Fixed-DRTP","有语义\n固定分布"),("Random-DRTP","随机语义\n有自适应"),("DRTP","有语义\n有自适应")]
    for i,(name,detail) in enumerate(labels):
        x=.05+i*.235; c="#E9F3F3" if name=="DRTP" else "#F4F7F8"
        rounded(ax,(x,.37),f"{name}\n{detail}",.18,.20,c,8)
    ax.text(.05,.14,"正式结果将在 Fixed-DRTP 与 Random-DRTP 的独立 5-seed 终点评估完成后填入。\n图的论证目标：区分“拓扑语义”与“动态暴露更新”两项贡献，而非重复主结果。",fontsize=8.2,color="#425A60")
    save(fig,"Fig6_ablation_placeholder")


def fig7_scale_placeholder():
    fig,ax=plt.subplots(figsize=(7.15,2.65)); ax.axis("off"); ax.set_xlim(0,1); ax.set_ylim(0,1)
    ax.text(.02,.90,"跨规模验证：从 3-UAV 到 6-UAV 的拓扑退化鲁棒协同",fontsize=11,fontweight="bold",color="#173B45")
    for n,x in [(3,.16),(6,.55)]:
        pts=[]
        for i in range(n):
            angle=2*math.pi*i/n; pts.append((x+.11*math.cos(angle),.53+.20*math.sin(angle)))
        for i in range(n):
            a,b=pts[i],pts[(i+1)%n]; ax.plot([a[0],b[0]],[a[1],b[1]],color="#167C80",lw=1.3)
        for px,py in pts: ax.scatter(px,py,s=130,c="#DDF0F0",edgecolors="#167C80",zorder=3)
        ax.text(x,.20,f"{n}-UAV",ha="center",fontsize=10,fontweight="bold")
    arrow(ax,(.31,.53),(.43,.53)); ax.text(.37,.61,"相同方法原则\n不同团队规模",ha="center",fontsize=8)
    ax.text(.02,.06,"仅使用 fault-step=3 的修复后正式 6-UAV 协议；旧协议因故障注入晚于 episode 结束而不进入本文结果。\n当前保留版式与图注，正式数值待 v2 固定终点评估返回后填入。",fontsize=7.7,color="#425A60")
    save(fig,"Fig7_cross_scale_placeholder")


def tc(cell, text, bold=False, size=8, color=None):
    cell.text=""
    p=cell.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run(str(text)); r.bold=bold; r.font.size=Pt(size); r.font.name="Microsoft YaHei"
    r._element.rPr.rFonts.set(qn("w:eastAsia"),"Microsoft YaHei")
    if color: r.font.color.rgb=RGBColor(*color)
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER


def shade(cell, fill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement("w:shd"); shd.set(qn("w:fill"),fill); tcPr.append(shd)


def set_cell_border(cell, **kwargs):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr(); borders=tcPr.first_child_found_in("w:tcBorders")
    if borders is None: borders=OxmlElement("w:tcBorders"); tcPr.append(borders)
    for edge in ("top","left","bottom","right"):
        if edge in kwargs:
            tag="w:"+edge; element=borders.find(qn(tag))
            if element is None: element=OxmlElement(tag); borders.append(element)
            for key,value in kwargs[edge].items(): element.set(qn("w:"+key),str(value))


def table(doc, headers, rows, widths=None):
    t=doc.add_table(rows=1, cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.style="Table Grid"
    for i,h in enumerate(headers):
        tc(t.rows[0].cells[i],h,True,8,(255,255,255)); shade(t.rows[0].cells[i],"1D5E63")
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row):
            tc(cells[i],v,False,7.5)
            if len(t.rows)%2==0: shade(cells[i],"F2F6F6")
    for row in t.rows:
        for cell in row.cells:
            set_cell_border(cell, top={"val":"single","sz":"4","color":"C9D4D5"}, bottom={"val":"single","sz":"4","color":"C9D4D5"}, left={"val":"single","sz":"4","color":"C9D4D5"}, right={"val":"single","sz":"4","color":"C9D4D5"})
    if widths:
        for row in t.rows:
            for cell,w in zip(row.cells,widths): cell.width=Cm(w)
    doc.add_paragraph().paragraph_format.space_after=Pt(2)
    return t


def para(doc, text="", style=None, bold_lead=None):
    p=doc.add_paragraph(style=style)
    p.paragraph_format.first_line_indent=Cm(.74) if style is None else Cm(0)
    p.paragraph_format.line_spacing=1.45
    p.paragraph_format.space_after=Pt(5)
    if bold_lead and text.startswith(bold_lead):
        r=p.add_run(bold_lead); r.bold=True; r.font.name="Microsoft YaHei"; r._element.rPr.rFonts.set(qn("w:eastAsia"),"Microsoft YaHei")
        r=p.add_run(text[len(bold_lead):]); r.font.name="Microsoft YaHei"; r._element.rPr.rFonts.set(qn("w:eastAsia"),"Microsoft YaHei")
    else:
        r=p.add_run(text); r.font.name="Microsoft YaHei"; r._element.rPr.rFonts.set(qn("w:eastAsia"),"Microsoft YaHei")
    return p


def heading(doc, text, level=1):
    p=doc.add_heading(text,level=level); p.paragraph_format.space_before=Pt(11); p.paragraph_format.space_after=Pt(5)
    return p


def cap(doc, text):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(8)
    r=p.add_run(text); r.bold=True; r.font.size=Pt(8.5); r.font.name="Microsoft YaHei"; r._element.rPr.rFonts.set(qn("w:eastAsia"),"Microsoft YaHei")


def add_figure(doc, name, caption, width=15.2):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(FIG/name),width=Cm(width))
    cap(doc,caption)


def page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def setup_doc():
    doc=Document(); sec=doc.sections[0]
    sec.top_margin=Cm(2.25); sec.bottom_margin=Cm(2.25); sec.left_margin=Cm(2.2); sec.right_margin=Cm(2.2)
    normal=doc.styles["Normal"]; normal.font.name="Times New Roman"; normal._element.rPr.rFonts.set(qn("w:eastAsia"),"Microsoft YaHei"); normal.font.size=Pt(9.5)
    for s,size,color in [("Title",18,"173B45"),("Heading 1",14,"173B45"),("Heading 2",11,"1D5E63"),("Heading 3",10,"1D5E63")]:
        st=doc.styles[s]; st.font.name="Microsoft YaHei"; st._element.rPr.rFonts.set(qn("w:eastAsia"),"Microsoft YaHei"); st.font.size=Pt(size); st.font.color.rgb=RGBColor.from_string(color); st.font.bold=True
    for style in doc.styles:
        if style.type==WD_STYLE_TYPE.PARAGRAPH: style.paragraph_format.widow_control=True
    footer=sec.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
    rr=footer.add_run("拓扑感知鲁棒训练框架 DRTP  |  投稿前工作稿"); rr.font.size=Pt(7.5); rr.font.color.rgb=RGBColor(100,110,115)
    return doc


def add_title(doc):
    p=doc.add_paragraph(style="Title"); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("面向通信拓扑退化的多无人机协同鲁棒训练\n——拓扑感知动态训练暴露分配方法").font.name="Microsoft YaHei"
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(16)
    r=p.add_run("DRTP: Topology-aware Dynamic Robustness Training Exposure Allocation"); r.italic=True; r.font.size=Pt(10); r.font.color.rgb=RGBColor(80,95,100)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run("作者与单位信息按目标期刊要求填写"); r.font.size=Pt(9); r.font.color.rgb=RGBColor(100,110,115)
    heading(doc,"摘 要",1)
    para(doc,"多无人机协同任务依赖通信拓扑维持信息共享与角色互补。实际执行中的链路失效、节点失效或中继关系变化并非普通环境噪声：它们会改变智能体可获得的信息结构，进而使训练阶段与部署阶段之间出现拓扑退化偏移。现有随机化训练通常通过均匀抽取故障条件扩大经验覆盖，却未区分不同拓扑退化条件对协同学习造成的难度差异。本文提出拓扑感知动态鲁棒训练暴露分配框架（DRTP），在不改变 actor、critic、PPO 目标、奖励、观测、动作接口或环境转移的前提下，仅在 reset 阶段根据拓扑组语义与相对标称表现的难度估计，自适应调整故障条件的训练暴露概率。该设计旨在把有限训练预算从均匀覆盖转化为面向结构性信息退化的鲁棒性塑造。")
    para(doc,"在两个彼此独立的 5-seed cohort 上，采用固定 10M 终点评估，DRTP 的扰动条件回报均值分别达到 216.66 和 210.34，高于对应 UTR 的 177.02 和 187.18；A cohort 中，DRTP 同时呈现更高的最低 seed 回报和更低的 seed 离散度。结构留出评估表明，DRTP 在两批 cohort 的未见结构条件下仍保持高于 UTR 的 cohort-level 回报。与 PLR-style 外部比较器的匹配比较显示，A cohort 中 DRTP 取得更高扰动回报并降低超时率；B cohort 中 PLR-style 的回报更高，而 DRTP 呈现更优的成功率—超时权衡，说明二者对应不同的训练暴露归纳偏置。本文因此将 DRTP 定位为一种面向拓扑退化的鲁棒协同训练框架：它并不保证每个随机 seed 均获提升，也不宣称对所有安全指标单调占优，但在本文评估的拓扑故障设置中呈现了重复的 cohort-level 鲁棒性收益。")
    para(doc,"关键词：多无人机协同；多智能体强化学习；通信拓扑退化；鲁棒训练；动态训练暴露分配；MAPPO")
    heading(doc,"术语与主张边界",2)
    table(doc,["术语","本文固定含义"],[
        ["拓扑退化","通信链路、节点或中继关系的故障引起的信息可获得性和协同结构变化。"],
        ["UTR","Uniform Topology Randomization，训练时对预定义故障组均匀暴露。"],
        ["DRTP","Topology-aware Dynamic Robustness Training Exposure Allocation，基于组级难度的受约束自适应暴露分配。"],
        ["PLR-style","通用优先级环境/条件重放比较器；不显式编码本文的拓扑语义。"],
        ["cohort-level","以独立训练 seed 为单位、在 cohort 内共同解读均值、中位数、低尾部与安全相关指标。"],
    ],[3.2,12.0])
    page_break(doc)


def add_introduction(doc):
    heading(doc,"1 引言",1)
    para(doc,"无人机集群在搜索、护航、拦截、灾害响应与协同感知等任务中，需要在分布式观测条件下持续交换局部信息。通信拓扑由可用链路、相对几何、中继节点和任务阶段共同决定，因此并不是一个无关紧要的实现细节。只要一条关键链路消失，原本能够共享的目标、任务分配或协同意图便可能变为局部不可见；同一组局部观测在不同通信拓扑下也可能对应不同的最优协同行为。由此，通信故障带来的挑战不只是状态值的轻微扰动，而是多智能体策略所依赖的信息结构发生了改变。")
    para(doc,"这一性质使拓扑退化成为 UAV 多智能体强化学习（MARL）中的一个独特鲁棒性问题。训练阶段若主要见到完整拓扑，测试阶段的结构性信息丢失会形成明显的分布偏移；若训练阶段只把故障条件作为均等的随机变量处理，策略又可能在稀缺而困难的拓扑下缺乏足够的协同练习。常规 domain randomization 有助于增加环境多样性，但它默认每个采样条件具有相同训练价值。对于具有明确结构语义的拓扑故障集合，这一默认假设并不充分：不同故障组会破坏不同的信息路径、角色依赖或中继关系，因而可能产生不同的回报退化、超时风险和恢复难度。")
    para(doc,"训练暴露分配因而是一个值得单独研究的控制变量。它不改变任务本身，也不在部署时增加额外模块；它决定的是策略在有限训练预算内反复经历哪些拓扑退化、以何种相对频率经历。均匀暴露可被视为一个透明且重要的基线，但其训练效率取决于所有条件难度近似相同这一强假设。通用优先级重放或课程学习能够依据学习信号改变采样频率，却通常不将通信拓扑的故障语义、标称参考和组间可解释性作为显式设计对象。")
    para(doc,"本文提出 DRTP（Topology-aware Dynamic Robustness Training Exposure Allocation），将拓扑退化下的协同鲁棒性表述为一个训练阶段的暴露塑造问题。DRTP 首先把预定义的标称与故障条件组织为可解释的拓扑组，然后以相对标称表现的组级难度信号估计哪些退化条件更需要训练暴露，并在概率下界、上界与标称锚定约束下更新条件分布 q。关键的是，DRTP 保持 actor、critic、PPO 更新、奖励、观测、动作接口和环境转移完全不变；它只改变 episode reset 时的条件选择。因而，任何性能差异都可归因于训练暴露分配，而非网络容量、奖励塑形或推理阶段特权信息。")
    para(doc,"本文的贡献并非把一个加权采样器包装为新的控制器，而是提出并检验以下视角：通信拓扑退化会改变协同信息结构，因而鲁棒训练应显式管理不同结构退化条件的暴露。具体而言：")
    for t in [
        "提出 topology-aware robustness training 的问题视角，将故障拓扑视为会改变协同信息结构的训练分布，而非无语义的随机扰动。",
        "设计 DRTP，以相对标称表现的组级难度与受约束的自适应概率更新，实现面向拓扑语义的训练暴露塑造，同时保持 MAPPO 学习器与环境接口不变。",
        "在独立 A/B cohort、固定终点评估、结构留出 OOD 评估与 PLR-style 外部比较中建立证据链，并为语义消融、运行开销和修复后 6-UAV 跨规模验证预留严格的正式协议。",
    ]:
        p=doc.add_paragraph(style="List Bullet"); p.add_run(t)
    add_figure(doc,"Fig1_topology_degradation_motivation.png","图1  通信拓扑退化的问题动机与协同信息结构变化。该图置于引言末尾，用于在介绍方法前说明：链路故障会改变信息可获得性和协同决策条件，而不仅是改变一个普通环境变量。")


def add_related_work(doc):
    heading(doc,"2 相关工作",1)
    heading(doc,"2.1 多智能体强化学习与通信受限协同",2)
    para(doc,"集中训练、分散执行范式为部分可观测协同决策提供了常用基础[1]。以 MAPPO 为代表的策略优化方法在同质和异质合作任务中表现出良好的工程稳定性[3]；同时，通信学习、图结构策略与消息传递机制试图利用智能体间的关系信息改善局部决策[5,6]。此类研究主要回答“如何在给定信息图下学习协作策略”，而本文关注互补的问题：当给定信息图在执行中退化时，训练阶段应如何组织经历，以使同一策略更好地适应结构性信息丢失。DRTP 不替换现有 actor 或 critic，也不要求新的通信编码器，因此可与不同的 CTDE 学习器结合。")
    heading(doc,"2.2 随机化、课程学习与优先级条件采样",2)
    para(doc,"环境随机化通过在训练中注入参数、扰动或场景差异来缩小训练—测试分布差距；课程学习与优先级重放则进一步尝试把训练预算投向更具学习价值的条件[4]。它们为“训练经历可以被主动分配”提供了重要启发。然而，通用采样机制通常将条件视为由损失、学习进度或其他无结构优先级描述的项目，未必保留故障条件之间的物理和协同语义。DRTP 的区别不在于否定这类方法，而在于把通信拓扑组、相对标称难度和标称暴露约束同时纳入分配规则，使概率变化能够对应可解释的退化结构。")
    heading(doc,"2.3 UAV 集群鲁棒性与拓扑退化",2)
    para(doc,"UAV 集群的鲁棒性研究常覆盖动力学不确定性、传感误差、对抗扰动、通信时延与失联等因素。通信拓扑退化则处于这些因素的交叉点：它既影响信息流，又可能改变角色之间的依赖关系和任务完成路径。若将其仅作为独立噪声处理，训练过程难以反映不同故障结构的相对困难程度。本文不主张覆盖所有通信失效模型，而是以预定义、可复现的拓扑条件组为对象，检验 topology-aware exposure 是否能在所评估的故障空间内塑造更稳健的协同能力。")
    table(doc,["维度","UTR","PLR-style","DRTP"],[
        ["采样对象","预定义拓扑组","通用条件/环境条目","预定义且有语义的拓扑组"],
        ["适应信号","无，均匀抽取","通用优先级或学习信号","相对标称的组级难度"],
        ["拓扑语义","不显式使用","不要求显式使用","显式保留组与故障含义"],
        ["标称参考","均匀组之一","通常不是必要项","作为难度锚定与暴露约束"],
        ["更新规则","固定均匀分布","依具体优先级机制而定","受约束的 q 自适应更新"],
    ],[2.3,4.2,4.2,4.2])
    cap(doc,"表1  UTR、PLR-style 与 DRTP 的机制定位比较。该表不是对 PLR-style 的性能结论，而是说明三者分配训练经历时使用的信息不同。")
    add_figure(doc,"Fig2_drtp_framework.png","图2  DRTP 框架。方法层只重分配 reset 条件的训练暴露；actor、critic、PPO、奖励、观测、动作接口与环境转移均保持不变。该图置于相关工作之后、问题定义之前，承接“为什么拓扑语义应进入训练暴露分配”的论述。")


def add_problem_method(doc):
    heading(doc,"3 问题定义",1)
    heading(doc,"3.1 拓扑退化下的协同决策",2)
    para(doc,"考虑由 N 个异质 UAV 构成的合作系统。在时刻 t，智能体 i 接收局部观测 o_i^t，并通过可用通信图 G_t=(V,E_t) 接收邻居信息。策略 π_θ(a_i^t|o_i^t,m_i^t) 在分散执行时仅依赖本地可得信息，其中 m_i^t 表示由当前有效邻域产生的通信消息。标称条件用 c_0 表示；故障条件集合 C_f={c_1,…,c_K} 包含中继节点、上游/下游链路、交叉链路及其他预定义的拓扑退化组。一次 episode 的 reset 条件 c 决定通信拓扑的退化模式与发生语义，而环境动力学、奖励及动作空间不随训练方法改变。")
    para(doc,"若训练分布 p_train(c) 与部署时的拓扑退化分布不匹配，策略在困难但低频的条件上可能缺乏足够的协同练习。本文不假设每个故障组有相同的重要性，也不试图预测任意真实世界故障的先验概率；研究目标是在固定的、可审计的训练条件库内，构造一个受约束的暴露分布 q_t(c)，使有限训练预算更有针对性地塑造拓扑退化下的鲁棒协同。")
    heading(doc,"3.2 训练条件组与相对标称难度",2)
    para(doc,"DRTP 以 topology group 而非单个 episode 为分配粒度。对第 k 个故障组，令 \u0304J_k(t) 为当前窗口内的组级性能估计，\u0304J_0(t) 为同一窗口的标称组估计。定义相对标称退化为 Δ_k(t)=max(0,\u0304J_0(t)-\u0304J_k(t))，并结合稳定化尺度得到难度 d_k(t)。这一相对化设计避免把任务整体学习进程误识别为单个故障组的固有困难：当所有组随训练共同改善时，难度主要反映故障组相对标称协同能力的缺口。该信号是训练分配依据，而非对拓扑“真实难度”的因果断言。")
    heading(doc,"3.3 受约束的自适应暴露更新",2)
    para(doc,"将 d_k(t) 归一化为候选分配 \u0303q_k(t)，DRTP 以平滑更新 q_{t+1}=(1-α)q_t+α\u0303q(t) 调整暴露概率。为防止困难组暂时波动导致训练分布塌缩，更新同时施加每组最小/最大暴露约束，并保留标称锚定概率。因而 q 既能够偏离均匀分布以响应训练难度，又不会放弃标称协调能力或使任一组长期消失。这里的 α、概率边界和组定义均在训练前冻结；终点评估不根据回报选择 checkpoint 或重新配置 q。")
    heading(doc,"3.4 算法过程与公平比较",2)
    para(doc,"算法1给出了 DRTP 的训练过程。与 UTR 的唯一差异是步骤 3 的 reset 条件采样。后续 rollout、优势估计、PPO 更新、网络参数更新和终点评估完全共享。这样的设计使论文所讨论的机制具备可分离性：若 DRTP 与 UTR 的表现出现差异，直接可检验的解释是训练经历在拓扑组之间被不同地分配，而不是学习器或任务定义发生了变化。")
    table(doc,["算法1：DRTP 训练过程",""],[
        ["输入","拓扑组集合 C={c_0,…,c_K}；初始均匀分布 q_0；PPO 参数 θ；更新系数 α；概率约束 Ω。"],
        ["1","初始化 q←q_0，并初始化每个组的性能统计。"],
        ["2","从 q 抽取 reset 条件 c，采集对应 topology condition 下的 MAPPO rollout。"],
        ["3","使用与 UTR 相同的优势估计和 PPO 目标更新 θ；记录组级性能。"],
        ["4","计算相对标称退化 Δ_k 和难度 d_k，得到候选分配 \u0303q。"],
        ["5","将 q←Π_Ω[(1−α)q+α\u0303q]，其中 Π_Ω 表示带标称锚定的概率可行域投影。"],
        ["输出","训练完成后的同一策略接口 π_θ；不增加部署时模块。"],
    ],[3.2,12.0])
    cap(doc,"算法1  DRTP 训练过程。符号以论文文字为准；投稿版可将本表转换为目标期刊偏好的伪代码环境。")
    add_figure(doc,"Fig3_exposure_mechanism.png","图3  训练暴露机制的版式设计。（a）展示 UTR 的均匀暴露与 DRTP 的 seed-dependent 非均匀 q 演化；（b）展示组级相对标称难度与终末暴露的描述性关系。正式图由全部 DRTP seed 的冻结 sampler 日志生成，不用示意曲线作定量证据。")


def add_experimental_setup(doc):
    heading(doc,"4 实验设置",1)
    heading(doc,"4.1 研究问题与证据结构",2)
    para(doc,"实验不是把所有可获得指标逐项罗列，而是围绕五个审稿相关问题构建。RQ1 检验 topology-aware exposure 是否在已定义的拓扑退化条件下改善鲁棒性；RQ2 检验这种收益是否能保留到留出的结构条件；RQ3 检验相对于通用优先级机制，拓扑语义是否提供不同的可解释价值；RQ4 检验方法能否迁移到更大 UAV 团队；RQ5 检验该训练阶段机制的计算代价。每个问题均对应预先固定的训练预算、终点评估或待完成的正式协议。")
    heading(doc,"4.2 共同训练与评估协议",2)
    para(doc,"主比较在相同的异质 UAV 协同环境、PPO/MAPPO 配置、网络结构、奖励、观测、动作接口、环境转移和 10M 训练预算下进行。每条轨迹在训练结束时采用固定 endpoint checkpoint，并在冻结的评估 tape 上执行终点评估。A 与 B 为相互独立的 5-seed training cohort，统计解释以 training seed 为独立单位并保持 cohort 分开报告；任何 n=10 汇总仅可用于描述性展示，不替代独立 cohort 证据。UTR、DRTP 和 PLR-style 使用相同的比较对象与固定终点评估设置。")
    table(doc,["项目","设置与控制原则"],[
        ["学习器","共享的 MAPPO/PPO 学习器；actor、critic 和优化目标保持一致。"],
        ["环境与接口","相同 UAV 协同环境、奖励、观测、动作接口与环境转移。"],
        ["训练预算","每条主轨迹固定 10M 环境步；不以终点评估回报选择 checkpoint。"],
        ["条件差异","UTR 为均匀拓扑随机化；DRTP 仅修改 reset 条件 q；PLR-style 为外部通用优先级比较。"],
        ["独立重复","A/B 各 5 个训练 seed，分别分析和报告。"],
        ["核心指标","扰动条件回报 J、成功率、超时率、碰撞率；联合解读均值、中位数、低尾部与 seed 离散度。"],
        ["OOD","固定的参数扰动与结构留出条件；不在线使用评估结果更新训练。"],
    ],[3.2,12.0])
    cap(doc,"表2  共同实验设置与公平比较控制。")
    heading(doc,"4.3 指标、统计与主张边界",2)
    para(doc,"J 为任务回报的固定协议汇总；success、timeout 与 collision 反映任务完成和安全相关结果。鉴于 MARL 训练存在 seed-dependent variation，本文不把单一均值作为唯一结论，也不以“所有 seed 均提升”作为必要条件。主结果同时报告 mean、median、最低 seed、sample SD 及 timeout/collision；当指标呈现不同方向时，按任务含义联合解释。本文不报告未经预先定义的显著性检验，也不把 A/B 合并为确认性 n=10 推断。")


def add_results(doc):
    heading(doc,"5 结果",1)
    heading(doc,"5.1 RQ1：DRTP 是否改善拓扑退化下的鲁棒性？",2)
    para(doc,"在两个独立的固定终点评估 cohort 中，DRTP 均取得高于 UTR 的扰动条件回报均值。A cohort 中，DRTP 的均值为 216.66，而 UTR 为 177.02；B cohort 中，DRTP 的均值为 210.34，而 UTR 为 187.18。A cohort 的改善并不只来自上尾部：DRTP 的最低 seed 回报从 79.75 提升至 191.49，sample SD 从 64.53 降至 23.48，且平均超时率从 0.730 降至 0.597。B cohort 中，DRTP 的均值和中位数同样更高，最低 seed 从 164.98 提升至 172.03，平均超时率从 0.711 降至 0.602。")
    para(doc,"这些结果支持的结论是：在本文定义的拓扑退化评估条件下，DRTP 相对 UTR 呈现重复的 cohort-level 鲁棒性收益。证据不支持“每个 seed 必然提升”这一更强命题；例如 A cohort 的配对方向为 3/5 正向。该差异提示训练随机性仍然影响局部结果，因此本文将重点置于两个独立 cohort 中重复出现的中心趋势、低尾部行为和超时风险，而不是将任一个单 seed 解释为普遍规律。")
    table(doc,["Cohort","方法","J 均值","J 中位数","最低 J","J 的 SD","超时率","碰撞率"],[
        ["A","UTR","177.02","181.12","79.75","64.53","0.730","0.003"],
        ["A","DRTP","216.66","223.82","191.49","23.48","0.597","0.009"],
        ["B","UTR","187.18","181.42","164.98","21.66","0.711","0.000"],
        ["B","DRTP","210.34","218.78","172.03","30.54","0.602","0.000"],
    ],[1.3,1.6,1.75,1.75,1.75,1.65,1.6,1.5])
    cap(doc,"表3  UTR 与 DRTP 的主结果（每个 cohort n=5）。J 为扰动条件终点评估汇总；SD 为 training seed 间样本标准差。A/B 分开报告，未将二者合并为确认性推断。")
    add_figure(doc,"Fig4_main_robustness.png","图4  主鲁棒性比较。柱体为 cohort 内扰动条件 J 均值，误差线为 seed 间 SD；PLR-style 作为外部比较器在同一图中提供机制语境，详细解释见 RQ3。图置于 RQ1 结果之后，以突出独立 cohort 的重复趋势。")
    heading(doc,"5.2 RQ2：DRTP 能否泛化到未见拓扑条件？",2)
    para(doc,"结构留出 OOD 评估用于检验主结果是否仅限于训练期间的条件组合。A cohort 中，DRTP 在参数扰动和结构留出条件的 J 均值分别为 209.20 和 201.08，高于 UTR 的 157.49 和 178.31；B cohort 中，对应值分别为 202.82 和 191.34，高于 UTR 的 185.33 和 179.38。因而，DRTP 的中心回报优势没有仅局限于主评估条件，而是在所报告的两类冻结 OOD 条件下保留。")
    para(doc,"这一结果的边界同样需要明确。结构留出并不等于对任意通信失效模型、任意飞行平台或真实网络协议的泛化保证；它只说明在本文冻结的未见结构条件中，topology-aware exposure 所形成的策略具有可迁移的 cohort-level 回报趋势。安全相关指标并非在每个 cohort、每种 OOD 条件中完全同方向，因此本文不据此作出普适安全改进声明。")
    table(doc,["Cohort","条件","UTR J 均值","DRTP J 均值","差值（DRTP−UTR）"],[
        ["A","参数扰动","157.49","209.20","+51.71"],
        ["A","结构留出","178.31","201.08","+22.77"],
        ["B","参数扰动","185.33","202.82","+17.49"],
        ["B","结构留出","179.38","191.34","+11.96"],
    ],[1.5,3.0,3.0,3.0,3.2])
    cap(doc,"表4  固定 OOD 条件下的 cohort-level 回报。参数扰动与结构留出在训练结束后进行，不用于在线调参。")
    add_figure(doc,"Fig5_ood_generalization.png","图5  参数扰动与结构留出 OOD 条件的终点评估。该图置于 RQ2 后，说明拓扑感知训练暴露的收益并非只体现在训练内故障组合。")
    heading(doc,"5.3 RQ3：收益是否反映拓扑语义，而非通用优先级？",2)
    para(doc,"PLR-style 匹配比较用于排除一个直接替代解释：性能趋势是否仅由任意通用优先级机制引起。A cohort 中，DRTP 的扰动 J 均值为 216.66，高于 PLR-style 的 203.87；同时，DRTP 的平均超时率为 0.597，低于 PLR-style 的 0.742。B cohort 呈现不同的权衡：PLR-style 的扰动 J 均值为 220.03，高于 DRTP 的 210.34；但 DRTP 的平均成功率更高（0.397 对 0.301），且平均超时率更低（0.602 对 0.699）。")
    para(doc,"因此，本文不把 PLR-style 比较写成“DRTP 全面胜出”。更有信息量的结论是：通用优先级训练也能在部分 cohort 中产生较强回报，而 DRTP 在另一个 cohort 中取得更高回报并在 B cohort 呈现更有利的成功率—超时权衡。该结果与两种机制的不同归纳偏置一致：PLR-style 优先处理通用学习价值，而 DRTP 对预定义的拓扑退化语义和标称参照进行显式分配。待完成的 Random-DRTP 语义置换消融将以最小新增训练进一步检验这一解释。")
    table(doc,["Cohort","方法","J 均值","最低 J","J 的 SD","超时率","碰撞率","解释重点"],[
        ["A","DRTP","216.66","191.49","23.48","0.597","0.009","回报更高且超时更低"],
        ["A","PLR-style","203.87","142.02","36.12","0.742","0.014","通用优先级比较"],
        ["B","DRTP","210.34","172.03","30.54","0.602","0.000","成功率—超时权衡更优"],
        ["B","PLR-style","220.03","201.06","13.98","0.699","0.000","回报与低尾部更高"],
    ],[1.3,1.7,1.7,1.7,1.6,1.6,1.6,3.0])
    cap(doc,"表5  DRTP 与 PLR-style 的匹配外部比较（每个 cohort n=5）。该表强调 cohort-specific 的性能—任务完成权衡，而非建立全面支配关系。")
    heading(doc,"5.4 RQ4：DRTP 是否能扩展到更大规模 UAV 团队？",2)
    para(doc,"跨规模验证采用修复后的 6-UAV 正式协议：故障在 episode 完成前的固定 fault-step=3 注入，并已通过只读 timing validation 确认所有非标称组发生实际链路变化。旧 6-UAV 协议因故障时刻晚于 episode 结束、不产生有效故障注入，已被明确排除，不进入本文任何表格、图或结论。新的 UTR/DRTP 多 seed 训练使用固定预算和固定终点评估，目前正在完成正式终点数据。")
    para(doc,"该设计回答的不是“3-UAV 的数值能否直接外推至任意规模”，而是更可检验的问题：当团队规模、故障组和协同关系增加时，保持学习器和接口原则不变的 topology-aware exposure 是否仍能产生一致的鲁棒性趋势。正式结果返回后，本节将报告 mean、median、最低 seed、成功率、超时率与碰撞率，并与 3-UAV 的证据边界并列解释。")
    table(doc,["团队规模","方法","J 均值","J 中位数","最低 J","成功率","超时率","状态"],[
        ["6-UAV","UTR","[待固定终点评估]","[待填]","[待填]","[待填]","[待填]","修复后正式协议进行中"],
        ["6-UAV","DRTP","[待固定终点评估]","[待填]","[待填]","[待填]","[待填]","修复后正式协议进行中"],
    ],[1.6,1.7,2.0,2.0,1.7,1.7,1.7,3.2])
    cap(doc,"表6  6-UAV 跨规模验证的正式结果表。仅填入 fault-step=3 修复协议下的固定终点评估；旧的无有效故障注入结果永久排除。")
    add_figure(doc,"Fig7_cross_scale_placeholder.png","图6  6-UAV 跨规模验证的版式与协议边界。图置于 RQ4，用于强调仅使用修复后、故障实际发生的正式协议。终点评估返回后替换为 UTR/DRTP 的真实多 seed 结果。")
    heading(doc,"5.5 RQ5：DRTP 的机制与计算代价是什么？",2)
    para(doc,"DRTP 的机制证据由两个层面组成。第一，训练日志记录 q 从均匀初始化向非均匀暴露的自适应偏离，并保留 seed-dependent variation；这说明方法并非名义上的固定加权。第二，组级的相对标称性能退化、终点评估表现与终末暴露共同构成描述性 difficulty—exposure 分析，用于检验难度与暴露调整是否具有可解释对应。该分析不把难度视为决定性能的唯一原因，而将其作为训练分配合理性的观测证据。")
    para(doc,"为进一步区分两个核心成分，本文新增 Fixed-DRTP（保留拓扑语义但停止后续 q 更新）和 Random-DRTP（保留更新机制但随机置换难度—拓扑组映射）的独立 5-seed 消融。该消融不重跑已完成的 UTR 与 DRTP 主方法，避免以重复训练消耗预算。结果返回后将与主实验的冻结 UTR/DRTP endpoint 并列报告。运行开销也将在最终冻结源码、同一 GPU、同一并发和相同预算下测量 wall-clock 训练时间、sampler update 时间和峰值 GPU memory；在得到实测值之前，本文不使用“零开销”或“可忽略开销”等措辞。")
    table(doc,["方法","拓扑语义","自适应更新","J/任务指标","状态"],[
        ["UTR","否","否","见表3","已完成主实验"],
        ["Fixed-DRTP","是","否","[待独立终点评估]","进行中"],
        ["Random-DRTP","否（随机置换）","是","[待独立终点评估]","进行中"],
        ["DRTP","是","是","见表3","已完成主实验"],
    ],[2.5,2.6,2.4,3.6,3.2])
    cap(doc,"表7  机制消融设计。该表仅呈现冻结的实验结构，不以尚未完成的数值作出机制结论。")
    add_figure(doc,"Fig6_ablation_placeholder.png","图7  机制消融的论证设计。Fixed-DRTP 用于检验动态调整的增益，Random-DRTP 用于检验拓扑语义相对任意动态采样的贡献。正式数值仅在独立 5-seed 终点评估完成后填入。")


def add_discussion_conclusion(doc):
    heading(doc,"6 讨论",1)
    heading(doc,"6.1 从故障多样性到拓扑感知的鲁棒性塑造",2)
    para(doc,"本文的中心含义不是“困难条件应被无限次重采样”，而是训练暴露应尊重拓扑退化的结构语义。对协同策略而言，节点、上游/下游链路、交叉链路或中继关系的失效可能破坏不同的信息路径。均匀随机化保证每类条件都被看见，却不保证有限预算在相对困难、协同依赖更强的条件上产生足够学习压力。DRTP 通过相对标称难度和受约束 q 更新，把这一差异显式写入训练分布，从而把鲁棒性塑造为训练过程的一个可控对象。")
    heading(doc,"6.2 为什么通用优先级方法也可能有效",2)
    para(doc,"PLR-style 在 B cohort 中取得更高的扰动回报，这一观察说明“主动分配训练经历”本身是一个有价值的方向，而非只有拓扑语义才有作用。DRTP 的贡献在于提供了一个与任务结构对齐、可解释且受标称锚定约束的分配视角；它并不要求在每个 cohort、每个指标上取代所有通用优先级方法。A/B 的差异提示，两种机制可在不同学习轨迹下形成不同的回报、成功率与超时权衡。论文的合理主张因此是 competitive and topology-aware，而不是 universal dominance。")
    heading(doc,"6.3 seed variation、低尾部与证据解释",2)
    para(doc,"多智能体策略优化具有对初始化、rollout 和非平稳协同轨迹敏感的特征。本文通过独立 A/B cohort、固定 endpoint、完整 per-seed 汇总和低尾部指标来避免由单个最佳轨迹驱动结论。A cohort 中 DRTP 的低尾部改善尤其明显；B cohort 中中心趋势与最低 seed 均仍高于 UTR，但 seed 离散度并未在所有 cohort 中同时下降。因而，本文把 lower-tail behavior 作为重要但非唯一证据，并避免将方法表述为保证消除训练随机性。")
    heading(doc,"6.4 局限性与适用范围",2)
    para(doc,"本文的证据来自仿真环境中的预定义通信拓扑退化集合，尚未涉及实飞验证、真实无线网络协议的全部时延/丢包过程，或任意规模 UAV 系统。故障模型的组定义也决定了 DRTP 可利用的语义粒度；若任务中无法可靠定义可操作的拓扑条件库，需要重新评估这一方法是否适用。当前跨规模、语义消融与运行开销实验遵循冻结协议并仍在完成中，因此本文对跨规模迁移、语义因果性和轻量性只保留待实测支持的表述。")
    heading(doc,"7 结论",1)
    para(doc,"本文研究了通信拓扑退化如何在 UAV 多智能体协同中造成训练—部署信息结构偏移，并提出 DRTP 作为 topology-aware robustness training framework。DRTP 不改动 MAPPO 的 actor、critic、PPO 目标、奖励、观测、动作接口或环境转移，而是以相对标称的组级难度和受约束的自适应 q 更新，重塑训练阶段的拓扑条件暴露。两个独立 cohort 的固定终点评估显示，DRTP 相对均匀拓扑随机化在本文评估的拓扑退化设置下呈现重复的 cohort-level 回报与超时风险改善趋势；结构留出评估进一步支持这种训练暴露塑造在冻结 OOD 条件中的可迁移性。")
    para(doc,"与 PLR-style 的匹配比较表明，DRTP 的价值不应被概括为对通用优先级训练的全面替代，而应理解为一种把拓扑退化语义、标称参考和受约束暴露分配结合起来的鲁棒协同训练选择。完成中的语义消融、运行开销和修复后 6-UAV 验证将补齐机制、可行性与跨规模证据。总体而言，本文提供的不是对 UAV 鲁棒性的普适保证，而是一条可审计的训练原则：当故障改变多智能体的信息结构时，训练经历的分配本身应成为鲁棒协同设计的一部分。")
    heading(doc,"参考文献",1)
    refs=[
        "[1] Lowe R, Wu Y, Tamar A, et al. Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments. Advances in Neural Information Processing Systems, 2017.",
        "[2] Schulman J, Wolski F, Dhariwal P, et al. Proximal Policy Optimization Algorithms. arXiv preprint arXiv:1707.06347, 2017.",
        "[3] Yu C, Velu A, Vinitsky E, et al. The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games. Advances in Neural Information Processing Systems, 2022.",
        "[4] Jiang M, Grefenstette E, Rocktäschel T. Prioritized Level Replay. Proceedings of the 38th International Conference on Machine Learning, 2021.",
        "[5] Sukhbaatar S, Fergus R, et al. Learning Multiagent Communication with Backpropagation. Advances in Neural Information Processing Systems, 2016.",
        "[6] Jiang J, Dun C, Huang T, Lu Z. Graph Convolutional Reinforcement Learning. International Conference on Learning Representations, 2020.",
    ]
    for r in refs:
        p=doc.add_paragraph(); p.paragraph_format.first_line_indent=Cm(0); p.paragraph_format.left_indent=Cm(.3); p.paragraph_format.line_spacing=1.25; p.add_run(r)


def main():
    set_font(); fig1_motivation(); fig2_framework(); fig3_mechanism_layout(); fig4_main(); fig5_ood(); fig6_ablation_placeholder(); fig7_scale_placeholder()
    doc=setup_doc(); add_title(doc); add_introduction(doc); add_related_work(doc); add_problem_method(doc); add_experimental_setup(doc); add_results(doc); add_discussion_conclusion(doc)
    doc.core_properties.title="面向通信拓扑退化的多无人机协同鲁棒训练"
    doc.core_properties.subject="DRTP submission-ready Chinese manuscript"
    doc.core_properties.author=""
    doc.save(OUT)
    print(OUT)

if __name__ == "__main__": main()
