package dev.warpbound.quest;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/** Награда за квест: предмет и количество. */
public record Reward(Item item, int count) {
    public static final Codec<Reward> CODEC = RecordCodecBuilder.create(i -> i.group(
            BuiltInRegistries.ITEM.byNameCodec().fieldOf("item").forGetter(Reward::item),
            Codec.INT.optionalFieldOf("count", 1).forGetter(Reward::count)
    ).apply(i, Reward::new));

    public ItemStack stack() {
        return new ItemStack(item, count);
    }
}
