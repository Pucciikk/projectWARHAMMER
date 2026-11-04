package dev.warpbound.gun;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import dev.warpbound.Warpbound;
import dev.warpbound.core.DataRegistry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.Item;

/**
 * Балансные числа оружия из data/warpbound/gun/&lt;предмет&gt;.json.
 * speed — наибольшая скорость, блоков за тик; speed_start и accel — разгон (болт вылетает медленнее и разгоняется своим двигателем); spread — градусы от оси; blast — разрыв снаряда (0 у лазгана); head — множитель попадания в голову.
 */
public record GunSpec(float damage, float blastDamage, float blastRadius, float speed, int lifeTicks, float spreadHip, float spreadAim, float head, float knockback, float speedStart, float accel) {
    public static final Codec<GunSpec> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.FLOAT.fieldOf("damage").forGetter(GunSpec::damage),
            Codec.FLOAT.optionalFieldOf("blast_damage", 0f).forGetter(GunSpec::blastDamage),
            Codec.FLOAT.optionalFieldOf("blast_radius", 0f).forGetter(GunSpec::blastRadius),
            Codec.FLOAT.fieldOf("speed").forGetter(GunSpec::speed),
            Codec.INT.fieldOf("life_ticks").forGetter(GunSpec::lifeTicks),
            Codec.FLOAT.fieldOf("spread_hip").forGetter(GunSpec::spreadHip),
            Codec.FLOAT.fieldOf("spread_aim").forGetter(GunSpec::spreadAim),
            Codec.FLOAT.optionalFieldOf("head", 1.5f).forGetter(GunSpec::head),
            Codec.FLOAT.optionalFieldOf("knockback", 0.1f).forGetter(GunSpec::knockback),
            Codec.FLOAT.optionalFieldOf("speed_start", 0f).forGetter(GunSpec::speedStart),
            Codec.FLOAT.optionalFieldOf("accel", 1f).forGetter(GunSpec::accel)
    ).apply(i, GunSpec::new));

    /** Запасные числа: оружие не должно ломаться, если запись в датапаке битая. */
    public static final GunSpec FALLBACK = new GunSpec(6, 0, 0, 6, 30, 2, 0.3f, 1.5f, 0.1f, 0, 1);
    public static final DataRegistry<GunSpec> REGISTRY = new DataRegistry<>("gun", CODEC);

    /** С какой скоростью снаряд выходит из ствола. */
    public float muzzleSpeed() {
        return speedStart > 0 ? speedStart : speed;
    }

    public static GunSpec of(Item item) {
        return REGISTRY.get(BuiltInRegistries.ITEM.getKey(item)).orElseGet(() -> {
            Warpbound.LOG.warn("нет data/gun для {}", BuiltInRegistries.ITEM.getKey(item));
            return FALLBACK;
        });
    }
}
