"""扩充 api_aliases.json：加入 CDE 高频品种中英映射（基名），并重映射中国数据的 api_en。"""
import json
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ALIAS_PATH = BASE / "config" / "api_aliases.json"

ADDITIONS = {
  "oseltamivir": "奥司他韦", "potassium chloride": "氯化钾", "cefuroxime": "头孢呋辛",
  "ambroxol": "氨溴索", "cefoperazone": "头孢哌酮", "sulbactam": "舒巴坦",
  "ceftazidime": "头孢他啶", "vonoprazan": "伏诺拉生", "ceftizoxime": "头孢唑肟",
  "levofloxacin": "左氧氟沙星", "ceftriaxone": "头孢曲松", "cefotaxime": "头孢噻肟",
  "febuxostat": "非布司他", "dapoxetine": "达泊西汀", "famotidine": "法莫替丁",
  "tranexamic acid": "氨甲环酸", "glucosamine": "氨基葡萄糖", "cefazolin": "头孢唑林",
  "piracetam": "吡拉西坦", "nicorandil": "尼可地尔", "cefixime": "头孢克肟",
  "memantine": "美金刚", "parecoxib": "帕瑞昔布", "ornidazole": "奥硝唑",
  "urapidil": "乌拉地尔", "clindamycin": "克林霉素", "pramipexole": "普拉克索",
  "benzylpenicillin": "青霉素", "ticagrelor": "替格瑞洛", "doxofylline": "多索茶碱",
  "lidocaine": "利多卡因", "entecavir": "恩替卡韦", "pentoxifylline": "己酮可可碱",
  "diprophylline": "二羟丙茶碱", "pantoprazole": "泮托拉唑", "piperacillin": "哌拉西林",
  "tazobactam": "他唑巴坦", "lacosamide": "拉考沙胺", "pyridoxine": "维生素B6",
  "magnesium sulfate": "硫酸镁", "levetiracetam": "左乙拉西坦", "phloroglucinol": "间苯三酚",
  "citicoline": "胞磷胆碱", "sodium bicarbonate": "碳酸氢钠", "roxadustat": "罗沙司他",
  "apremilast": "阿普米司特", "dopamine": "多巴胺", "mecobalamin": "甲钴胺",
  "cefminox": "头孢米诺", "cefoxitin": "头孢西丁", "palbociclib": "哌柏西利",
  "thioctic acid": "硫辛酸", "hydrotalcite": "铝碳酸镁", "tofacitinib": "托法替布",
  "cefdinir": "头孢地尼", "acetylcysteine": "乙酰半胱氨酸", "azilsartan": "美阿沙坦",
  "ropivacaine": "罗哌卡因", "dexmedetomidine": "右美托咪定", "telmisartan": "替米沙坦",
  "torasemide": "托拉塞米", "naloxone": "纳洛酮", "palonosetron": "帕洛诺司琼",
  "metoprolol": "美托洛尔", "peramivir": "帕拉米韦", "metoclopramide": "甲氧氯普胺",
  "amikacin": "阿米卡星", "neostigmine": "新斯的明", "cefmetazole": "头孢美唑",
  "montmorillonite": "蒙脱石", "duloxetine": "度洛西汀", "oxacillin": "苯唑西林",
  "tenofovir alafenamide": "丙酚替诺福韦", "finasteride": "非那雄胺",
  "sugammadex": "舒更葡糖", "nicardipine": "尼卡地平", "bumetanide": "布美他尼",
  "levocarnitine": "左卡尼汀", "cephalexin": "头孢氨苄", "cefaclor": "头孢克洛",
  "pemetrexed": "培美曲塞", "vortioxetine": "伏硫西汀", "isoniazid": "异烟肼",
  "tacrolimus": "他克莫司", "norepinephrine": "去甲肾上腺素", "iohexol": "碘海醇",
  "moxifloxacin": "莫西沙星", "voriconazole": "伏立康唑", "nitroglycerin": "硝酸甘油",
  "ampicillin": "氨苄西林", "fluvoxamine": "氟伏沙明", "atropine": "阿托品",
  "dobutamine": "多巴酚丁胺", "metronidazole": "甲硝唑", "celecoxib": "塞来昔布",
  "furosemide": "呋塞米", "ketorolac": "酮咯酸", "meropenem": "美罗培南",
  "propofol": "丙泊酚", "acarbose": "阿卡波糖", "dabigatran": "达比加群",
  "cisatracurium": "顺阿曲库铵", "oxytocin": "缩宫素", "bromhexine": "溴己新",
  "linezolid": "利奈唑胺", "nifedipine": "硝苯地平", "bisoprolol": "比索洛尔",
  "irbesartan": "厄贝沙坦", "enoxaparin": "依诺肝素", "etoricoxib": "依托考昔",
  "afatinib": "阿法替尼", "vildagliptin": "维格列汀", "phenylephrine": "去氧肾上腺素",
  "edoxaban": "艾多沙班", "indapamide": "吲达帕胺", "argatroban": "阿加曲班",
  "adenosylcobalamin": "腺苷钴胺", "milrinone": "米力农", "calcitriol": "骨化三醇",
  "calcium gluconate": "葡萄糖酸钙", "esmolol": "艾司洛尔", "bortezomib": "硼替佐米",
  "ganciclovir": "更昔洛韦", "lenalidomide": "来那度胺",
  "tenofovir disoproxil": "替诺福韦二吡呋酯", "valproic acid": "丙戊酸",
  "rocuronium": "罗库溴铵", "aztreonam": "氨曲南", "olmesartan": "奥美沙坦",
  "carbazochrome": "卡络磺", "captopril": "卡托普利", "isosorbide mononitrate": "单硝酸异山梨酯",
  "alanyl glutamine": "丙氨酰谷氨酰胺", "methocarbamol": "美索巴莫", "iopamidol": "碘帕醇",
  "iodixanol": "碘克沙醇", "trazodone": "曲唑酮", "venlafaxine": "文拉法辛",
  "methotrexate": "甲氨蝶呤", "cefotiam": "头孢替安", "gemcitabine": "吉西他滨",
  "posaconazole": "泊沙康唑", "dexamethasone": "地塞米松", "aspirin": "阿司匹林",
  "benidipine": "贝尼地平", "tirofiban": "替罗非班", "lornoxicam": "氯诺昔康",
  "latamoxef": "拉氧头孢", "lansoprazole": "兰索拉唑", "calcium chloride": "氯化钙",
  "fluconazole": "氟康唑", "cefprozil": "头孢丙烯", "polidocanol": "聚多卡醇",
  "atomoxetine": "托莫西汀", "lenvatinib": "仑伐替尼", "roxatidine": "罗沙替丁",
  "methylprednisolone": "甲泼尼龙", "aminophylline": "氨茶碱", "flumazenil": "氟马西尼",
  "gliclazide": "格列齐特", "betamethasone": "倍他米松", "alfacalcidol": "阿法骨化醇",
  "norfloxacin": "诺氟沙星", "lurasidone": "鲁拉西酮", "temozolomide": "替莫唑胺",
  "diclofenac": "双氯芬酸", "chlorphenamine": "氯苯那敏", "octreotide": "奥曲肽",
  "alogliptin": "阿格列汀", "oxycodone": "羟考酮", "trimetazidine": "曲美他嗪",
  "bupivacaine": "布比卡因", "cefepime": "头孢吡肟", "cefradine": "头孢拉定",
  "indobufen": "吲哚布芬", "morinidazole": "吗啉硝唑", "avatrombopag": "阿伐曲泊帕",
  "felodipine": "非洛地平", "rabeprazole": "雷贝拉唑", "aripiprazole": "阿立哌唑",
  "azithromycin": "阿奇霉素", "metaraminol": "间羟胺", "atosiban": "阿托西班",
  "cimetidine": "西咪替丁", "eldecalcitol": "艾地骨化醇", "sevelamer": "司维拉姆",
  "isosorbide dinitrate": "硝酸异山梨酯", "ondansetron": "昂丹司琼",
  "lamotrigine": "拉莫三嗪", "macrogol": "聚乙二醇", "epalrestat": "依帕司他",
  "enalapril": "依那普利", "aprepitant": "阿瑞匹坦", "mirabegron": "米拉贝隆",
  "ursodeoxycholic acid": "熊去氧胆酸", "caspofungin": "卡泊芬净",
  "fluorouracil": "氟尿嘧啶", "perampanel": "吡仑帕奈", "ibandronic acid": "伊班膦酸",
  "gadoteric acid": "钆特酸", "lanthanum carbonate": "碳酸镧", "ioversol": "碘佛醇",
  "epinephrine": "肾上腺素", "erlotinib": "厄洛替尼", "glipizide": "格列吡嗪",
  "pravastatin": "普伐他汀", "docetaxel": "多西他赛", "ezetimibe": "依折麦布",
  "nadroparin": "那屈肝素", "salbutamol": "沙丁胺醇", "prucalopride": "普芦卡必利",
  "cytarabine": "阿糖胞苷", "tedizolid": "特地唑胺", "brexpiprazole": "布瑞哌唑",
  "nicergoline": "尼麦角林", "nimodipine": "尼莫地平", "oxcarbazepine": "奥卡西平",
  "canagliflozin": "卡格列净", "pitavastatin": "匹伐他汀",
  "icosapent ethyl": "二十碳五烯酸乙酯", "mycophenolate": "麦考酚",
  "beraprost": "贝前列素", "calcium dobesilate": "羟苯磺酸钙", "amiodarone": "胺碘酮",
  "propranolol": "普萘洛尔", "vardenafil": "伐地那非", "irinotecan": "伊立替康",
  "avibactam": "阿维巴坦", "agomelatine": "阿戈美拉汀", "iguratimod": "艾拉莫德",
  "paclitaxel": "紫杉醇", "lincomycin": "林可霉素", "penehyclidine": "戊乙奎醚",
  "imatinib": "伊马替尼", "rebamipide": "瑞巴派特", "somatostatin": "生长抑素",
  "cefodizime": "头孢地嗪", "glimepiride": "格列美脲", "tandospirone": "坦度螺酮",
  "olaparib": "奥拉帕利", "perindopril": "培哚普利", "pyrazinamide": "吡嗪酰胺",
  "clarithromycin": "克拉霉素", "voglibose": "伏格列波糖", "nintedanib": "尼达尼布",
  "gadopentetic acid": "钆喷酸", "abiraterone": "阿比特龙", "sunitinib": "舒尼替尼",
  "iopromide": "碘普罗胺", "tramadol": "曲马多", "doxorubicin": "多柔比星",
  "ciclosporin": "环孢素", "lamivudine": "拉米夫定", "paliperidone": "帕利哌酮",
  "levodopa/benserazide": "多巴丝肼", "digoxin": "地高辛", "edaravone": "依达拉奉",
  "progesterone": "黄体酮", "mirtazapine": "米氮平", "terbutaline": "特布他林",
  "flunarizine": "氟桂利嗪", "paroxetine": "帕罗西汀", "thymalfasin": "胸腺法新",
  "bendamustine": "苯达莫司汀", "tigecycline": "替加环素", "decitabine": "地西他滨",
  "zoledronic acid": "唑来膦酸", "amisulpride": "氨磺必利", "letrozole": "来曲唑",
  "enzalutamide": "恩扎卢胺", "deferasirox": "地拉罗司", "linagliptin": "利格列汀",
  "fenofibrate": "非诺贝特",
  # 第二轮补充
  "potassium aspartate": "门冬氨酸钾", "gadobutrol": "钆布醇", "dasatinib": "达沙替尼",
  "adenosine": "腺苷", "hydroxychloroquine": "羟氯喹", "cinacalcet": "西那卡塞",
  "drotaverine": "屈他维林", "olopatadine": "奥洛他定", "olprinone": "奥普力农",
  "repaglinide": "瑞格列奈", "teicoplanin": "替考拉宁", "saxagliptin": "沙格列汀",
  "gefitinib": "吉非替尼", "desmopressin": "去氨加压素", "carboprost": "卡前列素",
  "risperidone": "利培酮", "alendronic acid": "阿仑膦酸", "eltrombopag": "艾曲泊帕",
  "mivacurium": "米库氯铵", "fasudil": "法舒地尔", "granisetron": "格拉司琼",
  "labetalol": "拉贝洛尔", "levocetirizine": "左西替利嗪", "pioglitazone": "吡格列酮",
  "ivabradine": "伊伐布雷定", "cetrorelix": "西曲瑞克", "vecuronium": "维库溴铵",
  "micafungin": "米卡芬净", "terlipressin": "特利加压素", "ademetionine": "腺苷蛋氨酸",
  "clozapine": "氯氮平", "sulfamethoxazole": "磺胺甲噁唑", "midazolam": "咪达唑仑",
  "acipimox": "阿昔莫司", "lactated ringer's": "乳酸钠林格",
  "sodium acetate ringer's": "醋酸钠林格", "glycerol fructose": "甘油果糖",
}


def main():
    aliases = json.load(open(ALIAS_PATH, encoding="utf-8"))
    added = skipped = 0
    for en, zh in ADDITIONS.items():
        if en in aliases:
            skipped += 1
            continue
        aliases[en] = {"zh": zh, "variants": []}
        added += 1
    json.dump(aliases, open(ALIAS_PATH, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"别名库新增 {added} 条（跳过已存在 {skipped} 条），总计 {len([k for k in aliases if not k.startswith('_')])} 条")

    # 双向包含匹配重映射中国数据 api_en
    zh_map = {}
    for en, info in aliases.items():
        if en.startswith("_") or not info.get("zh"):
            continue
        zh_map[info["zh"]] = en

    def guess(api_zh: str) -> str:
        best, best_en = 0, ""
        for zh, en in zh_map.items():
            if len(zh) < 2:
                continue
            if zh in api_zh or (len(api_zh) >= 3 and api_zh in zh):
                if len(zh) > best:
                    best, best_en = len(zh), en
        return best_en

    conn = sqlite3.connect(BASE / "data" / "generics.db")
    rows = conn.execute(
        "SELECT id, api_zh FROM products WHERE country='中国' AND (api_en='' OR api_en IS NULL)"
    ).fetchall()
    n = 0
    for rid, api_zh in rows:
        en = guess(api_zh or "")
        if en:
            conn.execute("UPDATE products SET api_en=? WHERE id=?", (en, rid))
            n += 1
    conn.commit()
    print(f"重映射：{n} / {len(rows)} 条中国记录获得英文 API")


if __name__ == "__main__":
    main()
