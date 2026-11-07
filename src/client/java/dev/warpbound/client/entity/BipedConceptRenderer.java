package dev.warpbound.client.entity;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.warpbound.client.entity.geo.GlowLayer;
import dev.warpbound.client.gun.GunRenderer;
import dev.warpbound.entity.astartes.BipedConceptEntity;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import software.bernie.geckolib.cache.object.GeoBone;
import software.bernie.geckolib.cache.object.GeoCube;
import software.bernie.geckolib.renderer.GeoEntityRenderer;

/**
 * Астартес и Громовой воин: меш рисуем напрямую, как у дредноута. Взгляд, удар и вздрагивание поверх клипа накладывает BipedConceptModel.
 * Слой свечения перерисовывает только голову и стёкла очков: иначе каждая грань фигуры рисовалась бы дважды ради линз.
 * Кость visor — красное стекло: только в этом проходе, он складывает цвет с тем, что за ним, поэтому лицо видно сквозь очки.
 */
public final class BipedConceptRenderer extends GeoEntityRenderer<BipedConceptEntity> {
    private boolean skipCubes;

    public BipedConceptRenderer(EntityRendererProvider.Context context, String model, boolean glow, float scale) {
        super(context, new BipedConceptModel(model));
        withScale(scale);                                   // модель в своих единицах, в игре — рост варианта
        this.shadowRadius = 0.7f;
        if (glow) addRenderLayer(new GlowLayer<>(this));
    }

    @Override
    public void renderRecursively(PoseStack poseStack, BipedConceptEntity entity, GeoBone bone, RenderType renderType, MultiBufferSource bufferSource, VertexConsumer buffer,
                                  boolean isReRender, float partialTick, int packedLight, int packedOverlay, int colour) {
        boolean head = bone.getName().equals("head");
        boolean visor = bone.getName().equals("visor");
        skipCubes = isReRender ? !head && !visor : visor;
        super.renderRecursively(poseStack, entity, bone, renderType, bufferSource, buffer, isReRender, partialTick, packedLight, packedOverlay, colour);
    }

    /** Падение играет своя анимация: ванильный поворот набок здесь лишний. */
    @Override
    protected float getDeathMaxRotation(BipedConceptEntity animatable) {
        return 0;
    }

    /** Красная заливка при смерти убила бы весь вид падения, поэтому она только на живом. */
    @Override
    public int getPackedOverlay(BipedConceptEntity animatable, float u, float partialTick) {
        return OverlayTexture.pack(OverlayTexture.u(u), OverlayTexture.v(animatable.isAlive() && animatable.hurtTime > 0));
    }

    @Override
    public void renderCube(PoseStack poseStack, GeoCube cube, VertexConsumer buffer, int packedLight, int packedOverlay, int colour) {
        if (skipCubes) return;
        if (cube.size().x >= 0) {
            super.renderCube(poseStack, cube, buffer, packedLight, packedOverlay, colour);
            return;
        }
        GunRenderer.drawMesh(poseStack, cube, buffer, packedLight, packedOverlay, colour);
    }
}
