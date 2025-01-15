import os
import sys
import re
import json
import base64
import datetime
from typing import Literal

import tkinter as tk
from tkinter.constants import *
import ttkbootstrap as ttk

import PIL.Image
import PIL.ImageTk

import requests
from contextlib import redirect_stdout

import pokeHomeApi
from home_icon import Icon

workDir = os.path.dirname(sys.argv[0])

TRADITIONAL_TYPE_ORDER = {"一般":1,
                          "火":2,
                          "水":3,
                          "草":4,
                          "电":5,
                          "冰":6,
                          "格斗":7,
                          "毒":8,
                          "地面":9,
                          "飞行":10,
                          "超能力":11,
                          "虫":12,
                          "岩石":13,
                          "幽灵":14,
                          "龙":15,
                          "恶":16,
                          "钢":17,
                          "妖精":18,
                          "星晶":99
}

def dump(obj):
    with open('dump/out.txt', 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False)

def getPokemonImageFile(fullId):
    if fullId == 0:
        if not os.path.exists(f'{workDir}/image'):
            os.makedirs(f'{workDir}/image')
        return f'{workDir}/raw/HOME_0.png'
    if os.path.isfile(f'{workDir}/image/HOME_{fullId}.png'):
        pass
    else:
        print('downloading image...')
        dexId, form = fullId.split('-')
        form = pokeHomeApi.pokeFormIdMapping(int(dexId), int(form))[2]
        try:
            htmlData = requests.get(f'https://zukan.pokemon.co.jp/detail/{dexId}', timeout=4).content.decode()
            jsonRaw = re.findall(r'<script id="json-data" type="application/json">(.*?)</script>', htmlData)[0]
            jsonData = json.loads(jsonRaw)
            imageUrl = ''
            if len(jsonData['groups']) == 0:
                imageUrl = jsonData['pokemon']['image_s']
            else:
                for formData in jsonData['groups']:
                    if formData['sub'] == form or (form == 999 and formData['omosa'] == "9,999.9"):
                        imageUrl = formData['image_s']
                        break
            img_data = requests.get(imageUrl, timeout=4).content
            with open(f'{workDir}/image/HOME_{fullId}.png', 'wb') as handler:
                handler.write(img_data)
        except requests.exceptions.RequestException:
            print('Request fail')
            return f'{workDir}/raw/HOME_0.png'
        
    return f'{workDir}/image/HOME_{fullId}.png'

class pokeRankWindow():
    def mainloop(self):
        self.__windowAutoPosition()
        with open('_tmp.ico', 'wb+') as tmp:
            tmp.write(base64.b64decode(Icon().ig))
        self.main.iconbitmap('_tmp.ico')
        os.remove('_tmp.ico')

        self.main.mainloop()

    def __windowAutoPosition(self):
        w = 982
        h = 857
        ws = self.main.winfo_screenwidth()
        hs = self.main.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        self.main.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.main.update()
        self.main.minsize(self.main.winfo_width(), self.main.winfo_height())
        # print(self.main.winfo_width(), self.main.winfo_height())

    def __selectSeasonCbo(self, *args):
        if self.varSearchPoke.get() == '':
            self.__searchPokemon()

    def __getSeason(self) -> list:
        self.seasonInfoMap = {}
        dataSeason = self.home.getSeasons()
        listSeason = []
        for season in dataSeason:
            for term in dataSeason[season]:
                seasonInfo = {
                    'season': season,
                    'name': dataSeason[season][term]['name'],
                    'start': dataSeason[season][term]['start'],
                    'end': dataSeason[season][term]['end'],
                }
                listSeason.append(f'{seasonInfo['name']} ({seasonInfo['start']} ~ {seasonInfo['end']})')
                self.seasonInfoMap[listSeason[-1]] = seasonInfo
                break
        return listSeason

    def __searchPokemon(self, *args):
        sstr = self.varSearchPoke.get()
        for item in self.tvPokeList.get_children():
            self.tvPokeList.delete(item)

        filtered_data = []
        # 没有过滤时按排名显示
        if sstr == "":
            argSeason = self.seasonInfoMap[self.cboSeason.get()]['season']
            rank = self.home.getRank(argSeason, self.rule)
            for fullId in rank:
                filtered_data.append(self.dictFullIdPokemon[fullId] if fullId in self.dictFullIdPokemon else self.dictFullIdPokemon[fullId.split('-')[0]+'-000'])
        elif sstr.lower() == 'all':
            for fullId in self.dictFullIdPokemon:
                filtered_data.append(self.dictFullIdPokemon[fullId])
        elif sstr.isdecimal() == True:
            for fullId in self.dictFullIdPokemon:
                if int(sstr) == int(fullId.split('-')[0]):
                    filtered_data.append(self.dictFullIdPokemon[fullId])
        else:
            for fullId in self.dictFullIdPokemon:
                if self.dictFullIdPokemon[fullId].find(sstr) >= 0:
                    filtered_data.append(self.dictFullIdPokemon[fullId])
        self.__pokemonFillList(filtered_data)   
    
    def __pokemonFillList(self, ld):
        for item in ld:
            self.tvPokeList.insert("", END, text=item)

    class pokemonIdentifier():
        def __init__(self, fullId:str, dex:dict) -> None:
            self.fullId = fullId
            self.dexId, self.formId = fullId.split('-')
            self.dexId = int(self.dexId)
            self.formId = int(self.formId)
            self.dex = dex[str(self.dexId)][str(self.formId)]

    def __findPokemon(self, fullName:str) -> pokemonIdentifier:
        for id, name in self.dictFullIdPokemon.items():
            if name == fullName:
                return self.pokemonIdentifier(id, dex = self.home.zukan)

    def __pokemonSelect(self, event):
        curItem = self.tvPokeList.focus()
        newSelectedPokeName = self.tvPokeList.item(curItem)['text']
        if newSelectedPokeName == '':
            return
        self.selectedPoke = self.__findPokemon(newSelectedPokeName)
        self.varPokeName.set(self.selectedPoke.dex['name'])
        self.varPokeFormName.set(self.selectedPoke.dex['form'])
        self.varPokeDexId.set(f'No.{self.selectedPoke.dexId}')
        character = (self.cboSeason.get(), self.rule, self.selectedPoke)
        if character != self.activeUsageCharacter:
            self.activeUsageCharacter = character
            self.__getUsage()

    def __getUsage(self):
        fullId = self.selectedPoke.fullId
        selectedPokeDex = self.selectedPoke.dex
        self.varPokeFormName.set(selectedPokeDex['form'])

        # 宝可梦图像
        imgPath = getPokemonImageFile(fullId)
        if imgPath != None:
            self.pokeIconImg = PIL.ImageTk.PhotoImage(PIL.Image.open(imgPath).resize((128, 128)))
            self.pokeIcon.configure(image=self.pokeIconImg)

        # 属性图标
        pokeTypeIcon = PIL.Image.new('RGBA', (48, 24))
        pokeTypeIcon.paste(self.typeIconImg[selectedPokeDex['type_1']], (0,0))
        if selectedPokeDex['type_2'] != '':
            pokeTypeIcon.paste(self.typeIconImg[selectedPokeDex['type_2']], (24,0))
        self.pokeTypeIconTk = PIL.ImageTk.PhotoImage(pokeTypeIcon)
        self.lblPokeTypeIcon.configure(image=self.pokeTypeIconTk)

        # 种族值
        self.__loadSpecies([selectedPokeDex['H'],
                            selectedPokeDex['A'],
                            selectedPokeDex['B'],
                            selectedPokeDex['C'],
                            selectedPokeDex['D'],
                            selectedPokeDex['S']])

        fullIdHome = f'{self.selectedPoke.dexId:04d}-{pokeHomeApi.pokeFormIdMapping(self.selectedPoke.dexId, self.selectedPoke.formId)[1]:03d}'
        argSeason = self.seasonInfoMap[self.cboSeason.get()]['season']
        titleSeason = self.seasonInfoMap[self.cboSeason.get()]['name']
        usage = self.home.getUsage(fullIdHome, argSeason, self.rule)
        rank = self.home.getRank(argSeason, self.rule)
        found = False
        for form in usage:
            if form == fullIdHome:
                # +性格效果说明
                for i in range(len(usage[form]['nature'])):
                    usage[form]['nature'][i] += \
                        f'{'　' if len(usage[form]['nature'][i]) <= 2 else ''}  {usage[form]['nature_effect'][i]}'
                self.fAbility.tvFill(usage[form]['ability'], usage[form]['ability_rate'])
                self.moveImgs = []
                for type in usage[form]['move_type']:
                    self.moveImgs.append(self.teraIconImgTk[type])
                self.fMove.tvFill(usage[form]['move'], usage[form]['move_rate'], self.moveImgs)
                self.fNature.tvFill(usage[form]['nature'], usage[form]['nature_rate'])
                self.fItem.tvFill(usage[form]['item'], usage[form]['item_rate'])
                self.teraImgs = []
                for type in usage[form]['terastal']:
                    self.teraImgs.append(self.teraIconImgTk[type])
                self.fTera.tvFill(usage[form]['terastal'], usage[form]['terastal_rate'], self.teraImgs)
                self.fPartner.tvFill(usage[form]['partner'])
                self.fDefeatPkm.tvFill(usage[form]['win_pkm'])
                self.winMoveImgs = []
                for type in usage[form]['win_move_type']:
                    self.winMoveImgs.append(self.teraIconImgTk[type])
                self.fDefeatMove.tvFill(usage[form]['win_move'], usage[form]['win_move_rate'], self.winMoveImgs)
                self.fLostPkm.tvFill(usage[form]['lose_pkm'])
                self.loseMoveImgs = []
                for type in usage[form]['lose_move_type']:
                    self.loseMoveImgs.append(self.teraIconImgTk[type])
                self.fLostMove.tvFill(usage[form]['lose_move'], usage[form]['lose_move_rate'], self.loseMoveImgs)
                found = True
                break
        if found == False:
            self.varTerm.set(f'{"双打对战" if self.rule == 1 else "单打对战"} {titleSeason} 无数据')
            self.fAbility.tvClear()
            self.fMove.tvClear()
            self.fNature.tvClear()
            self.fItem.tvClear()
            self.fTera.tvClear()
            self.fPartner.tvClear()
            self.fDefeatPkm.tvClear()
            self.fDefeatMove.tvClear()
            self.fLostPkm.tvClear()
            self.fLostMove.tvClear()
        else:
            self.varTerm.set(f'{"双打对战" if self.rule == 1 else "单打对战"} {titleSeason} 排名 {rank[fullIdHome] if fullIdHome in rank else '圈外'}')

    def __ruleSelect(self):
        self.rule = int(self.varRuleIsDouble.get())
        if self.varSearchPoke.get() == '':
            self.__searchPokemon()

    def __loadSpecies(self, species:list):
        for i in range(6):
            self.pbSpecies[i].configure(value=species[i])
            self.lblSpeciesValue[i].configure(text=f'{species[i]}')

    def __init__(self, theme='darkly') -> None:
        self.home = pokeHomeApi.pokeHomeLite(workDir)
        self.activeUsageCharacter = ()
        self.selectedPoke = None

        self.teraIconImg = {}
        self.typeIconImg = {}
        for typeName in TRADITIONAL_TYPE_ORDER:
            img = PIL.Image.open(f'{workDir}/raw/icon_type_{TRADITIONAL_TYPE_ORDER[typeName]}.png')
            self.teraIconImg[typeName] = img.resize((16, 16))
            self.typeIconImg[typeName] = img.resize((24, 24))

        self.dictFullIdPokemon = {}
        for pkm in self.home.zukan:
            for form in self.home.zukan[pkm]:
                if form == '0' and int(pkm) in pokeHomeApi.COMBINE_FORM_POKEMON:
                    self.dictFullIdPokemon[f"{int(pkm):04}-{int(form):03}"] = self.home.zukan[pkm][form]['name']
                else:
                    self.dictFullIdPokemon[f"{int(pkm):04}-{int(form):03}"] = self.home.zukan[pkm][form]['alias']

        self.main = ttk.Window('PokeHOME RankViewer')
        self.root = ttk.Frame(self.main, padding=10)
        self.style = ttk.Style()
        self.style.theme_use(theme)
        if theme in ('darkly'):
            self.tvLineColoring = self.style.colors.inputbg
        else:
            self.tvLineColoring = self.style.colors.active

        self.style.configure('Borderless.Treeview', borderwidth=0,
                             background=self.style.colors.bg, font=('微软雅黑', 10), rowheight=20)
        self.style.configure('cboSeason.TCombobox', postoffset=(0, 0, 140, 0))

        self.teraIconImgTk = {}
        for typeName in TRADITIONAL_TYPE_ORDER:
            self.teraIconImgTk[typeName] = PIL.ImageTk.PhotoImage(self.teraIconImg[typeName])

        # 行1: 查询设定, 宝可梦图标, 宝可梦概述, 特性使用率
        self.fLine1 = ttk.Frame(self.root, padding=(0, 0, 10, 5))
        self.fLine1.pack(fill=BOTH, expand=YES)

        ttk.Separator(self.root).pack(fill=X)
        # 行2: 招式, 性格, 道具, 太晶
        self.fLine2 = ttk.Frame(self.root, padding=(0, 10, 0, 10))
        self.fLine2.pack(fill=BOTH, expand=YES)

        ttk.Separator(self.root).pack(fill=X)
        # 行3: 同伴, 击倒的对手, 击倒的招式, 被击倒的对手, 被击倒的招式
        self.fLine3 = ttk.Frame(self.root, padding=(0, 10, 0, 10))
        self.fLine3.pack(fill=BOTH, expand=YES)

        # region fLine1

        self.fBlock1 = ttk.Frame(self.fLine1)
        # 宝可梦列表
        self.tvPokeList = ttk.Treeview(master=self.fBlock1, show=ttk.TREE)
        self.tvPokeList.bind('<<TreeviewSelect>>', self.__pokemonSelect)
        self.tvsbPokeList = ttk.Scrollbar(master=self.fBlock1, command=self.tvPokeList.yview)
        self.tvPokeList.configure(yscrollcommand=self.tvsbPokeList.set)

        # 搜索宝可梦
        self.varSearchPoke = ttk.StringVar()
        self.eSearchPoke = ttk.Entry(self.fBlock1, textvariable = self.varSearchPoke, width = 12)
        self.varSearchPoke.trace_add('write', self.__searchPokemon)

        # 赛季/规则行
        self.fSeason = ttk.Frame(self.fBlock1)
        # 选择赛季
        lblSeason = ttk.Label(self.fSeason, text='赛季:')
        self.cboSeason = ttk.Combobox(
            master=self.fSeason,
            state="readonly",
            style='cboSeason.TCombobox'
        )
        self.cboSeason.bind("<<ComboboxSelected>>", self.__selectSeasonCbo)

        now = datetime.datetime.now()
        seasonEnd = datetime.datetime.strptime(self.home.find_term(list(self.home.getSeasons().keys())[0])["end"], "%Y/%m/%d %H:%M")
        if now > seasonEnd:
            print('Updating season data')
            self.home.getSeasons(forceUpdate=True)
        self.cboSeason.configure(values=self.__getSeason())
        self.cboSeason.current(0)

        # 选择规则
        self.rule = 0
        self.varRuleIsDouble = ttk.Variable()
        self.cbRule = ttk.Checkbutton(
            master=self.fSeason, text="双打规则", bootstyle=(ttk.ROUND, ttk.TOGGLE),
            variable=self.varRuleIsDouble, command=self.__ruleSelect
        )
        # lblSeason.pack(side=LEFT)
        self.cboSeason.pack(side=LEFT)
        self.cbRule.pack(side=LEFT, fill=X, padx=5)
        self.cbRule.invoke()

        self.fSeason.pack(side=TOP, pady=10)
        self.eSearchPoke.pack(side=BOTTOM, fill=X, pady=10)
        self.tvsbPokeList.pack(side=RIGHT, fill=Y)
        self.tvPokeList.pack(side=RIGHT, fill=BOTH, expand=YES)

        self.__searchPokemon()
        self.fBlock1.pack(side=LEFT, fill=Y, expand=YES, anchor=W, padx=10)

        # 显示宝可梦
        self.fBlock2 = ttk.Frame(self.fLine1)

        self.varTerm = ttk.StringVar()
        self.lblTerm = ttk.Label(self.fBlock2, textvariable=self.varTerm, font=('微软雅黑', 16), width=20, padding=(20,10,0,0))
        self.lblTerm.pack(side=TOP,fill=X, expand=NO, anchor=N)

        self.fGrid1 = ttk.Frame(self.fBlock2)

        self.pokeIcon = ttk.Label(self.fBlock2)
        self.pokeType1Icon = ttk.Label(self.fBlock2)
        self.pokeType2Icon = ttk.Label(self.fBlock2)
        imgPath = getPokemonImageFile(0)
        if imgPath != None:
            self.pokeIconImg = PIL.ImageTk.PhotoImage(PIL.Image.open(imgPath).resize((128, 128)))
            self.pokeIcon.configure(image=self.pokeIconImg)
        self.pokeIcon.pack(side=LEFT,fill=BOTH, expand=YES, anchor=W, padx=10)

        self.pokeTypeIconTk = PIL.ImageTk.PhotoImage(PIL.Image.new('RGBA', (48,24)))
        self.fDexAndType = ttk.Frame(self.fGrid1)
        self.fDexAndType.grid(column=0, row=0, sticky=NW, pady=10)
        self.varPokeDexId = ttk.StringVar()
        self.lblPokeDexId = ttk.Label(self.fDexAndType, textvariable=self.varPokeDexId, font=('微软雅黑', 12), anchor=W, width=10)
        self.lblPokeDexId.pack(side=LEFT)
        self.lblPokeTypeIcon = ttk.Label(self.fDexAndType, anchor=N, width=10, image=self.pokeTypeIconTk)
        self.lblPokeTypeIcon.pack(side=LEFT)
        self.varPokeName = ttk.StringVar()
        self.pokeName = ttk.Label(self.fGrid1, textvariable=self.varPokeName, font=('微软雅黑', 24), anchor=W, width=10)
        self.pokeName.grid(column=0, row=1, sticky=NW)
        self.varPokeName.set('???')
        self.varPokeFormName = ttk.StringVar()
        self.pokeFormName = ttk.Label(self.fGrid1, textvariable=self.varPokeFormName, font=('微软雅黑', 12), anchor=W, width=16)
        self.pokeFormName.grid(column=0, row=2, sticky=NW)

        # 种族值显示
        self.fSpecies = ttk.Frame(self.fGrid1, padding=(0,10,0,20))
        self.fSpecies.grid(column=0, row=3, sticky=NW)
        self.lblSpecies = []
        self.pbSpecies = []
        self.lblSpeciesValue = []
        species = ['ＨＰ', '攻击', '防御', '特攻', '特防', '速度']
        for i, sp in enumerate(species):
            lblSpecies = ttk.Label(self.fSpecies, text=sp, font=('微软雅黑', 8), anchor=CENTER, padding=(5, 0, 5, 0))
            pbSpecies = ttk.Progressbar(
                master=self.fSpecies,
                orient=HORIZONTAL,
                maximum=255,
                value=0,
                bootstyle=(ttk.INFO, ttk.STRIPED),
            )
            lblSpeciesValue = ttk.Label(self.fSpecies, text='0', font=('微软雅黑', 8), anchor=CENTER, padding=(5, 0, 5, 0))
            lblSpecies.grid(column=0, row=0 + i, sticky=NW)
            pbSpecies.grid(column=1, row=0 + i, sticky=NW,pady=4)
            lblSpeciesValue.grid(column=2, row=0 + i, sticky=NW)
            self.lblSpecies.append(lblSpecies)
            self.pbSpecies.append(pbSpecies)
            self.lblSpeciesValue.append(lblSpeciesValue)
        # self.__loadSpecies([0,0,0,0,0,0])
        self.fGrid1.rowconfigure(0, weight=0)

        self.fGrid1.pack(side=LEFT,fill=BOTH, expand=YES, anchor=W)
        self.fBlock2.pack(side=LEFT, fill=Y, expand=YES, anchor=W, padx=10)

        menu = ttk.Menu(self.main)
        for i, t in enumerate(('清除赛季信息', '清除使用率排名信息', '清除详细信息', '清除所有信息')):
            menu.add_command(label=t, command=lambda x=i: self.deleteCache(x))

        mb = ttk.Menubutton(
            master=self.fLine1,
            text="清除缓存...",
            bootstyle=ttk.SECONDARY,
            menu=menu,
        )
        mb.pack(side=TOP, anchor=NE, pady=10)

        # 特性使用率
        self.fAbility = self.__treeviewWithTitleTemplate(self, self.fLine1, '特性', height=5)
        self.fAbility.pack(side=LEFT,fill=BOTH,expand=YES, anchor=E)
        # endregion

        # region fLine2
        self.fMove = self.__treeviewWithTitleTemplate(self, self.fLine2, '招式', withIcon=True)
        self.fNature = self.__treeviewWithTitleTemplate(self, self.fLine2, '性格', width=110)
        self.fItem = self.__treeviewWithTitleTemplate(self, self.fLine2, '道具')
        self.fTera = self.__treeviewWithTitleTemplate(self, self.fLine2, '太晶属性', width=24, withIcon=True)

        self.fMove.pack(side=LEFT,fill=BOTH,expand=YES,padx=10)
        self.fNature.pack(side=LEFT,fill=BOTH,expand=YES,padx=10)
        self.fItem.pack(side=LEFT,fill=BOTH,expand=YES,padx=10)
        self.fTera.pack(side=LEFT,fill=BOTH,expand=YES,padx=10)
        # endregion

        # region fLine3
        self.fPartner = self.__treeviewWithTitleTemplate(self, self.fLine3, '队伍的宝可梦', 'Pokemon')
        self.fDefeatPkm = self.__treeviewWithTitleTemplate(self, self.fLine3, '打倒的宝可梦', 'Pokemon')
        self.fDefeatMove = self.__treeviewWithTitleTemplate(self, self.fLine3, '打倒对手的招式', withIcon=True)
        self.fLostPkm = self.__treeviewWithTitleTemplate(self, self.fLine3, '被宝可梦打倒', 'Pokemon')
        self.fLostMove = self.__treeviewWithTitleTemplate(self, self.fLine3, '被打倒时的招式', withIcon=True)

        self.fPartner.pack(side=LEFT,fill=BOTH,expand=YES,padx=10)
        ttk.Separator(self.fLine3, orient='vertical').pack(side=LEFT, fill=Y)
        self.fDefeatPkm.pack(side=LEFT,fill=BOTH,expand=YES,padx=10)
        self.fDefeatMove.pack(side=LEFT,fill=BOTH,expand=YES,padx=10)
        ttk.Separator(self.fLine3, orient='vertical').pack(side=LEFT, fill=Y)
        self.fLostPkm.pack(side=LEFT,fill=BOTH,expand=YES,padx=10)
        self.fLostMove.pack(side=LEFT,fill=BOTH,expand=YES,padx=10)
        # endregion

        self.root.pack(fill=BOTH, expand=YES)

    def deleteCache(self, idx):
        if idx == 0:
            if os.path.isfile(f'{workDir}/cache/Season.json'):
                os.remove(f'{workDir}/cache/Season.json')
        elif idx == 1:
            for f in os.listdir(f'{workDir}/cache'):
                print(f)
                if f.endswith('.json') and f.startswith('Rank_S'):
                    os.remove(f'{workDir}/cache/{f}')
        elif idx == 2:
            for f in os.listdir(f'{workDir}/cache'):
                if f.endswith('.json') and f.startswith('pokemon_'):
                    os.remove(f'{workDir}/cache/{f}')
        elif idx == 3:
            for f in os.listdir(f'{workDir}/cache'):
                if f.endswith('.json'):
                    os.remove(f'{workDir}/cache/{f}')

    class __treeviewWithTitleTemplate(ttk.Frame):
        def __init__(self, __outer, master, heading, type:Literal['Attribute', 'Pokemon']='Attribute',
                     withIcon=False, width=100, height=10, padding=(5,0,5,5)) -> None:
            ttk.Frame.__init__(self, master)
            self.__outer = __outer
            self.type = type
            self.lblTitle = ttk.Label(self, text=heading, font=('微软雅黑', 12), anchor=CENTER, padding=(0,0,0,10))
            self.tvSheet = self.__treeviewTemplate(self, heading, withIcon, width=width, height=height, padding=padding)
            if self.type == 'Attribute':
                self.tvFill(['???','???','???'],[0,0,0])
            elif self.type == 'Pokemon':
                self.tvFill(['???','???','???'])
            self.lblTitle.pack(side=TOP, fill=X)
            self.tvSheet.pack(side=TOP,fill=BOTH)

        def __treeviewTemplate(self, master, heading, withIcon, width, height, padding=(5,0,5,5)) -> ttk.Treeview:
            if self.type == 'Attribute':
                columns = (0, 1)
            elif self.type == 'Pokemon':
                columns = (0)
            tv = ttk.Treeview(master=master, columns=columns, show=ttk.TREE, height=height, padding=padding,
                            style='Borderless.Treeview')
            tv.configure(selectmode='none')
            # tv.heading(0, text=heading)
            tv.column('#0', width=40 if withIcon == True else 0, stretch=False)
            if self.type == 'Attribute':
                tv.column('#1', width=width)
                tv.column('#2', width=55, anchor=E)
            elif self.type == 'Pokemon':
                tv.column('#1', width=width+40)
            return tv

        def tvFill(self, listKey:list, listRate:list=None, iconImage:list=None):
            for item in self.tvSheet.get_children():
                self.tvSheet.delete(item)
            for i in range(len(listKey)):
                item = self.tvSheet.insert("", END, tags='gray' if i % 2 == 0 else '')
                if listRate == None:
                    self.tvSheet.item(item, values=(f'{listKey[i]}'))
                else:
                    self.tvSheet.item(item, values=(f'{listKey[i]}', f'{listRate[i]:.1f}%'))
                if iconImage != None:
                    self.tvSheet.item(item, image=iconImage[i])
            self.tvSheet.tag_configure('gray', background=self.__outer.tvLineColoring)

        def tvClear(self):
            for item in self.tvSheet.get_children():
                self.tvSheet.delete(item)

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dark', help='Darkly mode', nargs='?', default=False)
    args = parser.parse_args()
    if args.dark != False:
        theme = 'darkly'
    else:
        theme = 'litera'
    window = pokeRankWindow(theme)
    window.mainloop()