package dev.warpbound.core;

import dev.warpbound.Warpbound;
import dev.warpbound.industry.SalvageForgeBlockEntity;
import dev.warpbound.shipyard.ShipyardBlockEntity;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.block.entity.BlockEntityType;

public final class WarpboundBlockEntities {
    public static final BlockEntityType<ShipyardBlockEntity> SHIPYARD = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE,
            Warpbound.id("shipyard"), BlockEntityType.Builder.of(ShipyardBlockEntity::new, WarpboundBlocks.SHIPYARD_CONSOLE).build(null));

    public static final BlockEntityType<SalvageForgeBlockEntity> SALVAGE_FORGE = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE,
            Warpbound.id("salvage_forge"), BlockEntityType.Builder.of(SalvageForgeBlockEntity::new, WarpboundBlocks.SALVAGE_FORGE).build(null));

    private WarpboundBlockEntities() {
    }

    public static void register() {
    }
}
