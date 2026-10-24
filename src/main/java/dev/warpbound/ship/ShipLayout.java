package dev.warpbound.ship;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import dev.warpbound.core.DataRegistry;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceLocation;

import java.util.List;

/**
 * Раскладка интерьера корабля из data/&lt;ns&gt;/ship_layout/*.json: какие отсеки и где.
 * Смещения — от центра палубы участка, нос смотрит на +Z.
 */
public record ShipLayout(List<Compartment> compartments, BlockPos spawn) {
    public static final Codec<ShipLayout> CODEC = RecordCodecBuilder.create(i -> i.group(
            Compartment.CODEC.listOf().fieldOf("compartments").forGetter(ShipLayout::compartments),
            BlockPos.CODEC.fieldOf("spawn").forGetter(ShipLayout::spawn)
    ).apply(i, ShipLayout::new));

    public static final DataRegistry<ShipLayout> REGISTRY = new DataRegistry<>("ship_layout", CODEC);

    public record Compartment(ResourceLocation structure, BlockPos offset) {
        public static final Codec<Compartment> CODEC = RecordCodecBuilder.create(i -> i.group(
                ResourceLocation.CODEC.fieldOf("structure").forGetter(Compartment::structure),
                BlockPos.CODEC.fieldOf("offset").forGetter(Compartment::offset)
        ).apply(i, Compartment::new));
    }

    public static void register() {
    }
}
