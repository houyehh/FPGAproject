import csv, warnings, matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
import numpy as np
plt.rcParams["font.family"]="Noto Sans CJK JP"
plt.rcParams["axes.unicode_minus"]=False
plt.rcParams["figure.dpi"]=170; plt.rcParams["savefig.bbox"]="tight"
warnings.simplefilter("error", UserWarning)
ROOT="."; OUT=ROOT+"/__figures/v11"

# ===== 附圖 5 §3.6 淨損益 3 規則 x 3 費率 =====
rows=list(csv.DictReader(open(ROOT+"/n2ew_era/16c_net_pnl_attribution/results/run1/cell_c_report_values.csv")))
fees=[("market_maker","造市者 254.68\n（TXF 不適用）"),("proprietary","期貨自營商 292\n（可得的最佳）"),("retail","散戶 372")]
rules=["back","proportional","front"]; rl={"back":"back（真下界）","proportional":"proportional","front":"front（真上界）"}
splits=["val","new3","new4"]; sl={"val":"驗證集","new3":"測試集 1","new4":"測試集 2"}
fig,axes=plt.subplots(1,3,figsize=(12.6,4.6),sharey=True)
rc={"back":"#34495e","proportional":"#7f8c8d","front":"#bdc3c7"}
for ax,(fk,fname) in zip(axes,fees):
    w=.26
    for j,ru in enumerate(rules):
        xs=np.arange(3)+(j-1)*w
        m=[];e=[];sg=[]
        for sp in splits:
            r=[x for x in rows if x["fee_scenario"]==fk and x["rule"]==ru and x["split"]==sp][0]
            m.append(float(r["session_mean_pnl_per_fill"])); e.append(float(r["se_clustered"]))
            sg.append(r["significantly_positive"]=="True")
        b=ax.bar(xs,m,w,yerr=e,capsize=2.5,color=rc[ru],ec="k",lw=.4,
                 error_kw=dict(lw=.8),label=rl[ru] if fk=="market_maker" else None)
        for x,v,s in zip(xs,m,sg):
            if s: ax.text(x,v+e[list(xs).index(x)]+3,"✓",ha="center",fontsize=9,color="#1e8449",fontweight="bold")
    ax.axhline(0,color="k",lw=1)
    ax.set_xticks(np.arange(3)); ax.set_xticklabels([sl[s] for s in splits],fontsize=9)
    ax.set_title(fname,fontsize=9.5); ax.grid(axis="y",alpha=.25,lw=.5)
axes[0].set_ylabel("淨損益（元／成交）\n各時段每成交損益的時段平均，誤差棒為時段聚類 SE")
axes[0].legend(fontsize=7.8,loc="lower left")
axes[0].set_ylim(-52,92)
fig.suptitle("附錄圖 A　絕對獲利同時受制於費率層級與撤單歸屬規則（✓ = 時段聚類 t 檢定顯著為正，雙尾 5%）",fontsize=10.5,y=1.03)
fig.text(.5,-.07,"部署模型、inventory cap 3、全部 16 個交易時段、連續處理不抽樣。df = 5／5／3，無零成交時段。\n"
  "唯一在真下界也顯著為正的費率層級（造市者）不適用於臺股期貨——臺灣期貨交易所造市者指定商品清單不含 TX／TXF。",
  ha="center",fontsize=7.6)
fig.savefig(OUT+"/fig5_net_pnl_grid.png")
print("A1 ok")
