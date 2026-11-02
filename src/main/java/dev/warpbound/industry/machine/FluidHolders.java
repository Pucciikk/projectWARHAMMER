package dev.warpbound.industry.machine;

import dev.warpbound.Warpbound;
import dev.warpbound.core.WarpboundBlocks;
import net.fabricmc.fabric.api.transfer.v1.fluid.FluidStorage;
import net.fabricmc.fabric.api.transfer.v1.item.ItemStorage;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.block.entity.BlockEntityType;

/** Сущность бака и горелки: отдельным классом, чтобы блоки могли сослаться на неё до регистрации. */
public final class FluidHolders {
    public static final BlockEntityType<FluidHolderBlockEntity> TYPE = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE, Warpbound.id("fluid_holder"),
            BlockEntityType.Builder.of(FluidHolderBlockEntity::new, WarpboundBlocks.FLUID_TANK, WarpboundBlocks.FLARE_STACK).build(null));

    public static final BlockEntityType<ConveyorBlockEntity> CONVEYOR = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE, Warpbound.id("conveyor"),
            BlockEntityType.Builder.of(ConveyorBlockEntity::new, WarpboundBlocks.CONVEYOR).build(null));

    public static final BlockEntityType<FluidPipeBlockEntity> PIPE = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE, Warpbound.id("fluid_pipe"),
            BlockEntityType.Builder.of(FluidPipeBlockEntity::new, WarpboundBlocks.FLUID_PIPE).build(null));

    private FluidHolders() {
    }

    public static void register() {
        FluidStorage.SIDED.registerForBlockEntity((be, side) -> be.port(side), TYPE);
        ItemStorage.SIDED.registerForBlockEntity((be, side) -> side == null ? null : be.port(side), CONVEYOR);
    }
}
