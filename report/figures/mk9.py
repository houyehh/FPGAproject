import warnings, matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
plt.rcParams["font.family"]="Noto Sans CJK JP"; plt.rcParams["axes.unicode_minus"]=False
plt.rcParams["figure.dpi"]=170; plt.rcParams["savefig.bbox"]="tight"
warnings.simplefilter("error", UserWarning)
OUT="./__figures/v11"

fig=plt.figure(figsize=(11.4,7.0))
gs=fig.add_gridspec(2,1,height_ratios=[1.05,1.0],hspace=.34)

# ---------- (a) 資料流 ----------
ax=fig.add_subplot(gs[0]); ax.axis("off"); ax.set_xlim(0,1); ax.set_ylim(0,1)
def box(x,y,w,h,t,fc,fs=8.2,tc="white",bold=True):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0,rounding_size=.012",fc=fc,ec="k",lw=.7))
    ax.text(x+w/2,y+h/2,t,ha="center",va="center",fontsize=fs,color=tc,
            fontweight="bold" if bold else "normal")
def arrow(x0,x1,y):
    ax.add_patch(FancyArrowPatch((x0,y),(x1,y),arrowstyle="-|>",mutation_scale=12,color="k",lw=1.2))

ax.text(.5,1.0,"(a) 每一個委託簿事件的資料流",ha="center",fontsize=10,fontweight="bold")
feat=("13 項原始欄位\n\n"
      "簿狀態 6：價差、兩側量、\n深度、兩個不平衡\n"
      "簿的變化 2　價格衍生 2\n事件強度與時序 3")
box(.005,.16,.235,.68,feat,"#7f8c8d",fs=7.4,bold=False)
arrow(.245,.285,.50)
ax.text(.265,.545,"標準化",ha="center",fontsize=7.2)
box(.29,.34,.135,.32,"16 項\n模型輸入","#95a5a6",fs=8)
arrow(.43,.465,.50)
box(.47,.28,.20,.44,"對角狀態空間模型\nh = 8，186 參數\n\nO(1) 狀態跨事件傳遞","#2471a3",fs=8)
arrow(.675,.71,.50)
box(.715,.34,.125,.32,"2 個分數\n買側／賣側","#34495e",fs=8)
arrow(.845,.878,.50)
box(.882,.16,.113,.68,"每側比較\nτ = −16.80\n\n≥ τ 掛單\n< τ 撤單\n\n四種動作","#1e8449",fs=7.4)
ax.text(.585,.20,"分數 = 該側掛單的期望 maker 損益（元）",ha="center",fontsize=7.4,style="italic")

# ---------- (b) 時間軸 ----------
bx=fig.add_subplot(gs[1]); bx.axis("off"); bx.set_xlim(0,1); bx.set_ylim(0,1)
bx.text(.5,1.02,"(b) 單一掛單的時間軸與標籤的定義",ha="center",fontsize=10,fontweight="bold")
Y=.62
bx.add_patch(FancyArrowPatch((.03,Y),(.97,Y),arrowstyle="-|>",mutation_scale=14,color="k",lw=1.3))
for x,lab in [(.08,"事件 t\n決策並掛於最佳價\n（一口）"),
              (.40,"事件 t+k\n成交"),
              (.78,"事件 t+k+20\nmarkout 結算")]:
    bx.plot([x],[Y],"o",ms=7,color="k",zorder=4)
    bx.text(x,Y+.07,lab,ha="center",va="bottom",fontsize=8,fontweight="bold")
bx.annotate("",xy=(.40,Y-.10),xytext=(.08,Y-.10),
            arrowprops=dict(arrowstyle="<->",color="#7f8c8d",lw=1.2))
bx.text(.24,Y-.225,"排隊等待（長度不定）\n前方消耗完才輪到你",ha="center",fontsize=7.6,color="#555")
bx.annotate("",xy=(.78,Y-.10),xytext=(.40,Y-.10),
            arrowprops=dict(arrowstyle="<->",color="#c0392b",lw=1.4))
bx.text(.59,Y-.225,"H20：固定 20 個事件\n**只是標籤的量測視窗，不是持有期限**".replace("**",""),
        ha="center",fontsize=7.6,color="#c0392b",fontweight="bold")
# 標籤公式
bx.add_patch(Rectangle((.03,.02),.94,.195,fc="#f4f6f7",ec="0.65",lw=.8))
bx.text(.055,.165,"標籤（訓練目標）",fontsize=8.5,fontweight="bold",va="center")
bx.text(.055,.105,"未成交 →  0",fontsize=8.5,va="center")
bx.text(.055,.050,"成交   →  捕獲（掛單當下中價與成交價之差） ＋ 自成交起 20 事件的帶號 mark movement  −  單邊費用 127.34 元",
        fontsize=8.5,va="center")
bx.text(.965,.165,"零標籤約佔 50%",fontsize=7.6,ha="right",va="center",style="italic")
# 兩種失效
bx.text(.40,Y+.30,"若未成交：價位離開最佳檔（作廢）或被掃穿（計為最不利的成交）",
        ha="center",fontsize=7.6,color="#555",
        bbox=dict(fc="white",ec="0.75",lw=.5,pad=3))
fig.suptitle("輸入特徵、模型輸出與標籤的定義",fontsize=11,y=.985)
fig.savefig(OUT+"/figA1_feature_label.png"); plt.close(fig)
print("ok")
