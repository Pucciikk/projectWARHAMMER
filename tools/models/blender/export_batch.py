"""
Строит и выгружает машины пачкой: в Blender выполнить exec этого файла, затем run("chem_reactor", ...).
Настройки экспорта каждой машины записаны здесь, чтобы перевыгрузка давала тот же результат.
"""
import os
import time
import traceback

HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"

# скрипт -> (имя блока, смещение ядра по Y, размер атласа, дополнительные настройки)
BATCH = {
    "chem_reactor": ("chem_reactor", 1.0, 1024, {}),
    "powder_works": ("powder_works", 1.0, 1024, {}),
    "cement_mill": ("cement_mill", 1.0, 1024, {}),
    "cracker": ("cracker", 1.0, 1024, {}),
    "promethium_gen": ("promethium_gen", 1.0, 1024, {}),
    "hydroponics": ("hydroponics", 1.0, 1024, {}),
    "lumber": ("lumber", 2.0, 1024, {}),
    "deep_drill": ("deep_drill", 2.0, 1024, {}),
    "manual_press": ("manual_press", 0.5, 1024, dict(work_name="work.strike", work_loop=False,
                                                     idle={"loop": True, "animation_length": 3.0, "bones": {}})),
    "salvage_forge": ("salvage_forge", 1.0, 1024, {}),
}


GUNS = {"lasgun": "lasgun_3d", "bolter": "bolter_3d"}


def run_gun(*names):
    """Оружие: меш с атласом 2048 (видно вплотную) и клипы рук."""
    for n in names or GUNS:
        t = time.time()
        try:
            ns = {}
            exec(open(os.path.join(HERE, "guns", n + ".py"), encoding="utf-8").read(), ns)
            exec(open(os.path.join(HERE, "export_machine.py"), encoding="utf-8").read(), ns)
            model = GUNS[n]
            ns["machine_export"](model, {}, 1.0, core_offset_y=0.0, size=2048, folder="item", locators=("arm_r", "arm_l", "muzzle", "eject"))
            ns["export_clips"](model, ns["CLIPS"])
            print(n, "готово за", round(time.time() - t), "с")
        except Exception:
            print(n, "ОШИБКА\n" + traceback.format_exc())


def run(*names):
    for n in names:
        block, core, size, extra = BATCH[n]
        t = time.time()
        try:
            ns = {}
            exec(open(os.path.join(HERE, n + ".py"), encoding="utf-8").read(), ns)
            exec(open(os.path.join(HERE, "export_machine.py"), encoding="utf-8").read(), ns)
            tr, length = ns["tracks"]()
            if n == "salvage_forge":
                extra = dict(extra, idle=ns["idle_tracks"]())
            ns["machine_export"](block, tr, length, core_offset_y=core, size=size, **extra)
            print(n, "готово за", round(time.time() - t), "с")
        except Exception:
            print(n, "ОШИБКА\n" + traceback.format_exc())
