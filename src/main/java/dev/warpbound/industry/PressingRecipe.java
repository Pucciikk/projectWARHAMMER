package dev.warpbound.industry;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/**
 * Рецепт ручного пресса из data/&lt;ns&gt;/pressing/*.json: что положить, какой штамп, сколько ударов, что выйдет.
 */
public record PressingRecipe(ResourceLocation input, ManualPressBlock.Die die, ResourceLocation result, int count, int presses) {
    public static final Codec<PressingRecipe> CODEC = RecordCodecBuilder.create(i -> i.group(
            ResourceLocation.CODEC.fieldOf("input").forGetter(PressingRecipe::input),
            ManualPressBlock.Die.CODEC.fieldOf("die").forGetter(PressingRecipe::die),
            ResourceLocation.CODEC.fieldOf("result").forGetter(PressingRecipe::result),
            Codec.INT.optionalFieldOf("count", 1).forGetter(PressingRecipe::count),
            Codec.INT.optionalFieldOf("presses", 3).forGetter(PressingRecipe::presses)
    ).apply(i, PressingRecipe::new));

    public boolean matches(ItemStack stack, ManualPressBlock.Die currentDie) {
        return currentDie == die && stack.is(BuiltInRegistries.ITEM.get(input));
    }

    public ItemStack output() {
        Item item = BuiltInRegistries.ITEM.get(result);
        return new ItemStack(item, count);
    }
}
