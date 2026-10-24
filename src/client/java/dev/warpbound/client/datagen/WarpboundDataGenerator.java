package dev.warpbound.client.datagen;

import net.fabricmc.fabric.api.datagen.v1.DataGeneratorEntrypoint;
import net.fabricmc.fabric.api.datagen.v1.FabricDataGenerator;
import net.fabricmc.fabric.api.datagen.v1.FabricDataOutput;
import net.fabricmc.fabric.api.datagen.v1.provider.FabricLanguageProvider;
import net.minecraft.core.HolderLookup;

import java.util.concurrent.CompletableFuture;

/**
 * Датаген: ./gradlew runDatagen пишет файлы в src/main/generated.
 * Пока только переводы; модели, рецепты и лут главы 1 лежат в resources руками.
 */
public class WarpboundDataGenerator implements DataGeneratorEntrypoint {
    @Override
    public void onInitializeDataGenerator(FabricDataGenerator generator) {
        FabricDataGenerator.Pack pack = generator.createPack();
        pack.addProvider(RussianLang::new);
        pack.addProvider(EnglishLang::new);
    }

    private static class RussianLang extends FabricLanguageProvider {
        RussianLang(FabricDataOutput output, CompletableFuture<HolderLookup.Provider> registries) {
            super(output, "ru_ru", registries);
        }

        @Override
        public void generateTranslations(HolderLookup.Provider registries, TranslationBuilder builder) {
            builder.add("modmenu.nameTranslation.warpbound", "Warpbound");
            builder.add("warpbound.ship_interior", "Борт корабля");
            builder.add("entity.warpbound.dreadnought", "Дредноут");
            builder.add("item.warpbound.dreadnought_spawn_egg", "Яйцо призыва дредноута");
            builder.add("itemGroup.warpbound.main", "Warpbound");
            builder.add("block.warpbound.hull_plating", "Обшивка корабля");
            builder.add("block.warpbound.scorched_hull_plating", "Обгоревшая обшивка");
            builder.add("block.warpbound.vox_beacon", "Вокс-маяк капсулы");
            builder.add("block.warpbound.brass_trim", "Латунный пояс обшивки");
            builder.add("block.warpbound.salvage_forge", "Горн обломков");
            builder.add("block.warpbound.manual_press", "Ручной пресс");
            builder.add("block.warpbound.manual_press.die", "Штамп: %s");
            builder.add("block.warpbound.manual_press.die.gear", "шестерня");
            builder.add("block.warpbound.manual_press.die.plate", "пластина");
            builder.add("item.warpbound.plasteel_ingot", "Пластальной слиток");
            builder.add("item.warpbound.plasteel_blend", "Пластальная шихта");
            builder.add("item.warpbound.plasteel_blend.tooltip", "Долго плавится в горне обломков, если корабельного лома не осталось");
            builder.add("item.warpbound.brass_ingot", "Латунный слиток");
            builder.add("item.warpbound.plasteel_plate", "Пластальная пластина");
            builder.add("item.warpbound.brass_gear", "Латунная шестерня");
            builder.add("block.warpbound.nav_table", "Навигационный стол");
            builder.add("block.warpbound.auspex", "Ауспик");
            builder.add("block.warpbound.geller_node", "Узел Поля Геллера");
            builder.add("block.warpbound.reactor_core", "Ядро реактора");
            builder.add("block.warpbound.teleportarium_pad", "Площадка телепортариума");
            builder.add("item.warpbound.teleport_homer", "Телепорт-маяк");
            builder.add("item.warpbound.teleport_homer.tooltip", "ПКМ на планете — подняться на свой корабль, если он на орбите");
            builder.add("nav.warpbound.title", "Навигационный стол");
            builder.add("nav.warpbound.jump", "Проложить курс");
            builder.add("nav.warpbound.here", "Мы здесь");
            builder.add("destination.warpbound.overworld", "Родной мир (орбита)");
            builder.add("destination.warpbound.kineris", "Кинерис Терциус");
            builder.add("ship.warpbound.arrived", "Корабль вышел в реальное пространство: %s");
            builder.add("ship.warpbound.course_set", "Курс проложен: %s. Прыжок вслепую — да хранит нас Император");
            builder.add("ship.warpbound.not_your_ship", "Это не ваш корабль");
            builder.add("ship.warpbound.in_warp", "Корабль в варпе: курс не сменить до выхода");
            builder.add("ship.warpbound.teleport_in_warp", "Телепортариум мёртв: в варпе за бортом только безумие");
            builder.add("ship.warpbound.no_world", "Под кораблём нет мира для высадки");
            builder.add("ship.warpbound.no_ship", "У вас нет корабля");
            builder.add("ship.warpbound.not_in_orbit_here", "Ваш корабль не на орбите этого мира");
            builder.add("ship.warpbound.hull_unbreakable", "Отсеки корабля собраны из модулей: их не сломать");
            builder.add("item.warpbound.shipyard_schematic", "Схема стапеля");
            builder.add("item.warpbound.shipyard_schematic.tooltip", "Нужна, чтобы собрать пульт верфи");
            builder.add("block.warpbound.dock_girder", "Балка стапеля");
            builder.add("block.warpbound.shipyard_console", "Пульт верфи");
            builder.add("item.warpbound.omnissian_key", "Омниссианский ключ");
            builder.add("item.warpbound.omnissian_key.tooltip", "ПКМ по ядру машины — освятить (собрать). Shift+ПКМ — разобрать");
            builder.add("multiblock.warpbound.air", "Пустота");
            builder.add("multiblock.warpbound.use_key", "Машина освящена. Разобрать её можно только Омниссианским ключом (Shift+ПКМ)");
            builder.add("multiblock.warpbound.already_formed", "Машина уже освящена");
            builder.add("multiblock.warpbound.formed", "Дух машины пробудился: %s");
            builder.add("multiblock.warpbound.unformed", "Машина разобрана. Блоки на месте");
            builder.add("multiblock.warpbound.not_formed", "Машина не собрана: несовпадений %s. Жёлтым подсвечено, чего не хватает, красным — лишнее");
            builder.add("multiblock.warpbound.wrong_blocks", " • Чужие блоки на месте частей: %s");
            builder.add("multiblock.warpbound.shipyard", "Стапель верфи");
            builder.add("shipyard.warpbound.title", "Верфь");
            builder.add("shipyard.warpbound.not_formed", "Стапель не освящён. Соберите раму и ударьте по пульту Омниссианским ключом");
            builder.add("shipyard.warpbound.cannot_unform", "Нельзя разобрать верфь, пока в доке строится корабль");
            builder.add("shipyard.warpbound.dock_blocked", "Док занят: мешают блоков %s (подсвечены красным)");
            builder.add("shipyard.warpbound.already_has_ship", "У вас уже есть корабль");
            builder.add("shipyard.warpbound.default_ship_name", "Безымянный фрегат");
            builder.add("shipyard.warpbound.launched", "Корабль «%s» ушёл на орбиту в синем пламени варпа. /wb ship enter — подняться на борт");
            builder.add("shipyard.warpbound.deposit", "Сдать");
            builder.add("shipyard.warpbound.start_stage", "Начать этап");
            builder.add("shipyard.warpbound.launch", "Старт");
            builder.add("shipyard.warpbound.requirements", "Поставки этапа:");
            builder.add("shipyard.warpbound.building", "Идёт работа: %s с");
            builder.add("shipyard.warpbound.ready", "Корабль готов к старту");
            builder.add("shipyard.warpbound.launching", "Варп-огонь разгорается…");
            builder.add("ship_class.warpbound.frigate", "Фрегат");
            builder.add("shipyard.warpbound.stage.keel", "Киль");
            builder.add("shipyard.warpbound.stage.hull", "Корпус");
            builder.add("shipyard.warpbound.stage.reactor", "Реактор");
            builder.add("shipyard.warpbound.stage.warp_engine", "Варп-двигатель");
            builder.add("shipyard.warpbound.stage.geller_field", "Поле Геллера");
            builder.add("shipyard.warpbound.stage.modules", "Отсеки");
            builder.add("item.warpbound.data_slate_storm", "Инфопланшет (журнал мостика)");
            builder.add("item.warpbound.data_slate_navigator", "Инфопланшет (шпиль Навигатора)");
            builder.add("item.warpbound.data_slate_ship", "Инфопланшет (реестр корабля)");
            builder.add("item.warpbound.data_slate.tooltip", "ПКМ — прочитать запись");
            builder.add("item.warpbound.vox_module", "Вокс-модуль");
            builder.add("item.warpbound.vox_module.tooltip", "Деталь для починки вокс-маяка");
            builder.add("item.warpbound.omnissiah_sigil", "Знак Омниссии");
            builder.add("item.warpbound.omnissiah_sigil.tooltip", "ПКМ по маяку — освятить. Shift+ПКМ — осквернить");
            builder.add("item.warpbound.forge_schematic", "Схема Кузни Механикус");
            builder.add("item.warpbound.forge_schematic.tooltip", "Понадобится, когда появятся исследования");
            builder.add("item.warpbound.obelisk_schematic", "Схема Варп-обелиска");
            builder.add("item.warpbound.obelisk_schematic.tooltip", "Понадобится, когда появятся исследования");
            builder.add("item.warpbound.tech_priest_spawn_egg", "Яйцо призыва техножреца");
            builder.add("item.warpbound.dark_tech_priest_spawn_egg", "Яйцо призыва тёмного техножреца");
            builder.add("entity.warpbound.tech_priest", "Техножрец");
            builder.add("entity.warpbound.dark_tech_priest", "Тёмный техножрец");
            builder.add("key.categories.warpbound", "Warpbound");
            builder.add("key.warpbound.quests", "Журнал памяти");
            builder.add("slate.warpbound.storm.title", "ЖУРНАЛ МОСТИКА");
            builder.add("slate.warpbound.storm.text", "+++ ЗАПИСЬ ПОВРЕЖДЕНА +++\nШторм поднялся из ниоткуда. Течения варпа развернулись против нас, будто их кто-то повернул.\nПоле Геллера: сорок процентов. Тридцать. Капитан приказал готовить спасательные капсулы.\n[ДАННЫЕ УТРАЧЕНЫ]");
            builder.add("slate.warpbound.navigator.title", "ШПИЛЬ НАВИГАТОРА");
            builder.add("slate.warpbound.navigator.text", "...это не буря, капитан! Оно смотрит на нас! Оно знает ваше имя!..\n...оно забирает его...\n+++ СИГНАЛ ПРЕРВАН. ШПИЛЬ НЕ ОТВЕЧАЕТ +++");
            builder.add("slate.warpbound.ship.title", "РЕЕСТР КОРАБЛЯ");
            builder.add("slate.warpbound.ship.text", "КОРАБЛЬ: [СТЁРТО]\nКЛАСС: [СТЁРТО]\nВЛАДЕЛЕЦ ПАТЕНТА: [СТЁРТО]\nГЕРБ ДОМА: выжжен.\nПоследняя запись: «Если кто-то найдёт это, знайте: мы были...»");
        }
    }

    private static class EnglishLang extends FabricLanguageProvider {
        EnglishLang(FabricDataOutput output, CompletableFuture<HolderLookup.Provider> registries) {
            super(output, "en_us", registries);
        }

        @Override
        public void generateTranslations(HolderLookup.Provider registries, TranslationBuilder builder) {
            builder.add("modmenu.nameTranslation.warpbound", "Warpbound");
            builder.add("warpbound.ship_interior", "Shipboard");
            builder.add("entity.warpbound.dreadnought", "Dreadnought");
            builder.add("item.warpbound.dreadnought_spawn_egg", "Dreadnought Spawn Egg");
            builder.add("itemGroup.warpbound.main", "Warpbound");
            builder.add("block.warpbound.hull_plating", "Hull Plating");
            builder.add("block.warpbound.scorched_hull_plating", "Scorched Hull Plating");
            builder.add("block.warpbound.vox_beacon", "Escape Pod Vox Beacon");
            builder.add("block.warpbound.brass_trim", "Brass Hull Trim");
            builder.add("block.warpbound.salvage_forge", "Salvage Forge");
            builder.add("block.warpbound.manual_press", "Manual Press");
            builder.add("block.warpbound.manual_press.die", "Die: %s");
            builder.add("block.warpbound.manual_press.die.gear", "gear");
            builder.add("block.warpbound.manual_press.die.plate", "plate");
            builder.add("item.warpbound.plasteel_ingot", "Plasteel Ingot");
            builder.add("item.warpbound.plasteel_blend", "Plasteel Blend");
            builder.add("item.warpbound.plasteel_blend.tooltip", "Slowly smelts in a Salvage Forge once the ship scrap runs out");
            builder.add("item.warpbound.brass_ingot", "Brass Ingot");
            builder.add("item.warpbound.plasteel_plate", "Plasteel Plate");
            builder.add("item.warpbound.brass_gear", "Brass Gear");
            builder.add("block.warpbound.nav_table", "Navigation Table");
            builder.add("block.warpbound.auspex", "Auspex");
            builder.add("block.warpbound.geller_node", "Geller Field Node");
            builder.add("block.warpbound.reactor_core", "Reactor Core");
            builder.add("block.warpbound.teleportarium_pad", "Teleportarium Pad");
            builder.add("item.warpbound.teleport_homer", "Teleport Homer");
            builder.add("item.warpbound.teleport_homer.tooltip", "Use on a planet to beam up to your ship, if it is in orbit");
            builder.add("nav.warpbound.title", "Navigation Table");
            builder.add("nav.warpbound.jump", "Plot course");
            builder.add("nav.warpbound.here", "We are here");
            builder.add("destination.warpbound.overworld", "Home world (orbit)");
            builder.add("destination.warpbound.kineris", "Kineris Tertius");
            builder.add("ship.warpbound.arrived", "The ship has returned to real space: %s");
            builder.add("ship.warpbound.course_set", "Course plotted: %s. A blind jump — may the Emperor protect us");
            builder.add("ship.warpbound.not_your_ship", "This is not your ship");
            builder.add("ship.warpbound.in_warp", "The ship is in the warp: the course cannot change until we exit");
            builder.add("ship.warpbound.teleport_in_warp", "The teleportarium is dead: beyond the hull there is only madness");
            builder.add("ship.warpbound.no_world", "There is no world below the ship to land on");
            builder.add("ship.warpbound.no_ship", "You have no ship");
            builder.add("ship.warpbound.not_in_orbit_here", "Your ship is not in orbit of this world");
            builder.add("ship.warpbound.hull_unbreakable", "The compartments are built from modules: they cannot be broken");
            builder.add("item.warpbound.shipyard_schematic", "Slipway Schematic");
            builder.add("item.warpbound.shipyard_schematic.tooltip", "Needed to assemble a Shipyard Console");
            builder.add("block.warpbound.dock_girder", "Dock Girder");
            builder.add("block.warpbound.shipyard_console", "Shipyard Console");
            builder.add("item.warpbound.omnissian_key", "Omnissian Key");
            builder.add("item.warpbound.omnissian_key.tooltip", "Use on a machine core to sanctify (assemble). Sneak-use to disassemble");
            builder.add("multiblock.warpbound.air", "Empty space");
            builder.add("multiblock.warpbound.use_key", "This machine is sanctified. Only an Omnissian Key can take it apart (sneak-use)");
            builder.add("multiblock.warpbound.already_formed", "The machine is already sanctified");
            builder.add("multiblock.warpbound.formed", "The machine spirit awakens: %s");
            builder.add("multiblock.warpbound.unformed", "Machine disassembled. The blocks stay in place");
            builder.add("multiblock.warpbound.not_formed", "Not assembled: %s mismatches. Yellow marks what is missing, red marks what is in the way");
            builder.add("multiblock.warpbound.wrong_blocks", " • Foreign blocks where parts belong: %s");
            builder.add("multiblock.warpbound.shipyard", "Shipyard Slipway");
            builder.add("shipyard.warpbound.title", "Shipyard");
            builder.add("shipyard.warpbound.not_formed", "The slipway is not sanctified. Build the frame and strike the console with an Omnissian Key");
            builder.add("shipyard.warpbound.cannot_unform", "Cannot disassemble the shipyard while a ship is being built");
            builder.add("shipyard.warpbound.dock_blocked", "The dock is obstructed by %s blocks (marked red)");
            builder.add("shipyard.warpbound.already_has_ship", "You already own a ship");
            builder.add("shipyard.warpbound.default_ship_name", "Nameless Frigate");
            builder.add("shipyard.warpbound.launched", "The \"%s\" rose to orbit in blue warp-fire. /wb ship enter to go aboard");
            builder.add("shipyard.warpbound.deposit", "Deposit");
            builder.add("shipyard.warpbound.start_stage", "Begin stage");
            builder.add("shipyard.warpbound.launch", "Launch");
            builder.add("shipyard.warpbound.requirements", "Stage deliveries:");
            builder.add("shipyard.warpbound.building", "Work in progress: %s s");
            builder.add("shipyard.warpbound.ready", "The ship is ready to launch");
            builder.add("shipyard.warpbound.launching", "Warp-fire kindles…");
            builder.add("ship_class.warpbound.frigate", "Frigate");
            builder.add("shipyard.warpbound.stage.keel", "Keel");
            builder.add("shipyard.warpbound.stage.hull", "Hull");
            builder.add("shipyard.warpbound.stage.reactor", "Reactor");
            builder.add("shipyard.warpbound.stage.warp_engine", "Warp Drive");
            builder.add("shipyard.warpbound.stage.geller_field", "Geller Field");
            builder.add("shipyard.warpbound.stage.modules", "Compartments");
            builder.add("item.warpbound.data_slate_storm", "Data-Slate (Bridge Log)");
            builder.add("item.warpbound.data_slate_navigator", "Data-Slate (Navigator's Spire)");
            builder.add("item.warpbound.data_slate_ship", "Data-Slate (Ship Registry)");
            builder.add("item.warpbound.data_slate.tooltip", "Right-click to read");
            builder.add("item.warpbound.vox_module", "Vox Module");
            builder.add("item.warpbound.vox_module.tooltip", "Part for repairing the vox beacon");
            builder.add("item.warpbound.omnissiah_sigil", "Sigil of the Omnissiah");
            builder.add("item.warpbound.omnissiah_sigil.tooltip", "Use on the beacon to sanctify. Sneak-use to desecrate");
            builder.add("item.warpbound.forge_schematic", "Mechanicus Forge Schematic");
            builder.add("item.warpbound.forge_schematic.tooltip", "Needed once research arrives");
            builder.add("item.warpbound.obelisk_schematic", "Warp Obelisk Schematic");
            builder.add("item.warpbound.obelisk_schematic.tooltip", "Needed once research arrives");
            builder.add("item.warpbound.tech_priest_spawn_egg", "Tech-Priest Spawn Egg");
            builder.add("item.warpbound.dark_tech_priest_spawn_egg", "Dark Tech-Priest Spawn Egg");
            builder.add("entity.warpbound.tech_priest", "Tech-Priest");
            builder.add("entity.warpbound.dark_tech_priest", "Dark Tech-Priest");
            builder.add("key.categories.warpbound", "Warpbound");
            builder.add("key.warpbound.quests", "Memory Journal");
            builder.add("slate.warpbound.storm.title", "BRIDGE LOG");
            builder.add("slate.warpbound.storm.text", "+++ RECORD CORRUPTED +++\nThe storm rose out of nowhere. The warp currents turned against us, as if someone turned them.\nGeller Field: forty percent. Thirty. The captain ordered the escape pods readied.\n[DATA LOST]");
            builder.add("slate.warpbound.navigator.title", "NAVIGATOR'S SPIRE");
            builder.add("slate.warpbound.navigator.text", "...this is no storm, captain! It is watching us! It knows your name!..\n...it is taking it...\n+++ SIGNAL LOST. THE SPIRE IS SILENT +++");
            builder.add("slate.warpbound.ship.title", "SHIP REGISTRY");
            builder.add("slate.warpbound.ship.text", "VESSEL: [ERASED]\nCLASS: [ERASED]\nWARRANT HOLDER: [ERASED]\nHOUSE HERALDRY: burned away.\nLast entry: \"If anyone finds this, know that we were...\"");
        }
    }
}
