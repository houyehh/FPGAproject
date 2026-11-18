import csv, warnings, matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
plt.rcParams["font.family"]="Noto Sans CJK JP"; plt.rcParams["axes.unicode_minus"]=False
plt.rcParams["figure.dpi"]=170; plt.rcParams["savefig.bbox"]="tight"
warnings.simplefilter("error", UserWarning)
ROOT="."; OUT=ROOT+"/__figures/v11"
rows=list(csv.DictReader(open(ROOT+"/n2ew_era/14e_tcn_resource_sharing/final/sweep_results_consolidated.csv")))

fig,ax=plt.subplots(figsize=(8.2,5.6))
ax.add_patch(Rectangle((0,1e4),220,53200-1e4,fc="#2ecc71",alpha=.13,ec="#27ae60",lw=1.4,ls="--",zorder=0))
ax.text(110,36000,"可行區\nDSP ≤ 220 且 LUT ≤ 53,200",ha="center",fontsize=9.5,color="#1e8449",fontweight="bold")
ax.scatter([int(r["dsp"]) for r in rows],[int(r["lut"]) for r in rows],
           s=54,c="#c0392b",ec="k",lw=.5,zorder=4,label="等預算 TCN 設計 A 的 13 個 sharing 組態")
ann={"baseline_14c":("基準組態：56 cycles、DSP 176\nLUT 482,926（元件容量的 908%）\n唯一具實際任務表現者",(14,-6)),
     "ii8_relaxed_cyclic2_fabric":("全移 LUT fabric：DSP 僅 12\n但 LUT 141,610（266%）",(14,4)),
     "ii8_relaxed_cyclic2_dsp":("LUT 最低 42,723（80.3%）\n但 DSP 286 > 220",(-120,-42)),
     "ii32_fabric_last3":("DSP 203 ≤ 220\n但 LUT 65,122（122%）",(12,10))}
for r in rows:
    if r["point"] in ann:
        lab,off=ann[r["point"]]
        ax.annotate(lab,(int(r["dsp"]),int(r["lut"])),textcoords="offset points",xytext=off,
                    fontsize=7.4,arrowprops=dict(arrowstyle="-",lw=.6,color="0.4"))
ax.scatter([176],[19177],s=230,marker="*",c="#2471a3",ec="k",lw=.8,zorder=5,
           label="本專題遞迴核心：49 cycles、DSP 176、LUT 19,177")
ax.annotate("同樣 176 顆 DSP，\nLUT 相差 25.2 倍",(176,19177),textcoords="offset points",
            xytext=(-128,10),fontsize=7.8,color="#2471a3",fontweight="bold")
ax.axvline(220,color="#27ae60",lw=1,ls=":"); ax.axhline(53200,color="#27ae60",lw=1,ls=":")
ax.set_yscale("log"); ax.set_xlim(0,320); ax.set_ylim(1.4e4,9e5)
ax.set_xlabel("DSP48E1 使用量（顆；元件上限 220）")
ax.set_ylabel("LUT-as-logic 使用量（個，對數刻度；元件上限 53,200）")
ax.set_title("等預算 TCN 的 resource sharing 掃描：13 個組態全部落在可行區外",fontsize=10.5)
ax.grid(alpha=.22,lw=.5); ax.legend(fontsize=8,loc="upper left",framealpha=.95)
fig.text(.5,-.045,"把乘法由 DSP 移往 LUT fabric 時，DSP 下降的速率低於 LUT 上升的速率，故在 DSP 進入預算之前\n"
  "LUT 已越界——交換曲線整條通過可行區之外。最接近可行的點為 5,454 cycles，即遞迴核心的 111 倍。",
  ha="center",fontsize=7.6)
fig.savefig(OUT+"/figA6_tcn_feasibility.png"); plt.close(fig)
print("ok")
