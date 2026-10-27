package dev.warpbound.client.gear;

import dev.warpbound.Warpbound;
import dev.warpbound.core.WarpboundItems;
import dev.warpbound.gear.GeoGear;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import software.bernie.geckolib.animatable.client.GeoRenderProvider;
import software.bernie.geckolib.model.DefaultedItemGeoModel;
import software.bernie.geckolib.renderer.GeoArmorRenderer;
import software.bernie.geckolib.renderer.GeoItemRenderer;

/**
 * 3D-модели снаряжения (GeckoLib): оружие в руках — geo/item/&lt;имя&gt;_3d, броня — geo/item/flak_armor и respirator_mask.
 * Модели собирает tools/models/gen_gear.py.
 */
public final class GearRenderers {
    private GearRenderers() {
    }

    @SuppressWarnings({"rawtypes", "unchecked"})
    public static void register() {
        GeoGear.RENDER = (item, consumer) -> {
            if (item == WarpboundItems.LASGUN || item == WarpboundItems.CHAINSWORD) {
                String name = item == WarpboundItems.LASGUN ? "lasgun_3d" : "chainsword_3d";
                consumer.accept(new GeoRenderProvider() {
                    private GeoItemRenderer renderer;

                    @Override
                    public BlockEntityWithoutLevelRenderer getGeoItemRenderer() {
                        if (renderer == null) renderer = new GeoItemRenderer(new DefaultedItemGeoModel(Warpbound.id(name)));
                        return renderer;
                    }
                });
            } else {
                String name = item == WarpboundItems.RESPIRATOR ? "respirator_mask" : "flak_armor";
                consumer.accept(new GeoRenderProvider() {
                    private GeoArmorRenderer renderer;

                    @Override
                    public <T extends LivingEntity> HumanoidModel<?> getGeoArmorRenderer(T entity, ItemStack stack, EquipmentSlot slot,
                                                                                        HumanoidModel<T> original) {
                        if (renderer == null) renderer = new GeoArmorRenderer(new DefaultedItemGeoModel(Warpbound.id(name)));
                        return renderer;
                    }
                });
            }
        };
    }
}
