import csv, warnings, matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
import matplotlib.pyplot as plt
plt.rcParams["font.family"]="Noto Sans CJK JP"; plt.rcParams["axes.unicode_minus"]=False
plt.rcParams["figure.dpi"]=170; plt.rcParams["savefig.bbox"]="tight"
warnings.simplefilter("error", UserWarning)
ROOT="."; OUT=ROOT+"/__figures/v11"

D={}
for s in (0,1,2):
    r=list(csv.DictReader(open(f"{ROOT}/n2ew_era/11b_toxicity_objective_retrain_v2/results/run1/stage2/training_curve_seed{s}.csv")))
    D[s]=([int(x["epoch"]) for x in r],[float(x["val_mse_normalized"]) for x in r],
          int(r[-1]["best_epoch"]),float(r[-1]["best_val_mse"]),int(r[-1]["epoch"]))
cols={0:"#1f77b4",1:"#d62728",2:"#2ca02c"}
fig,(a1,a2)=plt.subplots(1,2,figsize=(11.4,4.3))
for s in (0,1,2):
    ep,va,be,bv,last=D[s]
    a1.plot(ep,va,color=cols[s],lw=.9,label=f"seed {s}：best epoch {be}，第 {last} 輪 early stop")
    a1.plot([be],[bv],"o",color=cols[s],ms=5.5,mec="k",mew=.6,zorder=5)
a1.set_xlabel("訓練輪數 epoch（單位：輪）")
a1.set_ylabel("驗證集 MSE（標準化標籤上，無單位，越小越好）")
a1.set_title("(a) 全程",fontsize=10)
a1.set_ylim(.515,.58); a1.grid(alpha=.25,lw=.5); a1.legend(fontsize=7.6,loc="upper right")

for s in (0,1,2):
    ep,va,be,bv,last=D[s]
    a2.plot(ep,va,color=cols[s],lw=1.0)
    a2.plot([be],[bv],"o",color=cols[s],ms=6,mec="k",mew=.6,zorder=5)
    a2.axvline(last,color=cols[s],lw=.7,ls=":")
a2.set_xlim(100,490); a2.set_ylim(.5198,.5245)
a2.set_xlabel("訓練輪數 epoch（單位：輪）")
a2.set_title("(b) 放大：第 100 輪之後（縱軸範圍 0.0047）",fontsize=10)
a2.grid(alpha=.25,lw=.5)
a2.text(.03,.93,"● = best checkpoint　　虛線 = early stopping 觸發點\n三個 seed 的最終 best val MSE 相差 0.0015（0.29%）",
        transform=a2.transAxes,fontsize=7.4,va="top",bbox=dict(fc="white",ec="0.75",lw=.5,pad=3))
fig.suptitle("部署模型族的收斂曲線（186 參數，h = 8，三個 seed）",fontsize=11,y=1.01)
fig.text(.5,-.07,"後續所有評估皆使用各 seed 的 best checkpoint。三個 seed 皆因 early stopping 觸發而結束"
  "（patience 20，cosine annealing 週期 500 輪，初始學習率 1e-3 退火至 1e-5）。",ha="center",fontsize=7.6)
fig.savefig(OUT+"/figA2_convergence.png"); plt.close(fig)
print("ok")
