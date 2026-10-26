package dev.warpbound.client.entity.geo;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.animatable.GeoAnimatable;
import software.bernie.geckolib.cache.object.BakedGeoModel;
import software.bernie.geckolib.renderer.GeoRenderer;
import software.bernie.geckolib.renderer.layer.GeoRenderLayer;

import java.util.HashMap;
import java.util.Map;

/**
 * Свечение поверх модели: &lt;текстура&gt;_glow.png, полной яркостью и в темноте (линзы, глаза, варп-пламя).
 * Имя _glow, а не _glowmask GeckoLib, — как у дредноута и в контракте моделей.
 */
public class GlowLayer<T extends Entity & GeoAnimatable> extends GeoRenderLayer<T> {
    private final Map<ResourceLocation, ResourceLocation> glowTextures = new HashMap<>();

    public GlowLayer(GeoRenderer<T> renderer) {
        super(renderer);
    }

    @Override
    public void render(PoseStack poseStack, T entity, BakedGeoModel model, @Nullable RenderType renderType,
                       MultiBufferSource bufferSource, @Nullable VertexConsumer buffer, float partialTick,
                       int packedLight, int packedOverlay) {
        if (entity.isInvisible()) return;
        ResourceLocation glow = glowTextures.computeIfAbsent(getRenderer().getTextureLocation(entity),
                tex -> tex.withPath(p -> p.replace(".png", "_glow.png")));
        RenderType eyes = RenderType.eyes(glow);
        getRenderer().reRender(model, poseStack, bufferSource, entity, eyes, bufferSource.getBuffer(eyes), partialTick,
                LightTexture.FULL_BRIGHT, packedOverlay, 0xFFFFFFFF);
    }
}
