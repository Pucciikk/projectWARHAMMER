package dev.warpbound.industry;

import dev.warpbound.core.WarpboundBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.level.block.entity.AbstractFurnaceBlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Горн обломков: печь, которая знает только рецепты переплавки корабельного лома. */
public class SalvageForgeBlockEntity extends AbstractFurnaceBlockEntity {
    public SalvageForgeBlockEntity(BlockPos pos, BlockState state) {
        super(WarpboundBlockEntities.SALVAGE_FORGE, pos, state, WarpboundRecipes.SALVAGING);
    }

    @Override
    protected Component getDefaultName() {
        return Component.translatable("block.warpbound.salvage_forge");
    }

    @Override
    protected AbstractContainerMenu createMenu(int id, Inventory inventory) {
        return new SalvageForgeMenu(id, inventory, this, dataAccess);
    }
}
