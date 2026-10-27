package dev.warpbound.client.ship;

import dev.warpbound.Warpbound;
import dev.warpbound.client.multiblock.MachineRenderer;
import dev.warpbound.ship.block.WarpSamplerBlockEntity;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.model.DefaultedBlockGeoModel;
import software.bernie.geckolib.renderer.GeoBlockRenderer;

/** Варп-пробоотборник: модель warp_sampler со свечением порта, колб и рун. */
public class WarpSamplerRenderer extends GeoBlockRenderer<WarpSamplerBlockEntity> {
    public WarpSamplerRenderer() {
        super(new DefaultedBlockGeoModel<>(Warpbound.id("warp_sampler")));
        addRenderLayer(new MachineRenderer.Glow<>(this));
    }

    @Override
    public boolean shouldRenderOffScreen(WarpSamplerBlockEntity sampler) {
        return true;
    }

    @Override
    public boolean shouldRender(WarpSamplerBlockEntity sampler, Vec3 camera) {
        return Vec3.atCenterOf(sampler.getBlockPos()).closerThan(camera, 64);
    }
}
