package dev.warpbound.client.industry;

import dev.warpbound.industry.SalvageForgeMenu;
import net.minecraft.client.gui.screens.inventory.AbstractFurnaceScreen;
import net.minecraft.client.gui.screens.recipebook.BlastingRecipeBookComponent;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Inventory;

/** Экран горна обломков. Пока на ванильной текстуре доменной печи — до текстур автора. */
public class SalvageForgeScreen extends AbstractFurnaceScreen<SalvageForgeMenu> {
    private static final ResourceLocation LIT = ResourceLocation.withDefaultNamespace("container/blast_furnace/lit_progress");
    private static final ResourceLocation BURN = ResourceLocation.withDefaultNamespace("container/blast_furnace/burn_progress");
    private static final ResourceLocation TEXTURE = ResourceLocation.withDefaultNamespace("textures/gui/container/blast_furnace.png");

    public SalvageForgeScreen(SalvageForgeMenu menu, Inventory inventory, Component title) {
        super(menu, new BlastingRecipeBookComponent(), inventory, title, TEXTURE, LIT, BURN);
    }
}
