package dev.warpbound.entity;

import dev.warpbound.Warpbound;
import dev.warpbound.entity.dreadnought.DreadnoughtEntity;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.SpawnEggItem;

public final class WarpboundEntities {
    // Габарит общей туши: о неё спотыкаются игроки и блоки; попадания ловят части
    public static final EntityType<DreadnoughtEntity> DREADNOUGHT = Registry.register(
            BuiltInRegistries.ENTITY_TYPE, Warpbound.id("dreadnought"),
            EntityType.Builder.of(DreadnoughtEntity::new, MobCategory.MISC)
                    .sized(3.0f, 4.1f)
                    .eyeHeight(3.35f)
                    .clientTrackingRange(10)
                    .build("dreadnought"));

    public static final Item DREADNOUGHT_SPAWN_EGG = Registry.register(
            BuiltInRegistries.ITEM, Warpbound.id("dreadnought_spawn_egg"),
            new SpawnEggItem(DREADNOUGHT, 0x1f3f8f, 0xc9a227, new Item.Properties()));

    private WarpboundEntities() {
    }

    public static void register() {
        FabricDefaultAttributeRegistry.register(DREADNOUGHT, DreadnoughtEntity.createAttributes());
        ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.SPAWN_EGGS)
                .register(entries -> entries.accept(DREADNOUGHT_SPAWN_EGG));
    }
}
