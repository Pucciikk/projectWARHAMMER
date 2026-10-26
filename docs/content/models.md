# Контракт моделей: как заменить заглушку своей моделью

Заглушки делают скрипты `tools/models/gen_entities.py` (сущности) и `tools/models/gen_blocks.py` (машины).
Своя модель встаёт на место заглушки без правок кода, если совпадают имена файлов, костей и анимаций.

## Сущности (Blockbench → «GeckoLib Animated Model»)

Файлы (`<имя>` — id сущности):

| Что | Куда |
|---|---|
| геометрия | `assets/warpbound/geo/entity/<имя>.geo.json` |
| анимации | `assets/warpbound/animations/entity/<имя>.animation.json` |
| текстура | `assets/warpbound/textures/entity/<имя>.png` |
| свечение | `assets/warpbound/textures/entity/<имя>_glow.png` — только светящиеся пиксели, остальное прозрачно |

Масштаб: 16 пикселей модели = 1 блок, ноги на y = 0, перед смотрит в −Z (север), правая рука — в −X.

**Кости.** Обязательны: `body`, `head` (поворачивается за взглядом), `right_arm`, `left_arm`, `right_leg`, `left_leg`.
Оружие и инструмент — в `right_item` / `left_item` (дочерние кости рук). Навесное — отдельными костями.

**Анимации** (имена как в GeckoLib DefaultAnimations):

| Имя | Когда | Петля |
|---|---|---|
| `misc.idle` | стоит | да |
| `move.walk` | идёт | да |
| `move.run` | идёт в бою (кому нужно) | да |
| `attack.swing` | удар | нет |
| `attack.shoot` | выстрел | нет |
| `attack.cast` | колдовство, призыв | нет |
| `misc.interact` | техножрец благословляет | нет |
| `work.repair` | сервитор чинит | да |
| `misc.rest` | сервитор выключен | держать последний кадр |
| `misc.transform` | превращение жреца в демона, 3 с | нет |
| `misc.deploy` | десантный модуль раскрывается; челнок разжимает захваты; капсула открывает двери | держать последний кадр |
| `move.fly` | челнок в полёте (опоры убраны); капсула на тормозных соплах | да |
| `misc.land` | челнок на вертикальной тяге и на опорах | да |
| `misc.summon` | варп-разлом: весь ритуал призыва, 11,5 с | держать последний кадр |

**Особые кости и текстуры:**

| Сущность | Что |
|---|---|
| `tech_priest` | `servo_arm`…`servo_arm_3`, `servo_drill`, `mechadendrite_a/b/c` (+`_2`…`_5`, `_tip`), `robe_right/left`, `censer`, `mantle`, `hood`; топор — `left_item` |
| `dark_tech_priest` | своя модель: люлька `body`, ноги `leg_<front/back>_<right/left>` (+`_2`), малые руки `right_arm/left_arm` (+`_fore`), клешня `claw_arm`…`_3` → `right_item` с `claw_upper/lower`, ствол `gun_arm` → `left_item`, `gut`, `tumor`, `halo`, `tentacle_1..4` (+`_2`…`_4`) |
| `shuttle` | головы нет; `hull`, `turret`, `gear_<front/back>_<left/right>` (+`_2`), `clamp_left/right`, `capsule` (прячется после сброса), `thrust_*`, `exhaust_*` |
| `drop_capsule` | `body`, `door_left`, `door_right`, `thrusters` |
| `warp_rift` | `sigil`, `ring`, `column` — знак и столб пламени, всё светится |
| `pink_horror` | общая модель с синим ужасом (рисуется в 0.62 размера), текстура `blue_horror.png` |
| `cultist` | кости `knife`, `autogun`, `stubber` внутри `right_item` — видна одна по варианту; текстуры `cultist.png`, `cultist_1.png`, `cultist_2.png` |
| `possessed_priest` | кости демона `daemon_horns`, `daemon_jaw`, `daemon_spine`, `daemon_claw_right`, `daemon_claw_left` скрыты в фазе 1; во фазе 2 текстура `possessed_priest_daemon.png`, модель растёт в 1.58 раза |
| `servitor` | `mechadendrite_*` не нужны; инструменты в `right_item` (сварка) и `left_item` (клешня) |
| `boarding_pod` | кости `hull`, `petal_north`, `petal_south`, `petal_east`, `petal_west`; головы нет |

Рост (хитбокс) — в `WarpboundEntities`; если модель другого роста, поправлю хитбокс.

## Машины и оборудование (Blockbench → «Java Block/Item»)

Файл модели — `assets/warpbound/models/block/<имя>.json`, перед смотрит на север (блок сам поворачивается к игроку).
Состояния — отдельные модели: `vox_beacon` / `vox_beacon_broken`, `salvage_forge` / `salvage_forge_on`,
`manual_press` / `manual_press_down`. Остальные: `shipyard_console`, `nav_table`, `auspex`, `geller_node`,
`reactor_core`, `teleportarium_pad`, `command_throne`. Модель может выходить за блок (до −16…32), но хитбокс
лучше держать в блоке; если выходит — скажи, поправлю форму.

Анимированные машины (крутится, качается) — GeckoLib-блоки, их подключим отдельно по мере готовности моделей.
