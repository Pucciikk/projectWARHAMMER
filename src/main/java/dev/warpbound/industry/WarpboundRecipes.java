package dev.warpbound.industry;

import dev.warpbound.Warpbound;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.SimpleCookingSerializer;

public final class WarpboundRecipes {
    public static final RecipeType<SalvageRecipe> SALVAGING = Registry.register(BuiltInRegistries.RECIPE_TYPE,
            Warpbound.id("salvaging"), new RecipeType<SalvageRecipe>() {
                @Override
                public String toString() {
                    return "warpbound:salvaging";
                }
            });
    /** Горн работает чуть медленнее доменной печи: 200 тиков по умолчанию. */
    public static final RecipeSerializer<SalvageRecipe> SALVAGING_SERIALIZER = Registry.register(BuiltInRegistries.RECIPE_SERIALIZER,
            Warpbound.id("salvaging"), new SimpleCookingSerializer<>(SalvageRecipe::new, 200));

    private WarpboundRecipes() {
    }

    public static void register() {
    }
}
