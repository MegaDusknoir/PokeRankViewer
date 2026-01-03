import json
import os
import sys
import re
import requests

JPN = 0
ENG = 1
FRA = 2
ITA = 3
GER = 4
SPA = 5
KOR = 6
CHS = 7
CHT = 8

# 天梯不作区分的形态
COMBINE_FORM_POKEMON = (
    774, # 小陨星
    875, # 冰砌鹅
    888, # 苍响
    889, # 藏玛然特
    964, # 海豚侠
    1017, # 厄诡椪
    1024, # 太乐巴戈斯
)

NATURE_EFFECT = [
    "",
    "+攻击 -防御",
    "+攻击 -速度",
    "+攻击 -特攻",
    "+攻击 -特防",
    "+防御 -攻击",
    "",
    "+防御 -速度",
    "+防御 -特攻",
    "+防御 -特防",
    "+速度 -攻击",
    "+速度 -防御",
    "",
    "+速度 -特攻",
    "+速度 -特防",
    "+特攻 -攻击",
    "+特攻 -防御",
    "+特攻 -速度",
    "",
    "+特攻 -特防",
    "+特防 -攻击",
    "+特防 -防御",
    "+特防 -速度",
    "+特防 -特攻",
    ""
]

__bundlePath = 'raw'

def pokeFormIdMapping(nationalDex:int, form:int) -> tuple:
    """
    Form id defines in dex json, PokemonHome, Zukan are different.

    return (DexDefine, HomeDefine, ZukanDefine)
    """
    if nationalDex == 666:
        return (0, 18, 0)
    elif nationalDex == 774:
        return (form, 7, 0 if form == 0 else 1)
    elif nationalDex in COMBINE_FORM_POKEMON:
        return (form, 0, form)
    else:
        return (form, form, form)

def langcodeInt(langcode:str) -> int:
    langcodeDict = {
        'JPN': 0,
        'ENG': 1,
        'FRA': 2,
        'ITA': 3,
        'GER': 4,
        'SPA': 5,
        'KOR': 6,
        'CHS': 7,
        'CHT': 8,
    }
    return langcodeDict[langcode]

def create_type_code(path=__bundlePath, langcode=CHS):
    with open(f'{path}/bundle.js', encoding='utf-8') as fin:
        ls = re.findall(r'teraType:(.*?)}', fin.read())
        data = ls[langcode].split(',')
        dict = {}
        for d in data: 
            num = re.sub(r'\D', '', d)
            value = re.findall(r'"(.*?)"', d)[0]
            dict[str(num)] = value
    return dict

def create_nature_code(path=__bundlePath, langcode=CHS):
    with open(f'{path}/bundle.js', encoding='utf-8') as fin:
        ls = re.findall(r'seikaku:(.*?)}', fin.read())
        data = ls[langcode].split(',')
        dict = {}
        for d in data: 
            num = re.sub(r'\D', '', d)
            value = re.findall(r'"(.*?)"', d)[0]
            dict[str(num)] = value
    return dict

def create_ability_code(path=__bundlePath, langcode=CHS):
    with open(f'{path}/bundle.js', encoding='utf-8') as fin:
        ls = re.findall(r'tokusei:(.*?)}', fin.read())
        data = ls[langcode].split(',')
        dict = {}
        for d in data: 
            num = re.sub(r'\D', '', d)
            value = re.findall(r'"(.*?)"', d)[0]
            dict[str(num)] = value
    return dict

def create_move_code(path=__bundlePath, langcode=CHS):
    with open(f'{path}/bundle.js', encoding='utf-8') as fin:
        ls = re.findall(r'waza:{(.*?)}', fin.read())
        data = ls[langcode].split(',')
        dict = {}
        for d in data:
            num = d[:d.index(':')]
            value = re.findall(r'"(.*?)"', d)[0]
            dict[str(num)] = value
    return dict

def create_item_code(path=__bundlePath, langcode:str='CHS'):
    with open(f'{path}/pokeItem.json', 'r', encoding='utf-8') as file:
        data = json.load(file)['itemname']
    dict = {}
    for id in data:
        dict[id] = data[id][langcode] if langcode in data[id] else data[id]['JPN']
    return dict

def combineFullId(dexId:int, form:int) -> str:
    return f"{dexId:04}-{form:03}"

class pokeHomeLite:
    def __init__(self, workDir=os.path.dirname(sys.argv[0])) -> None:
        self.workDir = workDir
        bundlePath = f'{self.workDir}/raw'
        if not os.path.exists(f'{self.workDir}/cache'):
            os.makedirs(f'{self.workDir}/cache')

        self.proxy = {}

        # デコードデータの読み込み
        self.type_code = create_type_code(bundlePath, CHS)
        self.nature_code = create_nature_code(bundlePath, CHS)
        self.ability_code = create_ability_code(bundlePath, CHS)
        self.move_code = create_move_code(bundlePath, CHS)
        self.move_data = self.__loadMoveData(bundlePath)
        self.item_code = create_item_code(bundlePath, 'CHS')
        self.zukan = self.__readPokedex(bundlePath)

        self.__dataSeason = None
        self.__dataRank = {}

        self.cacheSeasonPath = 'cache/Season.json'

    def __loadMoveData(self, path) -> dict:
        # 図鑑の読み込み
        with open(f'{path}/pokeMove.json', encoding='utf-8') as fin:
            moves = json.load(fin)
        return moves

    def __readPokedex(self, path) -> dict:
        # 図鑑の読み込み
        with open(f'{path}/zukan.json', encoding='utf-8') as fin:
            dex = json.load(fin)
        for type_id in range(1,18):
            dex['493'][str(type_id)] = dex['493']['0'].copy()
            dex['493'][str(type_id)]['form'] = f'{self.type_code[str(type_id)]}属性'
            dex['493'][str(type_id)]['alias'] += f'-{self.type_code[str(type_id)]}'
            dex['493'][str(type_id)]['type_1'] = self.type_code[str(type_id)]
            self.type_code[str(type_id)]
        dex['493']['0']['form'] = '一般属性'
        return dex

    def setProxy(self, proxy:object):
        self.proxy = proxy

    def nameSearch(self, name):
        pid = None
        for pkm in home.zukan:
            if pid == None:
                for form in home.zukan[pkm]:
                    if home.zukan[pkm][form]['name'] == name or home.zukan[pkm][form]['alias'] == name:
                        pid = home.zukan[pkm][form]['id']
                        break
            else:
                break
        return pid

    def find_term(self, season:str, rule=1)->dict:
        dataSeason = self.getSeasons()
        for sn in dataSeason:
            if season == sn:
                for id in dataSeason[sn]:
                    if dataSeason[sn][id]['rule'] == rule:
                        return dataSeason[sn][id]

    def clearCache(self):
        for f in os.listdir(f'{self.workDir}/cache'):
            if f.endswith('.json'):
                os.remove(f'{self.workDir}/cache/{f}')
        self.__dataRank = {}
        self.__dataSeason = None

    def getUsage(self, fullId:str, season:str, rule=1)->dict:
        pid, formId = fullId.split('-')
        pid = str(int(pid))
        formId = str(int(formId))
        rank = self.getRank(season, rule)
        term = self.find_term(season, rule)
        id, rst, ts1, ts2 = term['cId'], term['rst'], term['ts1'], term['ts2']

        page = int(pid) // 200 + 1
        localDataPath = f'pokemon_({(page - 1)*200}~{(page)*200 - 1})_S{season}R{rule}.json'
        if os.path.isfile(f'{self.workDir}/cache/{localDataPath}'):
            with open(f'{self.workDir}/cache/{localDataPath}', 'r', encoding='utf-8') as fin:
                data = json.load(fin)
        else:
            headers = {
                'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Mobile Safari/537.36',
                'content-type': 'application/json',
            }
            # 採用率を取得
            print('採用率を取得...')
            #url = f'https://resource.pokemon-home.com/battledata/ranking/{id}/{rst}/{ts2}/pdetail-{page}' # 剣盾
            url = f'https://resource.pokemon-home.com/battledata/ranking/scvi/{id}/{rst}/{ts2}/pdetail-{page}' # SV
            res = requests.get(url, headers=headers, proxies=self.proxy)
            with open(f'{self.workDir}/cache/{localDataPath}', 'w', encoding='utf-8') as fout:
                fout.write(res.text)
            data = json.loads(res.text)

        # 採用率 (図鑑番号順)
        adoption = {}

        formId, findFormHomeId = pokeFormIdMapping(int(pid), int(formId))[0:2]
        formId = str(formId)
        findFormHomeId = str(findFormHomeId)
        for dexId in data:
            if dexId == pid:
                for formHomeId in data[dexId]:
                    if pid not in self.zukan:
                        print(f"{pid} is not in zukan")
                        continue

                    if formHomeId == findFormHomeId:
                        adoption[fullId] = {'rank': rank[fullId] if fullId in rank else 9999}

                        for k in ['id','form_id','name','form','alias']:
                            adoption[fullId][k] = self.zukan[pid][formId][k]

                        # 技
                        adoption[fullId]['move'], adoption[fullId]['move_rate'], adoption[fullId]['move_type'] = [], [], []
                        for d in data[dexId][formHomeId]['temoti']['waza']:
                            adoption[fullId]['move'].append(self.move_code[str(d['id'])])
                            adoption[fullId]['move_rate'].append(float(d['val']))
                            adoption[fullId]['move_type'].append(self.move_data[str(d['id'])]['type'])

                        # 性格
                        adoption[fullId]['nature'], adoption[fullId]['nature_rate'] = [], []
                        adoption[fullId]['nature_effect'] = []
                        for d in data[dexId][formHomeId]['temoti']['seikaku']:
                            adoption[fullId]['nature'].append(self.nature_code[str(d['id'])])
                            adoption[fullId]['nature_rate'].append(float(d['val']))
                            adoption[fullId]['nature_effect'].append(NATURE_EFFECT[int(d['id'])])

                        # 特性
                        adoption[fullId]['ability'], adoption[fullId]['ability_rate'] = [], []
                        for d in data[dexId][formHomeId]['temoti']['tokusei']:
                            adoption[fullId]['ability'].append(self.ability_code[str(d['id'])])
                            adoption[fullId]['ability_rate'].append(float(d['val']))
                        
                        # アイテム
                        adoption[fullId]['item'], adoption[fullId]['item_rate'] = [], []
                        for d in data[dexId][formHomeId]['temoti']['motimono']:
                            adoption[fullId]['item'].append(self.item_code[str(d['id'])])
                            adoption[fullId]['item_rate'].append(float(d['val']))
                        
                        # テラスタイプ
                        adoption[fullId]['terastal'], adoption[fullId]['terastal_rate'] = [], []
                        for d in data[dexId][formHomeId]['temoti']['terastal']:
                            adoption[fullId]['terastal'].append(self.type_code[str(d['id'])])
                            adoption[fullId]['terastal_rate'].append(float(d['val']))

                        # パートナー
                        adoption[fullId]['partner'] = []
                        for partner in data[dexId][formHomeId]['temoti']['pokemon']:
                            if str(partner['id']) in self.zukan and str(partner['form']) in self.zukan[str(partner['id'])]:
                                if partner['id'] in COMBINE_FORM_POKEMON:
                                    adoption[fullId]['partner'].append(self.zukan[str(partner['id'])][str(partner['form'])]['name'])
                                else:
                                    adoption[fullId]['partner'].append(self.zukan[str(partner['id'])][str(partner['form'])]['alias'])

                        # DefeatPkm
                        adoption[fullId]['win_pkm'] = []
                        for pkm in data[dexId][formHomeId]['win']['pokemon']:
                            if str(pkm['id']) in self.zukan and str(pkm['form']) in self.zukan[str(pkm['id'])]:
                                if pkm['id'] in COMBINE_FORM_POKEMON:
                                    adoption[fullId]['win_pkm'].append(self.zukan[str(pkm['id'])][str(pkm['form'])]['name'])
                                else:
                                    adoption[fullId]['win_pkm'].append(self.zukan[str(pkm['id'])][str(pkm['form'])]['alias'])

                        # DefeatMove
                        adoption[fullId]['win_move'], adoption[fullId]['win_move_rate'], adoption[fullId]['win_move_type'] = [], [], []
                        for d in data[dexId][formHomeId]['win']['waza']:
                            adoption[fullId]['win_move'].append(self.move_code[str(d['id'])])
                            adoption[fullId]['win_move_rate'].append(float(d['val']))
                            adoption[fullId]['win_move_type'].append(self.move_data[str(d['id'])]['type'])

                        # LostPkm
                        adoption[fullId]['lose_pkm'] = []
                        for lostPkm in data[dexId][formHomeId]['lose']['pokemon']:
                            if str(lostPkm['id']) in self.zukan and str(lostPkm['form']) in self.zukan[str(lostPkm['id'])]:
                                if lostPkm['id'] in COMBINE_FORM_POKEMON:
                                    adoption[fullId]['lose_pkm'].append(self.zukan[str(lostPkm['id'])][str(lostPkm['form'])]['name'])
                                else:
                                    adoption[fullId]['lose_pkm'].append(self.zukan[str(lostPkm['id'])][str(lostPkm['form'])]['alias'])

                        # LostMove
                        adoption[fullId]['lose_move'], adoption[fullId]['lose_move_rate'], adoption[fullId]['lose_move_type'] = [], [], []
                        for d in data[dexId][formHomeId]['lose']['waza']:
                            adoption[fullId]['lose_move'].append(self.move_code[str(d['id'])])
                            adoption[fullId]['lose_move_rate'].append(float(d['val']))
                            adoption[fullId]['lose_move_type'].append(self.move_data[str(d['id'])]['type'])
                        break
                break

        return adoption

    def getSeasons(self, forceUpdate=False) -> dict:
        if self.__dataSeason == None or forceUpdate == True:
            if forceUpdate == False and os.path.isfile(f'{self.workDir}/{self.cacheSeasonPath}'):
                with open(f'{self.workDir}/{self.cacheSeasonPath}', 'r', encoding='utf-8') as fin:
                    self.__dataSeason = json.load(fin)['list']
            else:
                headers = {
                    'accept': 'application/json, text/javascript, */*; q=0.01',
                    'countrycode': '304',
                    'authorization': 'Bearer',
                    'langcode': '9', # 1: Japanese, 2: English, 8: Korean, 9: Simplified Chinese, 10: Traditional Chinese
                    'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Mobile Safari/537.36',
                    'content-type': 'application/json',
                }
                # シーズン情報を取得
                print('シーズン情報を取得...')
                #url = 'https://api.battle.pokemon-home.com/cbd/competition/rankmatch/list' # 剣盾
                url = 'https://api.battle.pokemon-home.com/tt/cbd/competition/rankmatch/list' # SV
                res = requests.post(url, headers=headers, data='{"soft":"Sw"}', proxies=self.proxy)
                self.__dataSeason = json.loads(res.text)['list']
                with open(f'{self.workDir}/{self.cacheSeasonPath}', 'w', encoding='utf-8') as fout:
                    fout.write(res.text)
        return self.__dataSeason

    def getRank(self, season:str, rule=1, forceUpdate=False)->dict:
        rankTitle = f'Rank_S{season}R{rule}'
        if rankTitle not in self.__dataRank or forceUpdate == True:
            if forceUpdate == False and os.path.isfile(f'{self.workDir}/cache/{rankTitle}.json'):
                print('ポケモンの使用率をローカル取得...')
                with open(f'{self.workDir}/cache/{rankTitle}.json', 'r', encoding='utf-8') as fin:
                    rank = json.load(fin)
            else:
                term = self.find_term(season, rule)
                id, rst, ts1, ts2 = term['cId'], term['rst'], term['ts1'], term['ts2']

                headers = {
                    'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Mobile Safari/537.36',
                    'content-type': 'application/json',
                }

                # ポケモンの使用率を取得
                print('ポケモンの使用率を取得...')
                #url = f'https://resource.pokemon-home.com/battledata/ranking/{id}/{rst}/{ts2}/pokemon' # 剣盾
                url = f'https://resource.pokemon-home.com/battledata/ranking/scvi/{id}/{rst}/{ts2}/pokemon' # SV
                rankRaw = requests.get(url, headers=headers, proxies=self.proxy).text
                rank = {}
                for i,d in enumerate(json.loads(rankRaw)):
                    rank[combineFullId(d['id'], d['form'])] = i + 1
                with open(f'{self.workDir}/cache/{rankTitle}.json', 'w', encoding='utf-8') as fout:
                    json.dump(rank, fout)
            self.__dataRank[rankTitle] = rank
        return self.__dataRank[rankTitle]

if __name__ == '__main__':
    # ルール（シングル: 0, ダブル: 1）
    rule = 1

    argSeason = '26'
    argRule = 1
    if len(sys.argv) < 2:
        print('usage: .py [pokemon] [rule=1] [season=26]')
        exit()
    if len(sys.argv) >= 2:
        argPkm = sys.argv[1]
    if len(sys.argv) >= 3:
        argRule = int(sys.argv[2])
    if len(sys.argv) >= 4:
        argSeason = sys.argv[3]

    home = pokeHomeLite()
    argPkmId = home.nameSearch(argPkm)
    if argPkmId != None:
        usage = home.getUsage(f'{argPkmId:04d}-000', argSeason, argRule)
        with open(f'{home.workDir}/cache/{argPkmId}_usage_s{argSeason}_r{argRule}.json', 'w', encoding='utf-8') as fout:
            fout.write(json.dumps(usage, ensure_ascii=False))
    print(usage)
