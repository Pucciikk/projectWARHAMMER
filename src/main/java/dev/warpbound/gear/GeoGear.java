package dev.warpbound.gear;

import net.minecraft.world.item.Item;
import software.bernie.geckolib.animatable.client.GeoRenderProvider;

import java.util.function.BiConsumer;
import java.util.function.Consumer;

/**
 * Мост к 3D-моделям снаряжения (GeckoLib): рендеры живут только на клиенте, поэтому клиент при старте
 * подставляет сюда выдачу рендера по предмету (client/gear/GearRenderers). На сервере — пусто.
 */
public final class GeoGear {
    public static BiConsumer<Item, Consumer<GeoRenderProvider>> RENDER = (item, consumer) -> {
    };

    private GeoGear() {
    }
}
