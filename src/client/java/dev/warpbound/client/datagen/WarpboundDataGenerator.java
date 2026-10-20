package dev.warpbound.client.datagen;

import net.fabricmc.fabric.api.datagen.v1.DataGeneratorEntrypoint;
import net.fabricmc.fabric.api.datagen.v1.FabricDataGenerator;
import net.fabricmc.fabric.api.datagen.v1.FabricDataOutput;
import net.fabricmc.fabric.api.datagen.v1.provider.FabricLanguageProvider;
import net.minecraft.core.HolderLookup;

import java.util.concurrent.CompletableFuture;

/**
 * Датаген: ./gradlew runDatagen пишет файлы в src/main/generated.
 * Пока только переводы; модели, рецепты и лут добавим вместе с предметами.
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
        }
    }
}
