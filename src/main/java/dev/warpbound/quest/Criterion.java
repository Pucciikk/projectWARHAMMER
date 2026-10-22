package dev.warpbound.quest;

import com.mojang.serialization.Codec;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.Item;

import java.util.Optional;

/**
 * Условие квеста.
 * <ul>
 *   <li>{@code item}: в инвентаре не меньше {@code count} предметов;</li>
 *   <li>{@code crafted}: скрафчено за всю игру не меньше {@code count} (по статистике);</li>
 *   <li>{@code flag}: игра поставила флаг {@code flag} (починил маяк, пережил ночь и т.п.).</li>
 * </ul>
 * {@code label} — подпись в окне квестов, для флагов обязательна по смыслу.
 */
public record Criterion(String type, Optional<Item> item, int count, Optional<String> flag, Optional<String> label) {
    public static final String ITEM = "item";
    public static final String CRAFTED = "crafted";
    public static final String FLAG = "flag";

    public static final Codec<Criterion> CODEC = RecordCodecBuilder.<Criterion>create(i -> i.group(
            Codec.STRING.fieldOf("type").forGetter(Criterion::type),
            BuiltInRegistries.ITEM.byNameCodec().optionalFieldOf("item").forGetter(Criterion::item),
            Codec.INT.optionalFieldOf("count", 1).forGetter(Criterion::count),
            Codec.STRING.optionalFieldOf("flag").forGetter(Criterion::flag),
            Codec.STRING.optionalFieldOf("label").forGetter(Criterion::label)
    ).apply(i, Criterion::new)).validate(c -> switch (c.type) {
        case ITEM, CRAFTED -> c.item.isPresent()
                ? DataResult.success(c)
                : DataResult.error(() -> "условию " + c.type + " нужен item");
        case FLAG -> c.flag.isPresent()
                ? DataResult.success(c)
                : DataResult.error(() -> "условию flag нужен flag");
        default -> DataResult.error(() -> "неизвестный тип условия: " + c.type);
    });
}
