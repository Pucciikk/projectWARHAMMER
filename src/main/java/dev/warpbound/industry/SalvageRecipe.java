package dev.warpbound.industry;

import dev.warpbound.core.WarpboundBlocks;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.AbstractCookingRecipe;
import net.minecraft.world.item.crafting.CookingBookCategory;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeSerializer;

/** Рецепт горна обломков: один предмет на входе, один на выходе, как у печи. Тип — warpbound:salvaging. */
public class SalvageRecipe extends AbstractCookingRecipe {
    public SalvageRecipe(String group, CookingBookCategory category, Ingredient ingredient, ItemStack result,
                         float experience, int cookingTime) {
        super(WarpboundRecipes.SALVAGING, group, category, ingredient, result, experience, cookingTime);
    }

    @Override
    public ItemStack getToastSymbol() {
        return new ItemStack(WarpboundBlocks.SALVAGE_FORGE);
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return WarpboundRecipes.SALVAGING_SERIALIZER;
    }
}
