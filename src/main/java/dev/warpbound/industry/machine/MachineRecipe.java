package dev.warpbound.industry.machine;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.material.Fluid;

import java.util.List;

/** Рецепт машины цепочки из data/warpbound/machine_recipe. */
public record MachineRecipe(ResourceLocation machine, double seconds, List<ItemIn> itemsIn, List<ItemOut> itemsOut,
                            List<FluidAmount> fluidsIn, List<FluidAmount> fluidsOut) {
    private static final Codec<Item> ITEM = BuiltInRegistries.ITEM.byNameCodec();
    private static final Codec<Fluid> FLUID = BuiltInRegistries.FLUID.byNameCodec();

    public static final Codec<MachineRecipe> CODEC = RecordCodecBuilder.create(i -> i.group(
            ResourceLocation.CODEC.fieldOf("machine").forGetter(MachineRecipe::machine),
            Codec.DOUBLE.fieldOf("seconds").forGetter(MachineRecipe::seconds),
            ItemIn.CODEC.listOf().optionalFieldOf("items_in", List.of()).forGetter(MachineRecipe::itemsIn),
            ItemOut.CODEC.listOf().optionalFieldOf("items_out", List.of()).forGetter(MachineRecipe::itemsOut),
            FluidAmount.CODEC.listOf().optionalFieldOf("fluids_in", List.of()).forGetter(MachineRecipe::fluidsIn),
            FluidAmount.CODEC.listOf().optionalFieldOf("fluids_out", List.of()).forGetter(MachineRecipe::fluidsOut)
    ).apply(i, MachineRecipe::new));

    public int ticks() {
        return Math.max(1, (int) Math.round(seconds * 20));
    }

    public record ItemIn(Item item, int count) {
        static final Codec<ItemIn> CODEC = RecordCodecBuilder.create(i -> i.group(
                ITEM.fieldOf("item").forGetter(ItemIn::item),
                Codec.INT.fieldOf("count").forGetter(ItemIn::count)
        ).apply(i, ItemIn::new));
    }

    public record ItemOut(Item item, int count, double chance) {
        static final Codec<ItemOut> CODEC = RecordCodecBuilder.create(i -> i.group(
                ITEM.fieldOf("item").forGetter(ItemOut::item),
                Codec.INT.fieldOf("count").forGetter(ItemOut::count),
                Codec.DOUBLE.optionalFieldOf("chance", 1.0).forGetter(ItemOut::chance)
        ).apply(i, ItemOut::new));
    }

    public record FluidAmount(Fluid fluid, int mb) {
        static final Codec<FluidAmount> CODEC = RecordCodecBuilder.create(i -> i.group(
                FLUID.fieldOf("fluid").forGetter(FluidAmount::fluid),
                Codec.INT.fieldOf("mb").forGetter(FluidAmount::mb)
        ).apply(i, FluidAmount::new));
    }
}
