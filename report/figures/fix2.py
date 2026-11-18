import warnings, matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
plt.rcParams["font.family"]="Noto Sans CJK JP"; plt.rcParams["axes.unicode_minus"]=False
plt.rcParams["figure.dpi"]=170; plt.rcParams["savefig.bbox"]="tight"
warnings.simplefilter("error", UserWarning)
OUT="./__figures/v11"

stages=[("起點\ndense 遞迴\nunroll16 + dataflow",2236,"a"),("對角化遞迴",530,"a"),
        ("頂層 pipeline\nII = 1",146,"i"),("inverse sqrt\n→ 65 點 PWL LUT",75,"i"),
        ("並行 variance",59,"i"),("LUT → BRAM\n直接索引",49,"i")]
fig,ax=plt.subplots(figsize=(9.0,5.2))
xs=np.arange(len(stages)); ys=[s[1] for s in stages]
C={"a":"#c0392b","i":"#2471a3"}
ax.bar(xs,ys,color=[C[s[2]] for s in stages],width=.6,zorder=3)
for x,y in zip(xs,ys): ax.text(x,y*1.11,f"{y}",ha="center",fontsize=9.5,fontweight="bold",zorder=4)
ax.set_yscale("log"); ax.set_ylim(30,22000)
ax.set_xticks(xs); ax.set_xticklabels([s[0] for s in stages],fontsize=7.8)
ax.set_ylabel("單次推論延遲（cycles，對數刻度）\n@ 100 MHz，1 cycle = 10 ns")
ax.set_title("加速路徑：架構層 4.22 倍 × 實作層 10.82 倍 = 45.63 倍",fontsize=11)
ax.grid(axis="y",alpha=.25,lw=.5,zorder=0)

def bracket(x0,x1,y,txt,color,fs=8.6,bold=False):
    ax.annotate("",xy=(x1,y),xytext=(x0,y),
                arrowprops=dict(arrowstyle="<->",color=color,lw=1.6,shrinkA=0,shrinkB=0),zorder=5)
    ax.plot([x0,x0],[y*.86,y*1.16],color=color,lw=1.6,zorder=5)
    ax.plot([x1,x1],[y*.86,y*1.16],color=color,lw=1.6,zorder=5)
    ax.text((x0+x1)/2,y*1.30,txt,ha="center",va="bottom",fontsize=fs,color=color,
            fontweight="bold" if bold else "normal",zorder=6,
            bbox=dict(fc="white",ec="none",pad=1.5))

bracket(0,1,5200,"架構層 4.22×",C["a"],fs=9.4,bold=True)
bracket(1,5,310,"實作層 10.82×（六項主要改動）",C["i"],fs=9.4,bold=True)
ax.legend(handles=[Patch(fc=C["a"],label="架構層：改變模型數學"),
                   Patch(fc=C["i"],label="實作層：不改變模型數學")],
          fontsize=8.4,loc="upper right",framealpha=.96)
fig.text(.5,-.085,"縱軸為推論核心本身的延遲，不含行情解碼、特徵萃取與訂單產生。"
  "75 → 59 之間另有數次排程與時序餘裕的小幅調整，未逐一列出。",ha="center",fontsize=7.6)
fig.savefig(OUT+"/figA4_acceleration_ladder.png"); plt.close(fig)
print("ok")
