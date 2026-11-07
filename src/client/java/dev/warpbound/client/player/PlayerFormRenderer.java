package dev.warpbound.client.player;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.warpbound.client.gun.GunRenderer;
import dev.warpbound.player.GeneForm;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.cache.object.BakedGeoModel;
import software.bernie.geckolib.cache.object.GeoBone;
import software.bernie.geckolib.cache.object.GeoCube;
import software.bernie.geckolib.renderer.GeoReplacedEntityRenderer;
import software.bernie.geckolib.renderer.layer.GeoRenderLayer;

/**
 * Игрок в модели формы тела вместо ванильного. Модель ростом с форму (2,2 у Астартес), а игрок уже увеличен атрибутом scale,
 * поэтому модель ужата на 1,8 / рост: вместе с scale получается ровно хитбокс. Меш рисуется напрямую, как у NPC;
 * слой свечения перерисовывает только голову (линзы).
 */
public final class PlayerFormRenderer extends GeoReplacedEntityRenderer<AbstractClientPlayer, PlayerFormAnimatable> {
    private boolean skipCubes;

    public PlayerFormRenderer(EntityRendererProvider.Context context, GeneForm form) {
        super(context, new PlayerFormModel(form.model()), new PlayerFormAnimatable(form));
        withScale(1.8f / form.modelHeight());               // вместе со scale игрока выходит рост формы
        this.shadowRadius = 0.5f;
        addRenderLayer(new Glow(this));
        addRenderLayer(new HeldItemLayer(this));
    }

    @Override
    public void render(AbstractClientPlayer player, float entityYaw, float partialTick, PoseStack poseStack, MultiBufferSource bufferSource, int packedLight) {
        super.render(player, entityYaw, partialTick, poseStack, bufferSource, packedLight);
        if (shouldShowName(player)) renderNameTag(player, player.getDisplayName(), poseStack, bufferSource, packedLight, partialTick);
    }

    /** Рука от первого лица: смещение и размер относительно ванильной руки (их точка вращения — плечо). Подбирались по снимкам. */
    static float FP_SCALE = 0.95f, FP_X = 0f, FP_Y = 0.13f, FP_Z = 0f;
    private boolean firstPerson;

    /**
     * Латная перчатка вместо ванильной руки от первого лица. Ставим плечо руки Астартес туда, где у ванильной модели плечо,
     * в осях ванильной модели (оси GeckoLib, отражённые по X и Y), — ванильный ItemInHandRenderer уже развернул позу к камере
     * и сам добавляет взмах и покачивание. Кости руки на этот кадр в покое: висящая прямая рука, как у ванильной.
     */
    public void renderFirstPersonArm(PoseStack poseStack, MultiBufferSource buffers, int light, AbstractClientPlayer player, boolean right) {
        BakedGeoModel model = getGeoModel().getBakedModel(getGeoModel().getModelResource(animatable));
        GeoBone arm = model.getBone(right ? "arm_r" : "arm_l").orElse(null);
        if (arm == null) return;
        rest(arm);
        ResourceLocation tex = getTextureLocation(animatable);
        RenderType type = RenderType.entityCutoutNoCull(tex);
        poseStack.pushPose();
        poseStack.translate((right ? -5 : 5) / 16f + (right ? -FP_X : FP_X), 2 / 16f + FP_Y, FP_Z);
        poseStack.scale(-FP_SCALE, -FP_SCALE, FP_SCALE);
        poseStack.translate(-arm.getPivotX() / 16f, -arm.getPivotY() / 16f, -arm.getPivotZ() / 16f);
        firstPerson = true;
        try {
            renderRecursively(poseStack, animatable, arm, type, buffers, buffers.getBuffer(type), true, 0, light, OverlayTexture.NO_OVERLAY, 0xFFFFFFFF);
        } finally {
            firstPerson = false;
        }
        poseStack.popPose();
    }

    private static void rest(GeoBone bone) {
        bone.setRotX(0);
        bone.setRotY(0);
        bone.setRotZ(0);
        bone.setPosX(0);
        bone.setPosY(0);
        bone.setPosZ(0);
        for (GeoBone child : bone.getChildBones()) rest(child);
    }

    @Override
    public void renderRecursively(PoseStack poseStack, PlayerFormAnimatable animatable, GeoBone bone, RenderType renderType, MultiBufferSource bufferSource, VertexConsumer buffer,
                                  boolean isReRender, float partialTick, int packedLight, int packedOverlay, int colour) {
        boolean head = bone.getName().equals("head");
        boolean visor = bone.getName().equals("visor");
        skipCubes = firstPerson ? visor : isReRender ? !head && !visor : visor;
        super.renderRecursively(poseStack, animatable, bone, renderType, bufferSource, buffer, isReRender, partialTick, packedLight, packedOverlay, colour);
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

    /** Падение играет клип смерти: ванильный поворот набок здесь лишний. Тот же угол GeckoLib берёт для сна: спящий ложится на 90°. */
    @Override
    protected float getDeathMaxRotation(PlayerFormAnimatable animatable) {
        AbstractClientPlayer p = getCurrentEntity();
        return p != null && p.isSleeping() ? 90 : 0;
    }

    /**
     * Как у ванильного игрока (PlayerRenderer.setupRotations): на элитрах тело ложится по взгляду и разворачивается по ходу,
     * в воде и ползком — горизонтально. Сдвиг вдоль тела у ванили (0, −1, 0,3) в его масштабе; у нас единица здесь крупнее в 1 / withScale раз.
     */
    @Override
    protected void applyRotations(PlayerFormAnimatable animatable, PoseStack poseStack, float ageInTicks, float rotationYaw, float partialTick, float nativeScale) {
        super.applyRotations(animatable, poseStack, ageInTicks, rotationYaw, partialTick, nativeScale);
        AbstractClientPlayer p = getCurrentEntity();
        if (p == null || p.isSleeping()) return;
        float pitch = p.getViewXRot(partialTick);
        if (p.isFallFlying()) {
            float ticks = p.getFallFlyingTicks() + partialTick;
            float k = net.minecraft.util.Mth.clamp(ticks * ticks / 100f, 0, 1);
            if (!p.isAutoSpinAttack()) poseStack.mulPose(com.mojang.math.Axis.XP.rotationDegrees(k * (-90f - pitch)));
            net.minecraft.world.phys.Vec3 view = p.getViewVector(partialTick), vel = p.getDeltaMovementLerped(partialTick);
            double dv = vel.horizontalDistanceSqr(), dl = view.horizontalDistanceSqr();
            if (dv > 0 && dl > 0) {
                double cos = (vel.x * view.x + vel.z * view.z) / Math.sqrt(dv * dl);
                double cross = vel.x * view.z - vel.z * view.x;
                poseStack.mulPose(com.mojang.math.Axis.YP.rotation((float) (Math.signum(cross) * Math.acos(net.minecraft.util.Mth.clamp(cos, -1, 1)))));
            }
            return;
        }
        float swim = p.getSwimAmount(partialTick);
        if (swim > 0) {
            float target = p.isInWater() ? -90f - pitch : -90f;
            poseStack.mulPose(com.mojang.math.Axis.XP.rotationDegrees(net.minecraft.util.Mth.lerp(swim, 0, target)));
            if (p.isVisuallySwimming()) {
                float k = 1 / scaleHeight;
                poseStack.translate(0, -1 * k, 0.3f * k);
            }
        }
    }

    @Override
    public int getPackedOverlay(PlayerFormAnimatable animatable, float u, float partialTick) {
        AbstractClientPlayer p = getCurrentEntity();
        return OverlayTexture.pack(OverlayTexture.u(u), OverlayTexture.v(p != null && p.isAlive() && p.hurtTime > 0));
    }

    /** Свечение линз: &lt;текстура&gt;_glow.png полной яркостью. */
    private static final class Glow extends GeoRenderLayer<PlayerFormAnimatable> {
        private final PlayerFormRenderer owner;

        Glow(PlayerFormRenderer renderer) {
            super(renderer);
            this.owner = renderer;
        }

        @Override
        public void render(PoseStack poseStack, PlayerFormAnimatable animatable, BakedGeoModel model, @Nullable RenderType renderType, MultiBufferSource bufferSource,
                           @Nullable VertexConsumer buffer, float partialTick, int packedLight, int packedOverlay) {
            AbstractClientPlayer p = owner.getCurrentEntity();
            if (p == null || p.isInvisible()) return;
            ResourceLocation tex = getRenderer().getTextureLocation(animatable);
            RenderType eyes = RenderType.eyes(tex.withPath(path -> path.replace(".png", "_glow.png")));
            getRenderer().reRender(model, poseStack, bufferSource, animatable, eyes, bufferSource.getBuffer(eyes), partialTick, LightTexture.FULL_BRIGHT, packedOverlay, 0xFFFFFFFF);
        }
    }
}
