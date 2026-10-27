package dev.warpbound.gear;

import dev.warpbound.Warpbound;
import dev.warpbound.core.WarpboundItems;
import net.minecraft.Util;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.crafting.Ingredient;

import java.util.EnumMap;
import java.util.List;

/**
 * Материалы брони. Цифры защиты пока здесь (как у ванильных материалов); в JSON уйдут вместе с каркасом брони.
 * Текстуры на модели игрока — textures/models/armor/&lt;имя&gt;_layer_1.png и _layer_2.png (tools/textures/gen_s1_items.py).
 */
public final class WarpboundArmor {
    /** Флак-броня Гвардии: чуть крепче железной, легче чинится флак-пластинами. */
    public static final Holder<ArmorMaterial> FLAK = register("flak", 2, 6, 5, 2, 4, 0.5f, 0.0f, 10);
    /** Респиратор: почти не защищает, зато дышит за тебя на ядовитых мирах (Кинерис). */
    public static final Holder<ArmorMaterial> RESPIRATOR = register("respirator", 1, 1, 1, 1, 1, 0.0f, 0.0f, 8);

    private WarpboundArmor() {
    }

    public static void register() {
    }

    private static Holder<ArmorMaterial> register(String name, int boots, int chest, int legs, int helmet, int body,
                                                  float toughness, float knockback, int enchant) {
        EnumMap<ArmorItem.Type, Integer> defense = Util.make(new EnumMap<>(ArmorItem.Type.class), m -> {
            m.put(ArmorItem.Type.BOOTS, boots);
            m.put(ArmorItem.Type.LEGGINGS, legs);
            m.put(ArmorItem.Type.CHESTPLATE, chest);
            m.put(ArmorItem.Type.HELMET, helmet);
            m.put(ArmorItem.Type.BODY, body);
        });
        return Registry.registerForHolder(BuiltInRegistries.ARMOR_MATERIAL, Warpbound.id(name),
                new ArmorMaterial(defense, enchant, SoundEvents.ARMOR_EQUIP_IRON,
                        () -> Ingredient.of(name.equals("flak") ? WarpboundItems.FLAK_PLATE : WarpboundItems.RESPIRATOR_FILTER),
                        List.of(new ArmorMaterial.Layer(Warpbound.id(name))), toughness, knockback));
    }
}
