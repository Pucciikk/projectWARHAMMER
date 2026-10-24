package dev.warpbound.industry;

import dev.warpbound.core.WarpboundMenus;
import net.minecraft.world.Container;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.AbstractFurnaceMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.RecipeBookType;

public class SalvageForgeMenu extends AbstractFurnaceMenu {
    public SalvageForgeMenu(int id, Inventory inventory) {
        super(WarpboundMenus.SALVAGE_FORGE, WarpboundRecipes.SALVAGING, RecipeBookType.BLAST_FURNACE, id, inventory);
    }

    public SalvageForgeMenu(int id, Inventory inventory, Container container, ContainerData data) {
        super(WarpboundMenus.SALVAGE_FORGE, WarpboundRecipes.SALVAGING, RecipeBookType.BLAST_FURNACE, id, inventory, container, data);
    }
}
