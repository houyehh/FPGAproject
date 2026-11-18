import warnings, matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Patch
import numpy as np
plt.rcParams["font.family"]="Noto Sans CJK JP"; plt.rcParams["axes.unicode_minus"]=False
plt.rcParams["figure.dpi"]=170; plt.rcParams["savefig.bbox"]="tight"
warnings.simplefilter("error", UserWarning)
OUT="./__figures/v11"

# ===== 附圖 7：核心架構與各段 state 佔用 =====
blocks=[("前級線性\nW·x + b",12,"#95a5a6"),("LayerNorm\n(variance→LUT→scale)",25,"#e74c3c"),
        ("activation\n+ gating",9,"#95a5a6"),("對角遞迴\ns ← a⊙s + …",8,"#2471a3"),
        ("輸出線性\n+ 門檻摺疊",9,"#95a5a6")]
total=sum(b[1] for b in blocks)
fig,ax=plt.subplots(figsize=(11.2,3.5))
x=0.0; H=1.0
for name,n,c in blocks:
    w=n/total
    ax.add_patch(FancyBboxPatch((x+.004,0),w-.008,H,boxstyle="round,pad=0,rounding_size=.012",
                                fc=c,ec="k",lw=.7))
    ax.text(x+w/2,H*.60,name,ha="center",va="center",fontsize=8.6,color="white",fontweight="bold")
    ax.text(x+w/2,H*.22,f"{n} states",ha="center",va="center",fontsize=9.5,color="white",fontweight="bold")
    x+=w
rx0=sum(b[1] for b in blocks[:3])/total; rx1=sum(b[1] for b in blocks[:4])/total
TOP=H*1.26
ax.plot([rx1-.012,rx1-.012,rx0+.012],[H,TOP,TOP],color="#2471a3",lw=1.6,solid_capstyle="round")
ax.add_patch(FancyArrowPatch((rx0+.012,TOP),(rx0+.012,H*1.01),arrowstyle="-|>",
                             mutation_scale=13,color="#2471a3",lw=1.6))
ax.text((rx0+rx1)/2,H*1.33,"狀態回授（loop-carried dependency）\n下一個事件需等本事件算完",
        ha="center",fontsize=8,color="#2471a3")
ax.annotate("",xy=(0,-.14),xytext=(-.035,-.14),arrowprops=dict(arrowstyle="-|>",mutation_scale=12,color="k",lw=1.2))
ax.text(-.045,-.14,"事件 t\n16 項特徵",ha="right",va="center",fontsize=8)
ax.annotate("",xy=(1.035,-.14),xytext=(1.0,-.14),arrowprops=dict(arrowstyle="-|>",mutation_scale=12,color="k",lw=1.2))
ax.text(1.045,-.14,"2 個分數\n→ 符號檢查\n→ 買賣兩側掛／撤",ha="left",va="center",fontsize=8)
ax.set_xlim(-.22,1.26); ax.set_ylim(-.40,1.66); ax.axis("off")
ax.set_title("推論核心的區塊與各區塊的 scheduling state 佔用（區塊寬度正比於 state 數）",fontsize=10.5)
ax.text(.5,-.12,"區塊內數字為該區塊的 scheduling state 數；各區塊跨度重疊，故不可加總——核心總延遲為 49 cycles（490 ns @ 100 MHz）。\n"
   "LayerNorm（紅）佔 25 個，為對角遞迴（藍）8 個的 3.1 倍：拖慢核心的不是遞迴。",
   ha="center",va="top",fontsize=7.6,transform=ax.transAxes)
fig.savefig(OUT+"/figA5_core_architecture.png"); plt.close(fig)

# ===== 附圖 8：三個對照 =====
fig,axes=plt.subplots(1,3,figsize=(12.4,4.3))
# 對照一
a=axes[0]
v=[23.074,14.188]; v2=[22.292,15.219]; v3=[19.503,9.857]
X=np.arange(3); w=.36
a.bar(X-w/2,[23.074,22.292,19.503],w,color="#2471a3",ec="k",lw=.4,label="對角遞迴（186 參數）")
a.bar(X+w/2,[14.188,15.219,9.857],w,color="#95a5a6",ec="k",lw=.4,label="無歷史前饋（163 參數）")
a.set_xticks(X); a.set_xticklabels(["驗證集","測試集 1","測試集 2"],fontsize=8.5)
a.set_ylabel("每成交 maker P&L（元／成交）")
a.set_title("對照一　對無歷史前饋\n差 +7.1～+9.6 元，未達顯著",fontsize=9.5)
a.legend(fontsize=7.4); a.grid(axis="y",alpha=.25,lw=.5); a.set_ylim(0,28)
a.text(.5,.03,"t = 2.50 ／ 2.11 ／ −0.16（臨界 2.57／2.57／3.18）",transform=a.transAxes,
       ha="center",fontsize=7,bbox=dict(fc="white",ec="0.8",lw=.4,pad=2))
# 對照二
b=axes[1]
b.bar(X-w/2,[23.07,22.29,19.50],w,color="#2471a3",ec="k",lw=.4,label="對角遞迴（186 參數）")
b.bar(X+w/2,[4.83,7.47,0.27],w,color="#c0392b",ec="k",lw=.4,label="等預算 TCN（設計 A）")
for i,(t,sig) in enumerate(zip([-4.75,-3.81,-1.63],[True,True,False])):
    b.text(i,24.5,("✓ t = %.2f" if sig else "t = %.2f")%t,ha="center",fontsize=7.4,
           color="#1e8449" if sig else "0.4",fontweight="bold" if sig else "normal")
b.set_xticks(X); b.set_xticklabels(["驗證集","測試集 1","測試集 2"],fontsize=8.5)
b.set_title("對照二　對等預算視窗模型\n遞迴勝 16～19 元，2/3 顯著",fontsize=9.5)
b.legend(fontsize=7.4,loc="center right"); b.grid(axis="y",alpha=.25,lw=.5); b.set_ylim(0,28)
b.text(.5,.03,"且三個 TCN 設計無一裝得進元件（LUT 601%～1,266%）",transform=b.transAxes,
       ha="center",fontsize=7,bbox=dict(fc="white",ec="0.8",lw=.4,pad=2))
# 對照三
c=axes[2]
X3=np.arange(3)
c.bar(X3-w/2,[44.53,64.02,63.80],w,color="#2471a3",ec="k",lw=.4,label="遞迴")
c.bar(X3+w/2,[40.66,63.95,71.23],w,color="#c0392b",ec="k",lw=.4,label="TCN")
c.set_xticks(X3); c.set_xticklabels(["208／226 參數\n(state 3)","2,132／2,344 參數\n(state 16)","23,876／23,301 參數\n(state 64)"],fontsize=7.2)
c.set_ylabel("macro-F1（%）")
c.set_title("對照三　FI-2010 公開基準\n大容量階 TCN 明顯勝出",fontsize=9.5)
c.legend(fontsize=7.4,loc="upper left"); c.grid(axis="y",alpha=.25,lw=.5); c.set_ylim(35,80)
c.annotate("t = −10.05",xy=(2,74),ha="center",fontsize=7.8,color="#c0392b",fontweight="bold")
c.text(.5,.03,"每個樣本為獨立的 100 事件視窗，遞迴狀態每樣本歸零",transform=c.transAxes,
       ha="center",fontsize=7,bbox=dict(fc="white",ec="0.8",lw=.4,pad=2))
fig.suptitle("遞迴的優勢是條件性的：硬體預算小、且歷史須沿事件流累積時成立；兩者皆不成立時 TCN 勝出",
             fontsize=10.5,y=1.02)
fig.savefig(OUT+"/figA7_three_comparisons.png"); plt.close(fig)
print("7,8 ok")
