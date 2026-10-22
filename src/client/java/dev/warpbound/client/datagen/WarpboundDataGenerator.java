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
