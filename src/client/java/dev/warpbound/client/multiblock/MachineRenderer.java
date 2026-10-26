package dev.warpbound.client.multiblock;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.warpbound.Warpbound;
import dev.warpbound.multiblock.MultiblockHost;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.animatable.GeoAnimatable;
import software.bernie.geckolib.cache.object.BakedGeoModel;
import software.bernie.geckolib.model.DefaultedBlockGeoModel;
import software.bernie.geckolib.renderer.GeoBlockRenderer;
import software.bernie.geckolib.renderer.GeoRenderer;
import software.bernie.geckolib.renderer.layer.GeoRenderLayer;

/**
 * Собранная машина: ядро рисует цельную модель GeckoLib (geo/block/&lt;машина&gt;.geo.json,
 * textures/block/&lt;машина&gt;.png и светящаяся _glow.png). Несобранное ядро рисуется обычной моделью блока.
 * <p>
 * Машина больше одного блока, поэтому рисуется и тогда, когда само ядро за краем экрана.
 */
public class MachineRenderer<T extends BlockEntity & GeoAnimatable & MultiblockHost> extends GeoBlockRenderer<T> {
    public MachineRenderer(String model) {
        super(new DefaultedBlockGeoModel<>(Warpbound.id(model)));
        addRenderLayer(new Glow<>(this));
    }

    @Override
    public void render(T machine, float partialTick, PoseStack poseStack, MultiBufferSource bufferSource, int packedLight, int packedOverlay) {
        if (!machine.isFormed()) return;
        super.render(machine, partialTick, poseStack, bufferSource, packedLight, packedOverlay);
    }

    @Override
    public boolean shouldRenderOffScreen(T machine) {
        return true;
    }

    @Override
    public int getViewDistance() {
        return 128;
    }

    @Override
    public boolean shouldRender(T machine, Vec3 camera) {
        return Vec3.atCenterOf(machine.getBlockPos()).closerThan(camera, getViewDistance());
    }

    /** Свечение (_glow.png) полной яркостью поверх модели: огонь, лампы, экраны. */
    public static final class Glow<T extends BlockEntity & GeoAnimatable> extends GeoRenderLayer<T> {
        public Glow(GeoRenderer<T> renderer) {
            super(renderer);
        }

        @Override
        public void render(PoseStack poseStack, T animatable, BakedGeoModel model, @Nullable RenderType renderType,
                           MultiBufferSource bufferSource, @Nullable VertexConsumer buffer, float partialTick,
                           int packedLight, int packedOverlay) {
            ResourceLocation tex = getRenderer().getTextureLocation(animatable);
            ResourceLocation glow = tex.withPath(p -> p.replace(".png", "_glow.png"));
            RenderType eyes = RenderType.eyes(glow);
            getRenderer().reRender(model, poseStack, bufferSource, animatable, eyes, bufferSource.getBuffer(eyes), partialTick,
                    LightTexture.FULL_BRIGHT, packedOverlay, 0xFFFFFFFF);
        }
    }
}
