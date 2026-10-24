package dev.warpbound.shipyard;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import java.util.List;

/**
 * Класс корабля из data/&lt;ns&gt;/ship_class/*.json: этапы постройки на верфи.
 * Каждый этап — поставка ресурсов, время работы и шаблон-структура, которая появляется в доке.
 * Смещение шаблона задано, как и мультиблок, для ядра верфи, смотрящего на север.
 */
public record ShipClass(String name, List<Stage> stages) {
    public static final Codec<ShipClass> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.STRING.fieldOf("name").forGetter(ShipClass::name),
            Stage.CODEC.listOf().fieldOf("stages").forGetter(ShipClass::stages)
    ).apply(i, ShipClass::new));

    public record Stage(String name, List<Requirement> requirements, ResourceLocation structure, BlockPos offset,
                        int buildSeconds) {
        public static final Codec<Stage> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.STRING.fieldOf("name").forGetter(Stage::name),
                Requirement.CODEC.listOf().fieldOf("requirements").forGetter(Stage::requirements),
                ResourceLocation.CODEC.fieldOf("structure").forGetter(Stage::structure),
                BlockPos.CODEC.fieldOf("offset").forGetter(Stage::offset),
                Codec.INT.optionalFieldOf("build_seconds", 30).forGetter(Stage::buildSeconds)
        ).apply(i, Stage::new));
    }

    /** Поставка: предмет или #тег и количество. */
    public record Requirement(String item, int count) {
        public static final Codec<Requirement> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.STRING.fieldOf("item").forGetter(Requirement::item),
                Codec.INT.fieldOf("count").forGetter(Requirement::count)
        ).apply(i, Requirement::new));

        public boolean matches(ItemStack stack) {
            if (stack.isEmpty()) return false;
            if (item.startsWith("#")) {
                return stack.is(TagKey.create(Registries.ITEM, ResourceLocation.parse(item.substring(1))));
            }
            return stack.is(icon());
        }

        /** Предмет для иконки в экране верфи (для тега — первый попавшийся из него). */
        public Item icon() {
            if (item.startsWith("#")) {
                TagKey<Item> tag = TagKey.create(Registries.ITEM, ResourceLocation.parse(item.substring(1)));
                return BuiltInRegistries.ITEM.getTag(tag)
                        .flatMap(set -> set.stream().findFirst())
                        .map(holder -> holder.value())
                        .orElse(net.minecraft.world.item.Items.BARRIER);
            }
            return BuiltInRegistries.ITEM.get(ResourceLocation.parse(item));
        }
    }
}
