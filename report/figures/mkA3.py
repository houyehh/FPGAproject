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

# ===== 附圖 6 §4.5 18 格改善 =====
rows=list(csv.DictReader(open(ROOT+"/n2ew_era/16a_front_cancel_endpoint/results/run4/model_robustness_18_cells.csv")))
fig,(a1,a2)=plt.subplots(1,2,figsize=(11.6,4.5))
order=sorted(rows,key=lambda r:float(r["mean_improvement"]))
y=np.arange(len(order))
cm={"back":"#34495e","proportional":"#7f8c8d","front":"#bdc3c7"}
a1.barh(y,[float(r["mean_improvement"]) for r in order],
        xerr=[float(r["se_clustered"]) for r in order],capsize=2,
        color=[cm[r["rule"]] for r in order],ec="k",lw=.4,error_kw=dict(lw=.7))
a1.set_yticks(y)
a1.set_yticklabels([f'{ {"back":"back","proportional":"prop","front":"front"}[r["rule"]] }／{ {"val":"驗證","new3":"測試1","new4":"測試2"}[r["split"]] }／'
                    f'{"不過濾" if r["config"]=="no_spread_filter" else "價差≥2"}' for r in order],fontsize=6.8)
a1.axvline(0,color="k",lw=1)
a1.set_xlabel("相對對稱報價的改善（元／成交）")
a1.set_title("(a) 18 個組態全部為正\n全距 +24.87 至 +75.28 元／成交",fontsize=10)
a1.grid(axis="x",alpha=.25,lw=.5)
t=[float(r["t"]) for r in order]; cv=[float(r["critical"]) for r in order]
a2.barh(y,t,color=[cm[r["rule"]] for r in order],ec="k",lw=.4)
a2.plot(cv,y,"d",color="#c0392b",ms=4.5,label="雙尾 5% 臨界值（df = 5 或 3）")
a2.set_yticks(y); a2.set_yticklabels([])
a2.set_xlabel("時段聚類 t 值（無單位）")
a2.set_title("(b) 18 個組態全部顯著\n最小 t = 3.51（front／驗證集／價差≥2）；不過濾最小 6.55",fontsize=10)
a2.grid(axis="x",alpha=.25,lw=.5); a2.legend(fontsize=8,loc="lower right")
fig.legend(handles=[Patch(fc=cm[k],label=v) for k,v in
           [("back","back（真下界）"),("proportional","proportional"),("front","front（真上界）")]],
           fontsize=8,loc="upper center",ncol=3,bbox_to_anchor=(.5,1.09))
fig.suptitle("附錄圖 B　兩個設定共 18 個組態的改善（正文以「不過濾」為準；「價差≥2」為穩健性檢查）",
             fontsize=10.5,y=1.145)
fig.savefig(OUT+"/figA3_improvement_18cells.png"); plt.close(fig)
print("A3 ok")
