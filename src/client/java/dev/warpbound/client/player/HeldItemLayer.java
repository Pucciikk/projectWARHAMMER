package dev.warpbound.client.player;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.item.Items;
import dev.warpbound.client.gun.GunRenderer;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import software.bernie.geckolib.cache.object.GeoBone;
import software.bernie.geckolib.renderer.layer.GeoRenderLayer;
import software.bernie.geckolib.util.RenderUtil;

/**
 * Предметы в кулаках Астартес. Точка — низ и перед кулака (как у ванильной руки: низ и перед кисти), дальше ровно ванильные
 * повороты слоя ItemInHandLayer, поэтому любой предмет (меч, кирка, лук, щит, оружие мода) встаёт так же, как в руке обычного игрока.
 * Оси ванильной модели — оси GeckoLib, отражённые по X и Y.
 */
public final class HeldItemLayer extends GeoRenderLayer<PlayerFormAnimatable> {
    /** От запястья до низа кулака и вперёд до его передней грани, блоков (кулак Астартес крупнее, предмет тоже чуть крупнее). */
    static float DOWN = 0.15f, FORWARD = 0.06f, SIZE = 1.15f;
    /** Центр шлема над точкой вращения головы и его размер относительно головы игрока. */
    static float HEAD_CENTER = 0.17f, HEAD_SIZE = 0.9f;

    private final PlayerFormRenderer owner;

    public HeldItemLayer(PlayerFormRenderer renderer) {
        super(renderer);
        this.owner = renderer;
    }

    @Override
    public void renderForBone(PoseStack poseStack, PlayerFormAnimatable animatable, GeoBone bone, RenderType renderType, MultiBufferSource bufferSource,
                              VertexConsumer buffer, float partialTick, int packedLight, int packedOverlay) {
        AbstractClientPlayer p = owner.getCurrentEntity();
        if (p == null || p.isSpectator()) return;
        if (bone.getName().equals("head")) {
            spyglass(poseStack, bone, p, bufferSource, packedLight);
            return;
        }
        boolean right = bone.getName().equals("hand_r");
        if (!right && !bone.getName().equals("hand_l")) return;
        HumanoidArm arm = right ? HumanoidArm.RIGHT : HumanoidArm.LEFT;
        ItemStack stack = p.getMainArm() == arm ? p.getMainHandItem() : p.getOffhandItem();
        if (stack.isEmpty() || lookingThrough(p, stack)) return;
        boolean left = !right;
        poseStack.pushPose();
        RenderUtil.translateAndRotateMatrixForBone(poseStack, bone);
        // ванильные предметы рассчитаны на прямую руку: снимаем изгиб локтя и кисти — предмет в кулаке, но смотрит по плечу
        GeoBone fore = bone.getParent();
        float bend = bone.getRotX() + (fore != null ? fore.getRotX() : 0);
        poseStack.translate(0, -DOWN * 0.5f, 0);
        poseStack.mulPose(Axis.XP.rotation(-bend));
        poseStack.translate(0, -DOWN * 0.5f, -FORWARD);
        poseStack.scale(-SIZE, -SIZE, SIZE);                       // в оси ванильной модели: Y вниз вдоль руки
        poseStack.mulPose(Axis.XP.rotationDegrees(-90f));
        poseStack.mulPose(Axis.YP.rotationDegrees(180f));
        poseStack.translate((left ? -1 : 1) / 16f, 0, 0);
        GunRenderer.setHolder(p);                                    // дуло оружия мода привязано к стрелку (вспышка, снаряд)
        try {
            Minecraft.getInstance().getEntityRenderDispatcher().getItemInHandRenderer().renderItem(p, stack,
                    left ? ItemDisplayContext.THIRD_PERSON_LEFT_HAND : ItemDisplayContext.THIRD_PERSON_RIGHT_HAND, left, poseStack, bufferSource, packedLight);
        } finally {
            GunRenderer.setHolder(null);
        }
        poseStack.popPose();
    }

    /** Подзорная труба в деле: как у ванильного игрока, у глаза, а не в руке. */
    private static boolean lookingThrough(AbstractClientPlayer p, ItemStack stack) {
        return stack.is(Items.SPYGLASS) && p.getUseItem() == stack && p.swingTime == 0;
    }

    /** Ванильный PlayerItemInHandLayer.renderArmWithSpyglass, перенесённый на шлем Астартес (он крупнее головы игрока). */
    private void spyglass(PoseStack poseStack, GeoBone head, AbstractClientPlayer p, MultiBufferSource buffers, int light) {
        ItemStack stack = p.getUseItem();
        if (!lookingThrough(p, stack)) return;
        boolean left = (p.getUsedItemHand() == InteractionHand.MAIN_HAND ? p.getMainArm() : p.getMainArm().getOpposite()) == HumanoidArm.LEFT;
        poseStack.pushPose();
        RenderUtil.translateAndRotateMatrixForBone(poseStack, head);
        poseStack.translate(0, HEAD_CENTER, 0);
        poseStack.scale(-1, -1, 1);                                  // в оси ванильной модели
        poseStack.mulPose(Axis.YP.rotationDegrees(180f));
        poseStack.scale(0.625f * HEAD_SIZE, -0.625f * HEAD_SIZE, -0.625f * HEAD_SIZE);
        poseStack.translate((left ? -2.5f : 2.5f) / 16f, -0.0625f, 0);
        Minecraft.getInstance().getEntityRenderDispatcher().getItemInHandRenderer().renderItem(p, stack, ItemDisplayContext.HEAD, false, poseStack, buffers, light);
        poseStack.popPose();
    }
}
