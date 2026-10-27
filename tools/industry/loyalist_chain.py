#!/usr/bin/env python3
"""
Производственная цепочка лоялиста: сооружения, материалы и рецепты одной таблицей.

    python3 tools/industry/loyalist_chain.py [путь_к_html]

Пишет docs/industry/loyalist-chain.json (источник правды для будущих рецептов в датапаке)
и, если задан путь, интерактивную карту производства (HTML с данными внутри).
Цифры (время цикла, количества) — черновой баланс для расчёта пропорций, не финал.
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")

# ------------------------------------------------------------------ сооружения
# id: (название, размер, глава, группа, что это)
S = {}


def st(sid, name, size, ch, group, desc):
    S[sid] = dict(id=sid, name=name, size=size, ch=ch, group=group, desc=desc)


G_EXTRACT, G_METAL, G_CHEM, G_PARTS, G_ARMS, G_ARMOUR, G_GENE, G_SERVICE = (
    "Добыча", "Металлургия", "Химия и прометий", "Компоненты", "Оружие и боеприпасы", "Броня", "Генетика", "Служебные")

st("pick", "Кирка игрока", "—", 1, G_EXTRACT, "Ручная добыча: всё, что лежит в мире, можно копать как в ванилле.")
st("deep_drill", "Глубинный бур", "5×5×12", 4, G_EXTRACT,
   "Вышка, которая жрёт прометий как не в себя: руда по таблице мира без копания и без загрузки соседних чанков. Головки — расходник.")
st("pumpjack", "Насос-качалка", "3×5×6", 4, G_EXTRACT, "Ставится на залежь, найденную буровой разведки. Качает сырой прометий.")
st("water_intake", "Водозабор", "3×3×3", 2, G_EXTRACT, "Насос в любой воде или колодец. Вода — в трубы.")
st("air_condenser", "Атмосферный конденсатор", "3×3×5", 5, G_EXTRACT,
   "Разделяет воздух мира: азот и кислород. На мёртвых мирах ещё и ядовитые газы.")
st("lumber", "Лесопилка-культиватор", "5×5×4", 3, G_EXTRACT, "Саженцы растут под люменами, сервитор рубит. Брёвна, доски, опилки.")
st("hydroponics", "Гидропонный отсек", "5×3×4", 3, G_EXTRACT, "Любые ванильные растения без солнца; травы для ладана.")
st("corpse_mill", "Трупоперерабатывающий завод", "5×5×5", 6, G_EXTRACT,
   "Тела мобов → трупный крахмал и костная мука. Сырьё для растворов и пасты сервиторов.")

st("crusher", "Рудодробильня", "3×3×4", 2, G_METAL, "Обогащение ×2: руда → дроблёная руда, побочно гравий.")
st("wash_vat", "Промывочный чан", "3×3×3", 3, G_METAL, "Обогащение ×3: дроблёная руда в освящённой воде; побочно шлам и цинковая пыль.")
st("coke_oven", "Коксовая печь", "3×3×3", 2, G_METAL, "Уголь → кокс для домны; побочно каменноугольная смола.")
st("blast_furnace", "Домна Механикус", "5×5×7", 3, G_METAL, "Руда + кокс → чугун; побочно шлак (в цемент).")
st("converter", "Кислородный конвертер", "3×3×5", 3, G_METAL, "Чугун + кислород → сталь. Без кислорода сталь не варится.")
st("forge_smelter", "Плавильня Кузни", "пристройка", 2, G_METAL, "Пачечная плавка цветных металлов и сплавов (латунь, свинец, медь).")
st("induction", "Индукционная печь", "3×3×3", 6, G_METAL, "Быстрая плавка от сети без топлива; синтетические кристаллы.")
st("rolling_mill", "Прокатный стан", "7×3×3", 3, G_METAL, "Слиток → лист, пруток, труба; пруток → проволока.")
st("autoclave", "Полимерный автоклав", "3×3×4", 4, G_METAL, "Смола, армаплас, синтез пластали из стали и смолы.")
st("sinter", "Печь спекания", "5×5×5", 5, G_METAL, "Керамит: пласталь + пепельная керамика Кинериса при сильном жаре.")
st("ritual_forge", "Ритуальная кузня адамантия", "7×7×6", 7, G_METAL,
   "Фазовая ковка: нагрев → проковка → закалка в священном масле → литания. Сбой фазы — шлак.")
st("cement_mill", "Цементная мельница", "3×3×4", 4, G_METAL, "Рокрит и ферробетон из шлака, камня и гипса.")
st("radium_plant", "Обогатительная фабрика радия", "5×5×5", 5, G_METAL, "Радий Кинериса → радиевые ячейки; отходы — только в хранилище.")

st("distiller", "Перегонная колонна", "3×3×9+", 4, G_CHEM,
   "Сырой прометий → 4 фракции. Если фракцию не забирать, колонна встаёт.")
st("cracker", "Крекинг-установка", "3×3×5", 4, G_CHEM, "Тяжёлая фракция + водород → лёгкий прометий и битум.")
st("desulfurizer", "Сероочистка", "3×3×4", 4, G_CHEM, "Сернистый прометий + водород → чистый прометий и сера.")
st("electrolyzer", "Электролизёр", "3×3×3", 4, G_CHEM, "Вода → водород + кислород. Тяжёлая вода → дейтерий.")
st("centrifuge", "Центрифуга", "3×3×3", 5, G_CHEM, "Разделение: тяжёлая вода из воды; плазма и стволовые клетки из крови.")
st("chem_reactor", "Химический реактор", "3×3×4", 4, G_CHEM, "Кислоты, целлюлоза, регенерация отработанной кислоты.")
st("powder_works", "Пороховой цех", "5×3×4", 4, G_CHEM, "Нитроцеллюлоза, метательный заряд болта, фицелин. Взрывоопасно рядом с огнём.")
st("scriptorium", "Скрипторий", "5×5×5", 2, G_SERVICE, "Печати чистоты, ладан, освящённая вода, священное масло.")

st("forge", "Кузня Механикус", "5×5×6", 2, G_PARTS,
   "Центральный сборщик компонентов, растёт пристройками: волочильня, гравировальня, шлифовальня.")
st("cogitatorium", "Когитаторий", "5×5×4", 2, G_PARTS, "Платы, логические двигатели, ядра духа машины. Расшифровка СТК.")
st("press", "Ручной пресс", "1×2×1", 1, G_PARTS, "Ранний способ: шестерни и пластины вручную.")

st("armoury", "Оружейная мастерская", "5×5×4", 3, G_ARMS, "Сборка ручного оружия: лазганы, болтеры, цепные мечи, плазма.")
st("barrel_shop", "Ствольная мастерская", "7×3×3", 3, G_ARMS, "Нарезка стволов: труба + священное масло для резца.")
st("ammo_line", "Снаряжательная линия", "7×3×3", 3, G_ARMS, "Лазпакеты, гильзы, болт-снаряды, магазины, ленты, баллоны прометия.")
st("heavy_armoury", "Цех тяжёлого вооружения", "7×7×6", 6, G_ARMS, "Тяжёлый болтер, силовой кулак, лаз-пушка, плазменная пушка.")
st("plasma_works", "Плазменный цех", "5×5×5", 7, G_ARMS, "Плазменные колбы: дейтерий в магнитной ловушке.")

st("weavery", "Флак-мастерская", "5×3×3", 3, G_ARMOUR, "Ткань, флак-пластины, флак и карапакс.")
st("armour_line", "Конвейер силовой брони", "11×5×6", 7, G_ARMOUR, "Сборка силовой и терминаторской брони по этапам.")
st("armorium", "Арматорий", "5×5×7", 7, G_ARMOUR,
   "Облачение: серво-руки надевают доспех на Астартес и подключают его к Чёрному панцирю.")

st("solution_synth", "Синтезатор растворов", "3×3×4", 5, G_GENE,
   "Смешивает растворы; ванильные зелья заливаются по трубам как реагенты.")
st("analyzer", "Когитатор-анализатор", "3×3×3", 5, G_GENE, "Генный профиль образца; мини-игра совместимости.")
st("sequencer", "Генный секвенатор", "5×5×4", 6, G_GENE, "Геносемя легиона по рецепту гробницы; мини-игра сплайсинга.")
st("bio_vat", "Био-чан", "3×3×5", 5, G_GENE,
   "Выращивание органа: держать температуру, свет и подачу раствора. Сбой условий — орган гибнет.")
st("cryo", "Криохранилище", "3×3×3", 5, G_GENE, "Органы портятся за игровой день; в холоде — хранятся.")
st("apothecarion", "Ложе апотекариона", "5×3×3", 5, G_GENE,
   "Призыв апотекария; операция — мини-игра показателей. После операции модель игрока подрастает.")

st("coal_gen", "Угольный генераториум", "3×3×4", 2, G_SERVICE, "Первая мотивная сила.")
st("promethium_gen", "Прометиевый генераториум", "5×3×4", 4, G_SERVICE, "Энергия из прометия или прометиевого газа.")
st("radium_reactor", "Радиевый реактор", "5×5×6", 5, G_SERVICE, "Мощная энергия; облучает без свинцового экрана.")

# ------------------------------------------------------------------ материалы
# id: (название, вид, откуда берётся, если это сырьё)
I = {}


def it(iid, name, kind, src=None):
    I[iid] = dict(id=iid, name=name, kind=kind, src=src)


RAW, MAT, FLUID, PART, PRODUCT, BIO = "сырьё", "материал", "жидкость", "компонент", "изделие", "биоматериал"
for iid, name, src in [
    ("iron_ore", "Железная руда", "кирка / глубинный бур"), ("copper_ore", "Медная руда", "кирка / глубинный бур"),
    ("gold_ore", "Золотая руда", "кирка / глубинный бур"), ("coal", "Уголь", "кирка / глубинный бур"),
    ("redstone", "Редстоун", "кирка / глубинный бур"), ("quartz", "Кварц", "Незер / глубинный бур"),
    ("lead_ore", "Свинцовая руда", "кирка / глубинный бур"), ("sulfur_ore", "Серная руда", "у лавы, глубоко"),
    ("saltpeter", "Селитра", "наросты в пещерах и пустынях"), ("lapis", "Лазурит", "кирка / глубинный бур"),
    ("gravel", "Гравий", "лопата / каменоломня"), ("sand", "Песок", "лопата / каменоломня"), ("stone", "Камень", "кирка"),
    ("log", "Бревно", "топор / лесопилка"), ("string", "Нить", "пауки / лесопилка (лён)"), ("leather", "Кожа", "животные"),
    ("rotten_flesh", "Гнилая плоть", "мобы"), ("bone", "Кость", "мобы"), ("spider_eye", "Паучий глаз", "мобы"),
    ("raw_radium", "Сырой радий", "Кинерис"), ("ash_ceramic", "Пепельная керамика", "Кинерис"),
    ("raw_adamantium", "Сырой адамантий", "Кинерис, мир-кузница"),
    ("blood_sample", "Образец крови", "шприц: игрок, мобы, пленные"),
    ("progenoid", "Прогеноидная железа", "гробница Громового воина; павшие Астартес (редуктор)"),
    ("potion_regen", "Зелье регенерации", "варка / по трубе"), ("potion_strength", "Зелье силы", "варка / по трубе"),
    ("potion_healing", "Зелье исцеления", "варка / по трубе"), ("potion_weakness", "Зелье слабости", "варка / по трубе"),
    ("potion_water", "Зелье подводного дыхания", "варка / по трубе"), ("potion_night", "Зелье ночного зрения", "варка / по трубе"),
    ("potion_fire", "Зелье огнестойкости", "варка / по трубе"),
    ("legion_slate", "Инфопланшет рецепта легиона", "гробница Громового воина (сюжет гл. 5)"),
]:
    it(iid, name, RAW, src)
for iid, name, src in [("water", "Вода", "водозабор"), ("crude_promethium", "Сырой прометий", "насос-качалка"),
                       ("air", "Воздух", "атмосферный конденсатор")]:
    it(iid, name, FLUID, src)

for iid, name in [
    ("crushed_iron", "Дроблёная железная руда"), ("washed_iron", "Промытая железная руда"),
    ("crushed_copper", "Дроблёная медная руда"), ("washed_copper", "Промытая медная руда"),
    ("crushed_lead", "Дроблёная свинцовая руда"), ("coke", "Кокс"), ("pig_iron", "Чугун"), ("slag", "Шлак"),
    ("steel_ingot", "Стальной слиток"), ("steel_plate", "Стальной лист"), ("steel_rod", "Стальной пруток"),
    ("steel_wire", "Стальная проволока"), ("steel_tube", "Стальная труба"), ("copper_ingot", "Медный слиток"),
    ("copper_wire", "Медная проволока"), ("zinc_dust", "Цинковая пыль"), ("brass_ingot", "Латунный слиток"),
    ("lead_ingot", "Свинцовый слиток"), ("gold_ingot", "Золотой слиток"), ("sulfur", "Сера"), ("gypsum", "Гипс"),
    ("polymer_resin", "Полимерная смола"), ("armaplas", "Армаплас"), ("plasteel_ingot", "Пласталевый слиток"),
    ("plasteel_plate", "Пласталевый лист"), ("plasteel_tube", "Пласталевая труба"), ("ceramite_plate", "Керамитовая пластина"),
    ("adamantium_ingot", "Адамантиевый слиток"), ("rockrete", "Рокрит"), ("ferrocrete", "Ферробетон"),
    ("planks", "Доски"), ("sawdust", "Опилки"), ("cellulose", "Целлюлоза"), ("fabric", "Плотная ткань"),
    ("synthetic_crystal", "Синтетический кристалл"), ("herbs", "Травы"), ("incense", "Ладан"), ("purity_seal", "Печать чистоты"),
    ("parchment", "Пергамент"), ("bone_meal", "Костная мука"), ("corpse_starch", "Трупный крахмал"),
    ("radium_cell", "Радиевая ячейка"), ("rad_waste", "Радиоактивные отходы"), ("nitrocellulose", "Нитроцеллюлоза"),
    ("bolt_propellant", "Метательный заряд болта"), ("fyceline", "Фицелин (взрывчатка)"),
]:
    it(iid, name, MAT)
for iid, name in [
    ("holy_water", "Освящённая вода"), ("sludge", "Шлам"), ("coal_tar", "Каменноугольная смола"),
    ("oxygen", "Кислород"), ("hydrogen", "Водород"), ("nitrogen", "Азот"), ("heavy_water", "Тяжёлая вода"),
    ("deuterium", "Дейтерий"), ("heavy_fraction", "Тяжёлая фракция"), ("sour_promethium", "Сернистый прометий"),
    ("aromatics", "Ароматическая фракция"), ("promethium_gas", "Прометиевый газ («заряженные испарения»)"),
    ("promethium", "Прометий"), ("bitumen", "Битум"), ("sulfuric_acid", "Серная кислота"), ("nitric_acid", "Азотная кислота"),
    ("spent_acid", "Отработанная кислота"), ("sacred_oil", "Священное масло"),
]:
    it(iid, name, FLUID)
for iid, name in [
    ("brass_gear", "Латунная шестерня"), ("motive_coil", "Катушка мотивной силы"), ("servo_1", "Сервопривод I"),
    ("servo_2", "Сервопривод II"), ("cogitator_board", "Когитаторная плата"), ("logic_engine", "Логический двигатель"),
    ("capacitor", "Капаситор"), ("focusing_lens", "Фокусирующая линза"), ("vox_module", "Вокс-модуль"),
    ("mr_fuse", "Масс-реактивный взрыватель"), ("bolt_casing", "Гильза болта"), ("rifled_barrel", "Нарезной ствол"),
    ("heavy_barrel", "Тяжёлый ствол"), ("bolter_receiver", "Затворная группа болтера"), ("ammo_feed", "Ленточный подаватель"),
    ("suspensor", "Суспензор"), ("chain_teeth", "Зубья цепи"), ("chain_blade", "Цепное полотно"),
    ("field_generator", "Генератор силового поля"), ("containment_coil", "Катушка удержания"),
    ("fibre_bundle", "Электроволоконный пучок"), ("neural_interface", "Нейроразъём"), ("auto_senses", "Блок авточувств"),
    ("power_pack", "Ранцевый силовой блок"), ("crux_terminatus", "Крукс Терминатус"), ("teleport_homer", "Телепорт-маяк"),
    ("flak_plate", "Флак-пластина"), ("drill_head", "Буровая головка"),
]:
    it(iid, name, PART)
for iid, name in [
    ("lasgun", "Лазган"), ("las_cell", "Лазпакет"), ("bolt_round", "Болт-снаряд"), ("bolt_magazine", "Магазин болтера"),
    ("heavy_bolt_belt", "Лента тяжёлого болтера"), ("bolt_pistol", "Болт-пистолет"), ("bolter_guard", "Болтер «Гвардия» (человек)"),
    ("bolter_astartes", "Болтер Астартес"), ("storm_bolter", "Штормболтер"), ("heavy_bolter", "Тяжёлый болтер"),
    ("chainsword", "Цепной меч"), ("power_fist", "Силовой кулак"), ("promethium_canister", "Баллон прометия"),
    ("flamer", "Огнемёт"), ("plasma_flask", "Плазменная колба"), ("plasma_gun", "Плазмаган"),
    ("flak_armour", "Флак-броня (комплект)"), ("carapace_armour", "Карапакс (комплект)"),
    ("power_armour", "Силовая броня Mk VII (комплект)"), ("terminator_armour", "Тактический доспех дредноута (комплект)"),
]:
    it(iid, name, PRODUCT)
for iid, name in [
    ("blood_plasma", "Плазма крови"), ("stem_cells", "Стволовые клетки"), ("nutrient_medium", "Питательная среда"),
    ("immunosuppressant", "Иммуноподавитель"), ("growth_factor", "Фактор роста"), ("stabilizer", "Стабилизатор генома"),
    ("gene_profile", "Генный профиль (данные)"), ("geneseed_vial", "Колба геносемени легиона"),
    ("organ_heart", "Орган: второе сердце"), ("organ_lung", "Орган: многолёгкое"), ("organ_eye", "Орган: окулоба"),
    ("black_carapace", "Орган: Чёрный панцирь"),
]:
    it(iid, name, BIO)

# ------------------------------------------------------------------ рецепты: (сооружение, секунды, входы, выходы, заметка)
R = []


def rc(struct, t, ins, outs, note=""):
    R.append(dict(id=f"r{len(R)}", s=struct, t=t, i=[list(x) for x in ins], o=[list(x) for x in outs], note=note))


# металлургия: железо → сталь
rc("crusher", 4, [("iron_ore", 1)], [("crushed_iron", 2), ("gravel", 0.25)], "обогащение ×2")
rc("wash_vat", 6, [("crushed_iron", 2), ("holy_water", 1)], [("washed_iron", 3), ("sludge", 0.5)], "обогащение ×3")
rc("coke_oven", 12, [("coal", 2)], [("coke", 1), ("coal_tar", 0.5)])
rc("blast_furnace", 8, [("washed_iron", 2), ("coke", 1)], [("pig_iron", 2), ("slag", 1)])
rc("converter", 10, [("pig_iron", 3), ("oxygen", 1)], [("steel_ingot", 3), ("slag", 0.5)])
rc("rolling_mill", 3, [("steel_ingot", 1)], [("steel_plate", 1)])
rc("rolling_mill", 3, [("steel_ingot", 1)], [("steel_rod", 2)])
rc("rolling_mill", 4, [("steel_rod", 1)], [("steel_wire", 2)])
rc("rolling_mill", 6, [("steel_ingot", 2)], [("steel_tube", 1)])
# медь, латунь, свинец, золото
rc("crusher", 4, [("copper_ore", 1)], [("crushed_copper", 2)])
rc("wash_vat", 6, [("crushed_copper", 2), ("holy_water", 1)], [("washed_copper", 3)])
rc("forge_smelter", 4, [("washed_copper", 1)], [("copper_ingot", 1)])
rc("rolling_mill", 3, [("copper_ingot", 1)], [("copper_wire", 3)], "волочение")
rc("wash_vat", 6, [("gravel", 4), ("water", 1)], [("zinc_dust", 1), ("sand", 2)], "промывка гравия")
rc("forge_smelter", 6, [("copper_ingot", 3), ("zinc_dust", 1)], [("brass_ingot", 4)])
rc("crusher", 4, [("lead_ore", 1)], [("crushed_lead", 2)])
rc("forge_smelter", 4, [("crushed_lead", 1)], [("lead_ingot", 1)])
rc("forge_smelter", 4, [("gold_ore", 1)], [("gold_ingot", 1)])
# прометий
rc("distiller", 10, [("crude_promethium", 10)],
   [("sour_promethium", 4), ("heavy_fraction", 3), ("aromatics", 2), ("promethium_gas", 1)], "4 фракции")
rc("desulfurizer", 6, [("sour_promethium", 4), ("hydrogen", 1)], [("promethium", 4), ("sulfur", 1)])
rc("cracker", 8, [("heavy_fraction", 4), ("hydrogen", 1)], [("sour_promethium", 2), ("bitumen", 1)], "крекинг")
rc("autoclave", 8, [("bitumen", 2), ("water", 1)], [("polymer_resin", 2)])
rc("autoclave", 10, [("polymer_resin", 2), ("string", 4)], [("armaplas", 2)])
rc("autoclave", 12, [("steel_ingot", 2), ("polymer_resin", 1)], [("plasteel_ingot", 2)], "синтез пластали")
rc("rolling_mill", 3, [("plasteel_ingot", 1)], [("plasteel_plate", 1)])
rc("rolling_mill", 6, [("plasteel_ingot", 2)], [("plasteel_tube", 1)])
# газы и вода
rc("electrolyzer", 6, [("water", 2)], [("hydrogen", 2), ("oxygen", 1)])
rc("air_condenser", 8, [("air", 4)], [("nitrogen", 3), ("oxygen", 1)])
rc("centrifuge", 20, [("water", 20)], [("heavy_water", 1)], "изотопы")
rc("electrolyzer", 8, [("heavy_water", 2)], [("deuterium", 2), ("oxygen", 1)])
# кислоты и взрывчатка
rc("chem_reactor", 6, [("sulfur", 1), ("water", 2), ("oxygen", 1)], [("sulfuric_acid", 2)])
rc("crusher", 4, [("sulfur_ore", 1)], [("sulfur", 2)])
rc("chem_reactor", 8, [("saltpeter", 2), ("sulfuric_acid", 1)], [("nitric_acid", 2), ("gypsum", 1)])
rc("chem_reactor", 10, [("spent_acid", 2)], [("sulfuric_acid", 1), ("water", 1)], "регенерация (замкнуть цикл)")
rc("lumber", 6, [("log", 1)], [("planks", 4), ("sawdust", 2)])
rc("chem_reactor", 8, [("sawdust", 4), ("water", 1)], [("cellulose", 2)])
rc("powder_works", 10, [("cellulose", 2), ("nitric_acid", 1), ("sulfuric_acid", 1)], [("nitrocellulose", 2), ("spent_acid", 1)],
   "нитрация")
rc("powder_works", 8, [("nitrocellulose", 2), ("aromatics", 1)], [("bolt_propellant", 4)])
rc("powder_works", 12, [("aromatics", 2), ("nitric_acid", 2), ("sulfuric_acid", 1)], [("fyceline", 2), ("spent_acid", 1)])
# скрипторий и обряды
rc("hydroponics", 20, [("water", 2), ("bone_meal", 1)], [("herbs", 4)])
rc("scriptorium", 6, [("herbs", 2), ("coal_tar", 1)], [("incense", 2)])
rc("scriptorium", 4, [("water", 4), ("incense", 1)], [("holy_water", 4)])
rc("scriptorium", 6, [("promethium", 1), ("incense", 1)], [("sacred_oil", 2)], "трижды благословлённое")
rc("scriptorium", 4, [("sawdust", 4), ("water", 1)], [("parchment", 2)])
rc("scriptorium", 6, [("parchment", 1), ("coal_tar", 0.5)], [("purity_seal", 2)], "воск из смолы")
rc("corpse_mill", 10, [("rotten_flesh", 4), ("bone", 2)], [("corpse_starch", 2), ("bone_meal", 2)])
# стройматериалы
rc("cement_mill", 8, [("slag", 2), ("stone", 2), ("gypsum", 1), ("water", 1)], [("rockrete", 6)])
rc("cement_mill", 8, [("rockrete", 4), ("steel_rod", 1)], [("ferrocrete", 4)])
# Кинерис и высшие материалы
rc("sinter", 20, [("plasteel_plate", 1), ("ash_ceramic", 2)], [("ceramite_plate", 1)])
rc("radium_plant", 15, [("raw_radium", 4), ("lead_ingot", 1)], [("radium_cell", 2), ("rad_waste", 1)])
rc("ritual_forge", 40, [("raw_adamantium", 2), ("sacred_oil", 1), ("purity_seal", 1)], [("adamantium_ingot", 1), ("slag", 1)],
   "фазовая ковка")
# компоненты
rc("forge", 3, [("brass_ingot", 1)], [("brass_gear", 2)], "или ручной пресс")
rc("forge", 6, [("copper_wire", 4), ("steel_rod", 1)], [("motive_coil", 1)], "волочильня")
rc("forge", 8, [("brass_gear", 2), ("motive_coil", 1), ("steel_plate", 1)], [("servo_1", 1)])
rc("forge", 12, [("servo_1", 1), ("plasteel_plate", 1), ("cogitator_board", 1)], [("servo_2", 1)])
rc("cogitatorium", 8, [("copper_wire", 3), ("redstone", 2), ("quartz", 1)], [("cogitator_board", 1)], "гравировальня")
rc("cogitatorium", 20, [("cogitator_board", 4), ("gold_ingot", 1), ("sulfuric_acid", 1)], [("logic_engine", 1)], "травление")
rc("forge", 6, [("copper_wire", 2), ("lead_ingot", 1), ("armaplas", 1)], [("capacitor", 2)])
rc("induction", 10, [("quartz", 2), ("sand", 2)], [("synthetic_crystal", 1)])
rc("forge", 8, [("synthetic_crystal", 1), ("brass_ingot", 1)], [("focusing_lens", 1)], "шлифовальня")
rc("forge", 6, [("copper_wire", 2), ("cogitator_board", 1), ("brass_ingot", 1)], [("vox_module", 1)])
rc("forge", 6, [("brass_ingot", 1), ("redstone", 1), ("quartz", 1)], [("mr_fuse", 4)])
rc("forge", 10, [("motive_coil", 4), ("ceramite_plate", 1), ("logic_engine", 1)], [("containment_coil", 1)])
rc("forge", 15, [("motive_coil", 2), ("logic_engine", 1), ("gold_ingot", 2)], [("suspensor", 1)])
rc("forge", 12, [("radium_cell", 1), ("motive_coil", 2), ("ceramite_plate", 1)], [("field_generator", 1)])
rc("forge", 4, [("plasteel_plate", 1)], [("chain_teeth", 8)])
rc("forge", 6, [("chain_teeth", 16), ("steel_rod", 2)], [("chain_blade", 1)])
rc("forge", 10, [("servo_1", 1), ("steel_plate", 2), ("brass_gear", 4)], [("ammo_feed", 1)])
rc("forge", 20, [("logic_engine", 1), ("gold_ingot", 1), ("fibre_bundle", 1)], [("neural_interface", 1)])
rc("forge", 20, [("focusing_lens", 2), ("logic_engine", 1), ("vox_module", 1)], [("auto_senses", 1)])
rc("forge", 30, [("ceramite_plate", 2), ("motive_coil", 4), ("radium_cell", 1), ("logic_engine", 1)], [("power_pack", 1)])
rc("forge", 15, [("vox_module", 1), ("radium_cell", 1), ("logic_engine", 1)], [("teleport_homer", 1)])
rc("forge", 8, [("steel_plate", 2), ("adamantium_ingot", 0.25)], [("drill_head", 1)], "расходник бура")
rc("ritual_forge", 30, [("adamantium_ingot", 1), ("gold_ingot", 2), ("purity_seal", 2)], [("crux_terminatus", 1)])
# оружие и боеприпасы
rc("barrel_shop", 20, [("steel_tube", 1), ("sacred_oil", 0.5)], [("rifled_barrel", 1)], "масло для резца")
rc("barrel_shop", 30, [("plasteel_tube", 1), ("sacred_oil", 1)], [("heavy_barrel", 1)])
rc("armoury", 15, [("steel_plate", 2), ("servo_1", 1), ("brass_gear", 2), ("mr_fuse", 1)], [("bolter_receiver", 1)])
rc("ammo_line", 3, [("brass_ingot", 1)], [("bolt_casing", 4)])
rc("ammo_line", 6, [("bolt_casing", 4), ("bolt_propellant", 4), ("fyceline", 1), ("mr_fuse", 4), ("steel_rod", 1)],
   [("bolt_round", 4)], ".75 калибр, масс-реактивный")
rc("ammo_line", 4, [("bolt_round", 20), ("steel_plate", 1)], [("bolt_magazine", 1)])
rc("ammo_line", 6, [("bolt_round", 40), ("steel_wire", 2), ("armaplas", 1)], [("heavy_bolt_belt", 1)])
rc("ammo_line", 4, [("capacitor", 1), ("lead_ingot", 1), ("armaplas", 1)], [("las_cell", 2)], "зарядка — в сети")
rc("ammo_line", 3, [("steel_plate", 1), ("promethium", 4)], [("promethium_canister", 1)])
rc("armoury", 20, [("focusing_lens", 1), ("capacitor", 1), ("steel_tube", 1), ("planks", 2), ("cogitator_board", 1)],
   [("lasgun", 1)])
rc("armoury", 20, [("rifled_barrel", 1), ("bolter_receiver", 1), ("steel_plate", 2)], [("bolt_pistol", 1)])
rc("armoury", 30, [("rifled_barrel", 1), ("bolter_receiver", 1), ("steel_plate", 3), ("planks", 2)], [("bolter_guard", 1)],
   "тяжёлое для человека")
rc("armoury", 40, [("heavy_barrel", 1), ("bolter_receiver", 1), ("ceramite_plate", 2), ("cogitator_board", 1)],
   [("bolter_astartes", 1)], "образец Годвин")
rc("armoury", 45, [("heavy_barrel", 2), ("bolter_receiver", 2), ("ammo_feed", 1), ("ceramite_plate", 2)], [("storm_bolter", 1)])
rc("heavy_armoury", 90, [("heavy_barrel", 1), ("bolter_receiver", 2), ("servo_2", 1), ("ammo_feed", 1), ("suspensor", 1),
                         ("ceramite_plate", 3), ("logic_engine", 1)], [("heavy_bolter", 1)], "у Астартес — без суспензора не поднять")
rc("armoury", 20, [("chain_blade", 1), ("servo_1", 1), ("brass_gear", 2), ("steel_plate", 1)], [("chainsword", 1)])
rc("heavy_armoury", 80, [("field_generator", 1), ("servo_2", 3), ("ceramite_plate", 3), ("adamantium_ingot", 1)], [("power_fist", 1)])
rc("armoury", 25, [("steel_tube", 2), ("servo_1", 1), ("promethium_canister", 1)], [("flamer", 1)])
rc("plasma_works", 30, [("deuterium", 2), ("containment_coil", 1), ("plasteel_plate", 1)], [("plasma_flask", 1)])
rc("armoury", 60, [("containment_coil", 2), ("plasteel_tube", 1), ("ceramite_plate", 1), ("logic_engine", 1)], [("plasma_gun", 1)])
# броня
rc("weavery", 6, [("string", 4)], [("fabric", 2)])
rc("weavery", 8, [("fabric", 2), ("armaplas", 1)], [("flak_plate", 2)])
rc("weavery", 30, [("flak_plate", 8), ("fabric", 6), ("leather", 2)], [("flak_armour", 1)])
rc("weavery", 40, [("armaplas", 6), ("plasteel_plate", 4), ("fabric", 4)], [("carapace_armour", 1)])
rc("armour_line", 300, [("ceramite_plate", 12), ("fibre_bundle", 8), ("power_pack", 1), ("auto_senses", 1),
                        ("neural_interface", 2), ("servo_2", 4), ("adamantium_ingot", 2)], [("power_armour", 1)])
rc("armour_line", 600, [("ceramite_plate", 20), ("adamantium_ingot", 8), ("fibre_bundle", 12), ("power_pack", 2),
                        ("crux_terminatus", 1), ("teleport_homer", 1), ("servo_2", 6), ("storm_bolter", 1), ("power_fist", 1)],
   [("terminator_armour", 1)], "со штормболтером и силовым кулаком")
# генетика
rc("solution_synth", 10, [("water", 4), ("corpse_starch", 2), ("potion_regen", 1)], [("nutrient_medium", 4)])
rc("solution_synth", 10, [("potion_weakness", 1), ("spider_eye", 1), ("water", 2)], [("immunosuppressant", 2)])
rc("solution_synth", 12, [("potion_strength", 1), ("bone_meal", 2), ("nutrient_medium", 1)], [("growth_factor", 2)])
rc("solution_synth", 12, [("potion_healing", 1), ("lapis", 1), ("water", 2)], [("stabilizer", 2)], "Громовой воин")
rc("centrifuge", 10, [("blood_sample", 2)], [("blood_plasma", 1), ("stem_cells", 1)])
rc("analyzer", 30, [("progenoid", 1), ("blood_plasma", 1)], [("gene_profile", 1)], "мини-игра совместимости")
rc("sequencer", 120, [("progenoid", 1), ("gene_profile", 1), ("legion_slate", 0), ("growth_factor", 1), ("stabilizer", 1)],
   [("geneseed_vial", 1)], "мини-игра сплайсинга")
rc("bio_vat", 900, [("geneseed_vial", 0.25), ("stem_cells", 2), ("nutrient_medium", 6), ("growth_factor", 2),
                    ("immunosuppressant", 1)], [("organ_heart", 1)], "держать 37°, свет, раствор")
rc("bio_vat", 900, [("geneseed_vial", 0.25), ("stem_cells", 2), ("nutrient_medium", 6), ("growth_factor", 2),
                    ("potion_water", 2)], [("organ_lung", 1)], "многолёгкое — дышать ядом")
rc("bio_vat", 900, [("geneseed_vial", 0.25), ("stem_cells", 2), ("nutrient_medium", 6), ("growth_factor", 2),
                    ("potion_night", 2)], [("organ_eye", 1)], "окулоба — ночное зрение")
rc("bio_vat", 1800, [("geneseed_vial", 0.5), ("stem_cells", 4), ("nutrient_medium", 10), ("fibre_bundle", 4),
                     ("neural_interface", 2), ("potion_fire", 1)], [("black_carapace", 1)], "последний орган: связь с силовой бронёй")
rc("bio_vat", 120, [("nutrient_medium", 2), ("string", 4), ("copper_wire", 2)], [("fibre_bundle", 1)], "искусственные мышцы")

# ------------------------------------------------------------------ процедуры (не рецепты: действия игрока)
PROC = [
    dict(name="Путь Астартес", steps=[
        ("Образцы", "кровь шприцем, прогеноиды из гробницы Громового воина или с павших Астартес"),
        ("Центрифуга", "кровь → плазма и стволовые клетки"),
        ("Когитатор-анализатор", "генный профиль прогеноида: мини-игра совместимости"),
        ("Генный секвенатор", "геносемя легиона по инфопланшету: мини-игра сплайсинга"),
        ("Синтезатор растворов", "питательная среда, фактор роста, иммуноподавитель; зелья — по трубам"),
        ("Био-чан", "орган растёт 15–30 минут; держать температуру, свет люменов и подачу раствора"),
        ("Криохранилище", "готовый орган портится за игровой день, в холоде хранится"),
        ("Ложе апотекариона", "вызвать апотекария (челнок по маяку); операция — мини-игра показателей"),
        ("Генокарта", "орган светится, даёт способность; модель игрока подрастает"),
        ("Арматорий", "после Чёрного панциря: серво-руки надевают силовую броню"),
    ]),
]

GROUP_ORDER = [G_EXTRACT, G_METAL, G_CHEM, G_PARTS, G_ARMS, G_ARMOUR, G_GENE, G_SERVICE]
TARGETS = ["heavy_bolter", "bolt_magazine", "bolter_astartes", "bolt_pistol", "storm_bolter", "terminator_armour",
           "power_armour", "lasgun", "chainsword", "flamer", "plasma_gun", "flak_armour", "carapace_armour",
           "organ_heart", "black_carapace", "geneseed_vial", "steel_ingot", "plasteel_plate", "ceramite_plate",
           "adamantium_ingot", "promethium", "sacred_oil", "fyceline", "bolt_propellant"]


def check():
    """Все предметы в рецептах объявлены; у каждого не-сырья есть рецепт."""
    made = {o[0] for r in R for o in r["o"]}
    for r in R:
        assert r["s"] in S, r
        for x in r["i"] + r["o"]:
            assert x[0] in I, x
    missing = [i for i, v in I.items() if v["kind"] not in (RAW,) and v["src"] is None and i not in made]
    assert not missing, missing


def main():
    check()
    data = dict(structures=S, items=I, recipes=R, procedures=PROC, groups=GROUP_ORDER, targets=TARGETS)
    out = os.path.join(ROOT, "docs", "industry", "loyalist-chain.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("сооружений", len(S), "материалов", len(I), "рецептов", len(R))
    if len(sys.argv) > 1:
        tpl = open(os.path.join(os.path.dirname(__file__), "chain_map.html"), encoding="utf-8").read()
        with open(sys.argv[1], "w", encoding="utf-8") as f:
            f.write(tpl.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False)))
        print("карта:", sys.argv[1])


if __name__ == "__main__":
    main()
