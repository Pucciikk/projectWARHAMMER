package dev.warpbound.client.multiblock;

import dev.warpbound.Warpbound;
import dev.warpbound.ship.block.ShipFixtureBlockEntity;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.model.GeoModel;
import software.bernie.geckolib.renderer.GeoBlockRenderer;

/** Крупное корабельное оборудование: модель по id блока (geo/block/&lt;id&gt;.geo.json) со свечением. */
public class FixtureRenderer extends GeoBlockRenderer<ShipFixtureBlockEntity> {
    public FixtureRenderer() {
        super(new GeoModel<>() {
            @Override
            public ResourceLocation getModelResource(ShipFixtureBlockEntity fixture) {
                return Warpbound.id("geo/block/" + fixture.modelName() + ".geo.json");
            }

            @Override
            public ResourceLocation getTextureResource(ShipFixtureBlockEntity fixture) {
                return Warpbound.id("textures/block/" + fixture.modelName() + ".png");
            }

            @Override
            public ResourceLocation getAnimationResource(ShipFixtureBlockEntity fixture) {
                return Warpbound.id("animations/block/" + fixture.modelName() + ".animation.json");
            }
        });
        addRenderLayer(new MachineRenderer.Glow<>(this));
    }

    @Override
    public boolean shouldRenderOffScreen(ShipFixtureBlockEntity fixture) {
        return true;
    }

    @Override
    public boolean shouldRender(ShipFixtureBlockEntity fixture, Vec3 camera) {
        return Vec3.atCenterOf(fixture.getBlockPos()).closerThan(camera, 96);
    }
}
