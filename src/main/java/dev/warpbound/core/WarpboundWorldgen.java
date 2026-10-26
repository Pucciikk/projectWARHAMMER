package dev.warpbound.core;

import dev.warpbound.Warpbound;
import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.levelgen.GenerationStep;

/**
 * Генерация в Overworld: свинцовая руда (глубоко, часто — каталог, раздел 2.1).
 * Сами фичи — в data/warpbound/worldgen; руды Кинериса появятся вместе с его генератором мира.
 */
public final class WarpboundWorldgen {
    private WarpboundWorldgen() {
    }

    public static void register() {
        BiomeModifications.addFeature(BiomeSelectors.foundInOverworld(), GenerationStep.Decoration.UNDERGROUND_ORES,
                ResourceKey.create(Registries.PLACED_FEATURE, Warpbound.id("lead_ore")));
    }
}
