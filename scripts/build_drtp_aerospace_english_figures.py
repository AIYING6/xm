"""Render English-only submission figures from frozen DRTP evidence data.

This is a presentation adapter: it reads the fixed source-data CSV/JSON products
and writes English-labelled PNGs.  It does not run evaluation, alter results, or
choose checkpoints.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "paper" / "q2_final_zh" / "formal_results" / "source_data"
OUT = ROOT / "paper" / "q2_final_en" / "submission_figures"
BLUE, GREY, RED, GREEN, PURPLE = "#2563eb", "#6b7280", "#dc2626", "#16a34a", "#7c3aed"
SEEDS = (2301, 2302, 2303, 2304, 2305)
CONDITIONS = ("timing_28_80", "timing_36_80", "timing_52_80", "timing_60_80", "duration_44_40", "duration_44_60", "duration_44_100", "duration_44_120", "compound_28_120", "compound_60_120")
SHORT = {"timing_28_80":"T28", "timing_36_80":"T36", "timing_52_80":"T52", "timing_60_80":"T60", "duration_44_40":"D40", "duration_44_60":"D60", "duration_44_100":"D100", "duration_44_120":"D120", "compound_28_120":"C28/120", "compound_60_120":"C60/120"}


def rows(name: str):
    with (DATA / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=600, bbox_inches="tight")
    plt.close(fig)


def box(ax, xywh, text, color="#f3f4f6", fs=7):
    x,y,w,h=xywh
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.02,rounding_size=0.025",facecolor=color,edgecolor="#9ca3af",linewidth=.8))
    ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=fs)


def arrow(ax, p1, p2, color):
    ax.add_patch(FancyArrowPatch(p1,p2,arrowstyle="-|>",mutation_scale=12,linewidth=1.5,color=color))


def concepts():
    fig,axs=plt.subplots(1,4,figsize=(7.2,2.25))
    titles=["(a) Roles and legal relations", "(b) Before relay failure", "(c) During relay failure", "(d) Information boundary"]
    for a,t in zip(axs,titles): a.set(xlim=(0,1),ylim=(0,1));a.axis("off");a.set_title(t,fontweight="bold",fontsize=8)
    a=axs[0]
    for x,label,c,role in ((.18,"S",BLUE,"Scout"),(.50,"R",PURPLE,"Relay"),(.82,"A",RED,"Attacker"),(.50,"T",GREEN,"Target")):
        a.scatter(x,.57 if label!="T" else .18,s=430,color=c,edgecolor="white",zorder=3);a.text(x,.57 if label!="T" else .18,label,color="white",ha="center",va="center",fontsize=7,fontweight="bold");a.text(x,.41 if label!="T" else .06,role,ha="center",fontsize=6)
    arrow(a,(.25,.57),(.43,.57),BLUE);arrow(a,(.57,.57),(.75,.57),PURPLE);arrow(a,(.22,.52),(.45,.23),GREEN);a.text(.5,.88,"Policy observes only legal current information",ha="center",fontsize=6.4)
    a=axs[1]
    box(a,(.10,.64,.80,.17),"Scout → Relay → Attacker\nlegal cached-information path","#eff6ff");box(a,(.10,.30,.80,.17),"Nominal / pre-failure","#f3f4f6")
    a=axs[2]
    box(a,(.10,.64,.80,.17),"Relay-mediated edges unavailable","#fee2e2");box(a,(.10,.30,.80,.17),"Legal direct Scout → Attacker path\nwhen physical conditions permit","#ecfdf5")
    a=axs[3]
    box(a,(.10,.62,.80,.16),"F0: onset 44; duration 80","#fee2e2");box(a,(.10,.38,.80,.16),"Training groups: N + F0 / TE / TL / DS / DL / CP","#eff6ff",6);box(a,(.10,.14,.80,.16),"Excluded: failure labels, future links, simulator truth","#f3f4f6",6)
    fig.suptitle("Relay-node failure as legal topology/path reconfiguration",y=1.03,fontsize=10,fontweight="bold");fig.tight_layout();save(fig,"fig1_relay_failure_topology_reconfiguration.png")
    fig,axs=plt.subplots(1,4,figsize=(7.2,2.25));titles=["(a) Shared backbone", "(b) UTR", "(c) DRTP", "(d) Controlled contrast"]
    for a,t in zip(axs,titles):a.set(xlim=(0,1),ylim=(0,1));a.axis("off");a.set_title(t,fontweight="bold",fontsize=8)
    for txt,y,c in (("Single-Graph actor + CTDE critic\n116,728 parameters; same PPO",.65,"#eff6ff"),("50% nominal anchor N",.40,"#ecfdf5"),("50% perturbation: F0, TE, TL, DS, DL, CP",.15,"#fff7ed")):box(axs[0],(.13,y,.74,.16),txt,c)
    for txt,y,c in (("N: fixed 0.50",.69,"#ecfdf5"),("Perturbation mass: 0.50",.45,"#fff7ed"),("Uniform q = 1/6\nTotal group probability = 1/12",.18,"#eff6ff")):box(axs[1],(.15,y,.70,.15 if y>.2 else .17),txt,c)
    for txt,y,c in (("N: fixed 0.50",.74,"#ecfdf5"),("Group returns → EMA → relative difficulty",.53,"#f5f3ff"),("Exponentiated update + smoothing + bounded simplex",.31,"#f5f3ff"),("q(k) ∈ [0.05, 0.35]; training only",.09,"#fff7ed")):box(axs[2],(.12,y,.76,.13),txt,c,6.1)
    for txt,y,c in (("Same network, PPO, reward, environment, budget and tape",.69,"#f3f4f6"),("Only difference: fixed uniform q vs bounded adaptive q",.43,"#dbeafe"),("Same execution-time inputs; no adaptive sampler",.17,"#fefce8")):box(axs[3],(.10,y,.80,.15),txt,c,6.1)
    fig.suptitle("UTR–DRTP training-distribution contrast",y=1.03,fontsize=10,fontweight="bold");fig.tight_layout();save(fig,"fig2_utr_drtp_training_distribution.png")


def data_figures():
    decision=json.loads((DATA/"DRTP_UTR_Q2_FORMAL_DECISION.json").read_text(encoding="utf-8")); paired=decision["paired_rows"]; cells=rows("per_seed_condition_summary.csv")
    lookup={(r["arm"],int(r["seed"]),r["condition"]):float(r["J"]) for r in cells}
    endpoints=[("J_nominal","Nominal J"),("J_F0","F0 J"),("J_OOD_mean","Mean perturbation J"),("J_OOD_worst","Worst perturbation J")]
    fig,axes=plt.subplots(1,4,figsize=(7.2,2.25))
    for ax,(key,label) in zip(axes,endpoints):
        for s in SEEDS:
            if key=="J_nominal": v=[lookup[(a,s,"nominal")] for a in ("utr_sg","drtp_sg")]
            elif key=="J_F0": v=[lookup[(a,s,"f0_seen_44_80")] for a in ("utr_sg","drtp_sg")]
            else:
                v=[]
                for a in ("utr_sg","drtp_sg"):
                    z=[lookup[(a,s,c)] for c in CONDITIONS];v.append(np.mean(z) if key.endswith("mean") else np.min(z))
            ax.plot([0,1],v,color="#9ca3af",lw=.8);ax.scatter([0,1],v,s=15,color=[GREY,BLUE])
        pooled=[decision["pooled"][a][key] for a in ("utr_sg","drtp_sg")];ax.scatter([0,1],pooled,marker="D",s=28,color=[GREY,BLUE],zorder=3)
        stat=decision["paired_summaries"][key];ax.set_title(label,fontweight="bold",fontsize=8);ax.set_xticks([0,1],["UTR","DRTP"]);ax.grid(axis="y",ls=":",alpha=.6);ax.text(.5,.96,f"mean Δ={stat['mean']:.1f}; {stat['wins']}/5",ha="center",va="top",transform=ax.transAxes,fontsize=6)
    axes[0].set_ylabel("Mission score");fig.suptitle("Formal paired five-seed comparison at 10M",y=1.03,fontsize=10,fontweight="bold");fig.tight_layout();save(fig,"fig3_formal_primary_performance.png")
    fig,ax=plt.subplots(figsize=(7.2,2.7));d=[];wins=[]
    for c in CONDITIONS:
        x=[lookup[("drtp_sg",s,c)]-lookup[("utr_sg",s,c)] for s in SEEDS];d.append(np.mean(x));wins.append(sum(v>0 for v in x))
    bars=ax.bar(range(10),d,color=BLUE);ax.axhline(0,color="#374151",lw=.8);ax.set_xticks(range(10),[SHORT[c] for c in CONDITIONS],rotation=35,ha="right");ax.set_ylabel("Paired ΔJ (DRTP − UTR)");ax.set_title("Formal condition-wise perturbation decomposition",fontweight="bold");ax.grid(axis="y",ls=":",alpha=.6)
    for b,v,w in zip(bars,d,wins):ax.text(b.get_x()+b.get_width()/2,v+1.5,f"{v:.1f}\n{w}/5",ha="center",fontsize=6)
    fig.tight_layout();save(fig,"fig4_ood_condition_decomposition.png")
    fig,axs=plt.subplots(1,2,figsize=(7.2,2.55),gridspec_kw={"width_ratios":[1.25,1]});x=np.arange(5);width=.24
    for off,(field,name) in zip((-width,0,width),(("delta_J_F0","F0"),("delta_J_OOD_mean","Mean perturbation"),("delta_J_OOD_worst","Worst perturbation"))):axs[0].bar(x+off,[r[field] for r in paired],width,label=name)
    axs[0].axhline(0,color="#374151",lw=.8);axs[0].set_xticks(x,[str(s) for s in SEEDS]);axs[0].set_xlabel("Training seed");axs[0].set_ylabel("Paired ΔJ (DRTP − UTR)");axs[0].set_title("All retained seed-level effects",fontweight="bold",fontsize=8);axs[0].legend(fontsize=5.8);axs[0].grid(axis="y",ls=":",alpha=.6)
    p=decision["pooled"];labels=["Collision","Timeout","Constraint\nviolation"];axs[1].bar(np.arange(3)-.18,[p["utr_sg"][k] for k in ("collision_failure_mean","timeout_failure_mean","constraint_failure_mean")],.36,color=GREY,label="UTR");axs[1].bar(np.arange(3)+.18,[p["drtp_sg"][k] for k in ("collision_failure_mean","timeout_failure_mean","constraint_failure_mean")],.36,color=BLUE,label="DRTP");axs[1].set_xticks(np.arange(3),labels,rotation=18,ha="right");axs[1].set_ylim(0,1);axs[1].set_ylabel("Failure-condition rate");axs[1].set_title("Safety outcomes",fontweight="bold",fontsize=8);axs[1].legend(fontsize=6);axs[1].grid(axis="y",ls=":",alpha=.6)
    fig.suptitle("Formal reliability and safety boundary",y=1.03,fontsize=10,fontweight="bold");fig.tight_layout();save(fig,"fig5_seed_reliability_and_safety.png")
    sampler=json.loads((DATA/"sampler_telemetry_summary.json").read_text(encoding="utf-8")); groups=list(sampler["final_q_mean"]); means=[sampler["final_q_mean"][g] for g in groups]; sd=[sampler["final_q_sample_sd"][g] for g in groups]
    fig,ax=plt.subplots(figsize=(7.2,2.7));ax.bar(groups,means,yerr=sd,capsize=3,color=[BLUE,PURPLE,"#0891b2","#d97706",GREEN,RED]);ax.axhline(1/6,color=GREY,ls="--",lw=1,label="UTR uniform q = 1/6");ax.set_ylim(0,.42);ax.set_ylabel("Final adaptive group weight q\n(mean ± seed SD)");ax.set_xlabel("Perturbation/topology group");ax.set_title("DRTP sampler telemetry at the frozen 10M checkpoint",fontweight="bold");ax.grid(axis="y",ls=":",alpha=.6);ax.legend(fontsize=7);fig.tight_layout();save(fig,"fig6_adaptive_weight_telemetry.png")
    monitor=rows("formal_training_monitor_binned.csv");fig,axs=plt.subplots(1,2,figsize=(7.2,2.3))
    for ax,metric,title in zip(axs,("train_avg_reward","approx_kl"),("Training rollout reward (diagnostic only)","Approximate PPO KL")):
        for arm,col,name in (("utr_sg",GREY,"UTR"),("drtp_sg",BLUE,"DRTP")):
            series=[]
            for s in SEEDS:
                rr=[r for r in monitor if r["method"]==arm and int(r["train_seed"])==s];xx=[float(r["environment_steps_million"]) for r in rr];yy=np.array([float(r[metric]) for r in rr]);series.append(yy);ax.plot(xx,yy,color=col,alpha=.14,lw=.55)
            y=np.vstack(series);ax.plot(xx,y.mean(0),color=col,lw=1.4,label=name);ax.fill_between(xx,y.min(0),y.max(0),color=col,alpha=.1)
        ax.set_title(title,fontweight="bold",fontsize=8);ax.set_xlabel("Training environment steps (millions)");ax.grid(axis="y",ls=":",alpha=.6)
    axs[0].set_ylabel("Mean batch reward");axs[0].legend(fontsize=6);axs[1].set_ylabel("KL");fig.suptitle("Training diagnostics; not used for checkpoint selection",y=1.03,fontsize=10,fontweight="bold");fig.tight_layout();save(fig,"figS1_training_diagnostics.png")
    # A concise English terminal-outcome view is sufficient for Fig. 7.
    terminal=rows("formal_terminal_outcomes_by_seed_family.csv");families=["正常工况","F0","时机扰动","持续时间扰动","复合扰动"];labels=["Nominal","F0","Timing","Duration","Compound"]
    fig,axes=plt.subplots(1,3,figsize=(7.2,2.35));
    for ax,(metric,title,ylim) in zip(axes,(("success_at_horizon","Completion rate",(0,.4)),("timeout","Timeout rate",(0,1)),("collision","Collision rate",(0,.045)))):
        for i,f in enumerate(families):
            for arm,off,col in (("utr_sg",-.16,GREY),("drtp_sg",.16,BLUE)):
                vals=[float(r[metric]) for r in terminal if r["method"]==arm and r["family"]==f];ax.scatter([i+off]*len(vals),vals,s=10,color=col,alpha=.85);ax.scatter(i+off,np.mean(vals),s=28,marker="D",color=col)
        ax.set_title(title,fontweight="bold",fontsize=8);ax.set_xticks(range(5),labels,rotation=25,ha="right");ax.set_ylim(*ylim);ax.grid(axis="y",ls=":",alpha=.6)
    axes[0].set_ylabel("Rate");fig.suptitle("Formal terminal outcomes",y=1.03,fontsize=10,fontweight="bold");fig.tight_layout();save(fig,"fig7_formal_terminal_outcomes.png")


def main():
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":7,"axes.spines.right":False,"axes.spines.top":False})
    concepts();data_figures();print(f"PASS: English presentation figures at {OUT}")

if __name__=="__main__":main()
