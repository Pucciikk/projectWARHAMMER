package dev.warpbound.client.entity;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.warpbound.Warpbound;
import dev.warpbound.client.gun.GunRenderer;
import dev.warpbound.entity.dreadnought.concept.DreadConceptEntity;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.RenderType;
import software.bernie.geckolib.cache.object.GeoBone;
import software.bernie.geckolib.cache.object.GeoCube;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;

/** Дредноут: меш рисуем напрямую, как у машин и оружия. */
public final class DreadConceptRenderer extends GeoEntityRenderer<DreadConceptEntity> {
    public DreadConceptRenderer(EntityRendererProvider.Context context, String model, float shadow) {
        super(context, new DefaultedEntityGeoModel<>(Warpbound.id(model)));
        this.shadowRadius = shadow;
    }

    private final java.util.Map<DreadConceptEntity, DreadLoopSound> loops = new java.util.WeakHashMap<>();

    @Override
    public void render(DreadConceptEntity entity, float yaw, float partial, PoseStack pose, net.minecraft.client.renderer.MultiBufferSource buffers, int light) {
        if (entity.isAlive() && entity.isVehicle() && entity.fuel() > 0) {
            DreadLoopSound loop = loops.get(entity);
            if (loop == null || loop.isStopped()) {
                loop = new DreadLoopSound(entity);
                loops.put(entity, loop);
                net.minecraft.client.Minecraft.getInstance().getSoundManager().play(loop);
            }
        }
        super.render(entity, yaw, partial, pose, buffers, light);
    }

    /** Корпус идёт за взглядом пилота, пушка ещё и наклоняется. Поворот поверх клипа: кость получает его вместе со всеми детьми. */
    @Override
    public void renderRecursively(PoseStack poseStack, DreadConceptEntity entity, GeoBone bone, RenderType renderType, net.minecraft.client.renderer.MultiBufferSource bufferSource, VertexConsumer buffer,
                                  boolean isReRender, float partialTick, int packedLight, int packedOverlay, int colour) {
        String name = bone.getName();
        boolean torso = name.equals("torso"), gun = name.equals("arm_r");
        if ((torso || gun) && entity.isAlive() && entity.isVehicle()) {
            poseStack.pushPose();
            float px = bone.getPivotX() / 16f, py = bone.getPivotY() / 16f, pz = bone.getPivotZ() / 16f;
            poseStack.translate(px, py, pz);
            if (torso) poseStack.mulPose(com.mojang.math.Axis.YP.rotationDegrees(-entity.torsoRelative(partialTick)));
            else poseStack.mulPose(com.mojang.math.Axis.XP.rotationDegrees(entity.gunPitch(partialTick)));
            poseStack.translate(-px, -py, -pz);
            super.renderRecursively(poseStack, entity, bone, renderType, bufferSource, buffer, isReRender, partialTick, packedLight, packedOverlay, colour);
            poseStack.popPose();
            return;
        }
        super.renderRecursively(poseStack, entity, bone, renderType, bufferSource, buffer, isReRender, partialTick, packedLight, packedOverlay, colour);
    }

    /** Падение играет своя анимация: ванильный поворот набок здесь лишний. */
    @Override
    protected float getDeathMaxRotation(DreadConceptEntity animatable) {
        return 0;
    }

    /** Красная заливка при смерти убила бы весь вид падения, поэтому она только на живом. */
    @Override
    public int getPackedOverlay(DreadConceptEntity animatable, float u, float partialTick) {
        return OverlayTexture.pack(OverlayTexture.u(u), OverlayTexture.v(animatable.isAlive() && animatable.hurtTime > 0));
    }

    @Override
    public void renderCube(PoseStack poseStack, GeoCube cube, VertexConsumer buffer, int packedLight, int packedOverlay, int colour) {
        if (cube.size().x >= 0) {
            super.renderCube(poseStack, cube, buffer, packedLight, packedOverlay, colour);
            return;
        }
        GunRenderer.drawMesh(poseStack, cube, buffer, packedLight, packedOverlay, colour);
    }
}
