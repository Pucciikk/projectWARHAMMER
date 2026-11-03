package dev.warpbound.core;

import dev.warpbound.Warpbound;
import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.levelgen.GenerationStep;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;

/**
 * Генерация в Overworld: свинцовая и серная руды, селитра, выходы прометия над залежами (каталог, раздел 2.1).
 * Сами фичи — в data/warpbound/worldgen; руды Кинериса появятся вместе с его генератором мира.
 */
public final class WarpboundWorldgen {
    private WarpboundWorldgen() {
    }

    public static void register() {
        Registry.register(BuiltInRegistries.FEATURE, Warpbound.id("promethium_seep"),
                new dev.warpbound.industry.PromethiumSeepFeature(NoneFeatureConfiguration.CODEC));
        for (String ore : new String[]{"lead_ore", "sulfur_ore", "saltpeter_ore"}) {
            BiomeModifications.addFeature(BiomeSelectors.foundInOverworld(), GenerationStep.Decoration.UNDERGROUND_ORES,
                    ResourceKey.create(Registries.PLACED_FEATURE, Warpbound.id(ore)));
        }
        BiomeModifications.addFeature(BiomeSelectors.foundInOverworld(), GenerationStep.Decoration.VEGETAL_DECORATION,
                ResourceKey.create(Registries.PLACED_FEATURE, Warpbound.id("promethium_seep")));
    }
}
