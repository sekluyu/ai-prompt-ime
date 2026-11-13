"""Build the GPT-owned bootstrap dictionary or a colleague-supplied UTF-8 TSV."""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from general_phrases import merge
from ranking import compiled_weights

ROOT = Path(__file__).resolve().parents[1]


def bootstrap():
    rows = []
    def add(tag, zh, code, weight=1000):
        rows.append(dict(tag=tag, zh=zh, code=code, weight=weight))
    base = '''1girl|一个女孩|yigenvhai
1girl|女孩|nvhai
1boy|一个男孩|yigenanhai
solo|单人|danren
twintails|双马尾|shuangmawei
ponytail|马尾|mawei
high_ponytail|高马尾|gaomawei
low_ponytail|低马尾|dimawei
short_twintails|短双马尾|duanshuangmawei
long_hair|长发|changfa
short_hair|短发|duanfa
medium_hair|中长发|zhongchangfa
very_long_hair|超长发|chaochangfa
straight_hair|直发|zhifa
wavy_hair|波浪发|bolangfa
curly_hair|卷发|juanfa
braid|辫子|bianzi
twin_braids|双辫|shuangbian
hair_bun|丸子头|wanzitou
double_bun|双丸子头|shuangwanzitou
bangs|刘海|liuhai
blunt_bangs|齐刘海|qiliuhai
ahoge|呆毛|daimao
hair_over_one_eye|遮住一只眼|zhezhuyizhiyan
thighhighs|过膝袜|guoxiwa
kneehighs|及膝袜|jixiwa
pantyhose|连裤袜|liankuwa
socks|袜子|wazi
barefoot|赤脚|chijiao
boots|靴子|xuezi
shoes|鞋子|xiezi
high_heels|高跟鞋|gaogenxie
sneakers|运动鞋|yundongxie
loafers|乐福鞋|lefuxie
dress|连衣裙|lianyiqun
skirt|裙子|qunzi
pleated_skirt|百褶裙|baizhequn
shirt|衬衫|chenshan
t-shirt|短袖衫|duanxiushan
blouse|女式衬衫|nvshichenshan
sweater|毛衣|maoyi
cardigan|开衫|kaishan
jacket|夹克|jiake
coat|外套|waitao
hoodie|连帽衫|lianmaoshan
school_uniform|校服|xiaofu
sailor_collar|水手领|shuishouling
serafuku|水手服|shuishoufu
maid|女仆|nvpu
maid_headdress|女仆头饰|nvputoushi
kimono|和服|hefu
yukata|浴衣|yuyi
china_dress|旗袍|qipao
armor|盔甲|kuijia
cape|披风|pifeng
scarf|围巾|weijin
gloves|手套|shoutao
hat|帽子|maozi
beret|贝雷帽|beileimao
witch_hat|魔女帽|monvmao
hair_ribbon|发带|fadai
hairclip|发夹|fajia
hair_ornament|发饰|fashi
headband|发箍|fagu
bow|蝴蝶结|hudiejie
necktie|领带|lingdai
bowtie|领结|lingjie
glasses|眼镜|yanjing
round_eyewear|圆框眼镜|yuankuangyanjing
sunglasses|墨镜|mojing
earrings|耳环|erhuan
necklace|项链|xianglian
smile|微笑|weixiao
grin|露齿笑|luchixiao
laughing|大笑|daxiao
blush|脸红|lianhong
crying|哭泣|kuqi
tears|眼泪|yanlei
angry|生气|shengqi
sad|悲伤|beishang
surprised|惊讶|jingya
sleepy|困倦|kunjuan
closed_eyes|闭眼|biyan
one_eye_closed|单眼闭合|danyanbihe
open_mouth|张嘴|zhangzui
closed_mouth|闭嘴|bizui
looking_at_viewer|看向观众|kanxiangguanzhong
looking_away|看向别处|kanxiangbiechu
looking_back|回头看|huitoukan
looking_up|抬头看|taitoukan
looking_down|低头看|ditoukan
standing|站立|zhanli
sitting|坐着|zuozhe
walking|行走|xingzou
running|跑步|paobu
jumping|跳跃|tiaoyue
lying|躺着|tangzhe
kneeling|跪着|guizhe
squatting|蹲着|dunzhe
arms_up|举起双手|juqishuangshou
arms_crossed|抱臂|baobi
hand_on_hip|手放腰间|shoufangyaojian
hands_in_pockets|双手插兜|shuangshouchadou
holding_book|拿着书|nazheshu
holding_umbrella|撑伞|chengsan
peace_sign|胜利手势|shenglishoushi
portrait|肖像|xiaoxiang
close-up|特写|texie
upper_body|上半身|shangbanshen
full_body|全身|quanshen
cowboy_shot|七分身|qifenshen
from_above|俯视|fushi
from_below|仰视|yangshi
from_side|侧视|ceshi
from_behind|背面|beimian
profile|侧脸|celian
outdoors|户外|huwai
indoors|室内|shinei
simple_background|简单背景|jiandanbeijing
transparent_background|透明背景|toumingbeijing
gradient_background|渐变背景|jianbianbeijing
sky|天空|tiankong
blue_sky|蓝天|lantian
cloud|云|yun
sunset|日落|riluo
sunrise|日出|richu
night|夜晚|yewan
starry_sky|星空|xingkong
moon|月亮|yueliang
full_moon|满月|manyue
rain|雨|yu
snow|雪|xue
cherry_blossoms|樱花|yinghua
flower|花|hua
tree|树|shu
forest|森林|senlin
mountain|山|shan
ocean|海洋|haiyang
beach|海滩|haitan
river|河流|heliu
lake|湖泊|hupo
waterfall|瀑布|pubu
grass|草地|caodi
garden|花园|huayuan
city|城市|chengshi
street|街道|jiedao
building|建筑|jianzhu
rooftop|屋顶|wuding
classroom|教室|jiaoshi
library|图书馆|tushuguan
bedroom|卧室|woshi
window|窗户|chuanghu
chair|椅子|yizi
table|桌子|zhuozi
book|书|shu
umbrella|雨伞|yusan
cat|猫|mao
dog|狗|gou
bird|鸟|niao
butterfly|蝴蝶|hudie
cat_ears|猫耳|maoer
fox_ears|狐耳|huer
rabbit_ears|兔耳|tuer
animal_ears|兽耳|shouer
tail|尾巴|weiba
wings|翅膀|chibang
horns|角|jiao
elf|精灵|jingling
pointy_ears|尖耳朵|jianerduo
robot|机器人|jiqiren
mecha|机甲|jijia
sword|剑|jian
staff|法杖|fazhang
magic|魔法|mofa
backlighting|逆光|niguang
sunlight|阳光|yangguang
moonlight|月光|yueguang
shadow|阴影|yinying
depth_of_field|景深|jingshen
blurry_background|背景虚化|beijingxuhua
monochrome|单色|danse
greyscale|灰度|huidu
sketch|草图|caotu
lineart|线稿|xiangao
watercolor_(medium)|水彩|shuicai
traditional_media|传统媒介|chuantongmeijie
pixel_art|像素画|xiangsuhua
chibi|Q版|qban
comic|漫画|manhua'''
    for line in base.splitlines():
        add(*line.split('|'))
    colors = [('black','黑','hei'),('white','白','bai'),('red','红','hong'),('blue','蓝','lan'),('green','绿','lv'),('yellow','黄','huang'),('pink','粉','fen'),('purple','紫','zi'),('brown','棕','zong'),('orange','橙','cheng'),('grey','灰','hui')]
    for color, zh, code in colors:
        for noun, cn, py in [('hair','发','fa'),('eyes','眼','yan'),('dress','色连衣裙','selianyiqun'),('skirt','色裙子','sequnzi'),('shirt','色衬衫','sechenshan'),('background','色背景','sebeijing')]:
            add(f'{color}_{noun}',zh+cn,code+py,800)
    add('blonde_hair','金发','jinfa')
    add('white_hair','白头发','baitoufa')
    add('white_hair','白毛','baimao')
    add('thighhighs','长筒袜','changtongwa')
    add('hair','头发','toufa')
    return rows


def build(source=None, output_dir=None, variant='searchable'):
    rows = list(csv.DictReader(source.open(encoding='utf-8-sig'), delimiter='\t')) if source else bootstrap()
    rows = merge(rows,variant)
    merged = {}
    seen_source_keys = set()
    duplicate_rows = 0
    for row in rows:
        tag, zh, code = (row[k].strip() for k in ('tag','zh','code'))
        if not re.fullmatch('[a-z]+', code) or any(c in tag+zh for c in '\t\r\n') or not tag or not zh:
            raise ValueError(f'Invalid row: {row!r}')
        weight=int(row['weight'])
        if weight < 0:
            raise ValueError('weight must be nonnegative')
        source_key=(tag,code)
        if source_key in seen_source_keys:
            continue
        seen_source_keys.add(source_key)
        # Migration from v0.2.3: unprefixed rows are the canonical ffdkj/core
        # entries retained by that builder. Explicit v2 roles persist thereafter.
        role=row.get('role') or ('alias' if tag.startswith('__prompt__:') else 'primary')
        if role not in {'primary','alias'}:
            raise ValueError('Unknown ranking role: '+role)
        text=tag.removeprefix('__prompt__:')
        key=(code,text)
        item=dict(tag=tag,zh=zh,code=code,weight=weight,role=role)
        if key not in merged:
            merged[key]=item
        else:
            duplicate_rows+=1
            old=merged[key]
            # Keep the canonical source key where one exists. User-facing
            # spelling and every distinct pinyin entry remain unchanged.
            canonical=text if text in (old['tag'],tag) else old['tag']
            if (role=='primary',weight,'〔' in zh) > (old['role']=='primary',old['weight'],'〔' in old['zh']):
                merged[key]=item
            merged[key]['weight']=max(weight,old['weight'])
            merged[key]['tag']=canonical
    clean=list(merged.values())
    priorities=compiled_weights(clean)
    clean.sort(key=lambda x:(x['code'],-priorities[(x['tag'],x['code'])],x['tag']))
    out = output_dir or ROOT/'rime'
    out.mkdir(parents=True,exist_ok=True)
    lines = ['---','name: booru','version: "0.2.4"','sort: by_weight','use_preset_vocabulary: false','columns: [text, code, weight]','...']
    # Source tags keep their keys; project phrases use a private output prefix.
    lines.extend(f"{r['tag']}\t{r['code']}\t{priorities[(r['tag'],r['code'])]}" for r in clean)
    (out/'booru.dict.yaml').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    with (out/'booru.tsv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['tag','zh','code','weight','role'],delimiter='\t',lineterminator='\n')
        writer.writeheader(); writer.writerows(clean)
    report=dict(source=str(source) if source else 'GPT curated bootstrap (not ffdkj full data)',rows=len(clean),unique_tags=len({r['tag'] for r in clean}),merged_duplicate_rows=duplicate_rows,sha256=hashlib.sha256((out/'booru.tsv').read_bytes()).hexdigest())
    report_dir=ROOT/'validation/gpt'
    report_dir.mkdir(parents=True,exist_ok=True)
    (report_dir/'build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--source',type=Path)
    parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--variant',choices=['default','searchable'],default='searchable',help='Complete corpus by default; default selects the historical smaller import scope')
    args=parser.parse_args()
    build(args.source,args.output_dir,args.variant)
