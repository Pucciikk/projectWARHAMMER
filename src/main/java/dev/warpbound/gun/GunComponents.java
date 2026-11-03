package dev.warpbound.gun;

import com.mojang.serialization.Codec;
import dev.warpbound.Warpbound;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.codec.ByteBufCodecs;

/** Компоненты предметов оружия. Регистрируются при первом обращении: предметы создаются раньше, чем Warpbound вызывает register(). */
public final class GunComponents {
    public static final DataComponentType<Integer> AMMO = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE, Warpbound.id("gun_ammo"),
            DataComponentType.<Integer>builder().persistent(Codec.INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());

    private GunComponents() {
    }
}
