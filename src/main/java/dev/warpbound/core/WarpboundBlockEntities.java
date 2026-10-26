package dev.warpbound.core;

import dev.warpbound.Warpbound;
import dev.warpbound.industry.ManualPressBlockEntity;
import dev.warpbound.industry.MechanicusForgeBlockEntity;
import dev.warpbound.industry.SalvageForgeBlockEntity;
import dev.warpbound.multiblock.MachinePartBlockEntity;
import dev.warpbound.ship.block.ShipFixtureBlockEntity;
import dev.warpbound.shipyard.ShipyardBlockEntity;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.block.entity.BlockEntityType;

public final class WarpboundBlockEntities {
    public static final BlockEntityType<ShipyardBlockEntity> SHIPYARD = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE,
            Warpbound.id("shipyard"), BlockEntityType.Builder.of(ShipyardBlockEntity::new, WarpboundBlocks.SHIPYARD_CONSOLE).build(null));

    public static final BlockEntityType<SalvageForgeBlockEntity> SALVAGE_FORGE = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE,
            Warpbound.id("salvage_forge"), BlockEntityType.Builder.of(SalvageForgeBlockEntity::new, WarpboundBlocks.SALVAGE_FORGE).build(null));

    public static final BlockEntityType<ManualPressBlockEntity> MANUAL_PRESS = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE,
            Warpbound.id("manual_press"), BlockEntityType.Builder.of(ManualPressBlockEntity::new, WarpboundBlocks.MANUAL_PRESS).build(null));

    public static final BlockEntityType<MechanicusForgeBlockEntity> MECHANICUS_FORGE = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE,
            Warpbound.id("mechanicus_forge"), BlockEntityType.Builder.of(MechanicusForgeBlockEntity::new, WarpboundBlocks.MECHANICUS_FORGE).build(null));

    public static final BlockEntityType<ShipFixtureBlockEntity> SHIP_FIXTURE = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE,
            Warpbound.id("ship_fixture"), BlockEntityType.Builder.of(ShipFixtureBlockEntity::new, WarpboundBlocks.REACTOR_CORE,
                    WarpboundBlocks.GELLER_NODE, WarpboundBlocks.NAV_TABLE, WarpboundBlocks.AUSPEX, WarpboundBlocks.TELEPORTARIUM_PAD,
                    WarpboundBlocks.COMMAND_CONSOLE).build(null));

    public static final BlockEntityType<MachinePartBlockEntity> MACHINE_PART = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE,
            Warpbound.id("machine_part"), BlockEntityType.Builder.of(MachinePartBlockEntity::new, WarpboundBlocks.MACHINE_PART).build(null));

    private WarpboundBlockEntities() {
    }

    public static void register() {
    }
}
