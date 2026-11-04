package dev.warpbound.client.gun;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.warpbound.Warpbound;
import dev.warpbound.gear.ChainswordItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import software.bernie.geckolib.animation.AnimationState;
import software.bernie.geckolib.cache.object.GeoBone;
import software.bernie.geckolib.cache.object.GeoCube;
import software.bernie.geckolib.model.DefaultedItemGeoModel;
import software.bernie.geckolib.renderer.GeoItemRenderer;

/** Цепной меч: меш из Blender, цепь бежит всегда (зубья — отдельные кости), остальные кости двигает клип удара только в виде от первого лица. */
public final class ChainswordRenderer extends GeoItemRenderer<ChainswordItem> {
    static final String MODEL = "chainsword_3d";
    private static ChainswordRenderer instance;

    private ChainswordRenderer() {
        super(new Model());
        addRenderLayer(new GunRenderer.Glow<>(this));
    }

    public static ChainswordRenderer get() {
        if (instance == null) instance = new ChainswordRenderer();
        return instance;
    }

    private static final class Model extends DefaultedItemGeoModel<ChainswordItem> {
        private final float[] out = new float[6];
        private final float[] seconds = new float[1];

        Model() {
            super(Warpbound.id(MODEL));
        }

        @Override
        public void setCustomAnimations(ChainswordItem animatable, long instanceId, AnimationState<ChainswordItem> state) {
            GunClips.Clip chain = GunClips.get(MODEL, "chain");
            float t = ChainswordClient.chainPhase() * chain.length();
            for (String bone : chain.tracks().keySet()) {
                if (chain.sample(bone, t, out)) getBone(bone).ifPresent(b -> GunRenderer.applyPose(b, out));
            }
            GunClips.Clip clip = GunRenderer.viewPass ? ChainswordClient.activeClip(Minecraft.getInstance(), seconds) : GunClips.get(MODEL, "idle");
            if (!GunRenderer.viewPass) seconds[0] = 0;
            for (String bone : clip.tracks().keySet()) {
                if (bone.equals("_view") || !clip.sample(bone, seconds[0], out)) continue;
                getBone(bone).ifPresent(b -> GunRenderer.applyPose(b, out));
            }
        }
    }

    @Override
    public void renderRecursively(PoseStack poseStack, ChainswordItem animatable, GeoBone bone, RenderType renderType, MultiBufferSource bufferSource, VertexConsumer buffer,
                                  boolean isReRender, float partialTick, int packedLight, int packedOverlay, int colour) {
        if (GunRenderer.viewPass && !isReRender && GunRenderer.isLocator(bone.getName())) GunRenderer.capture(poseStack, bone);
        super.renderRecursively(poseStack, animatable, bone, renderType, bufferSource, buffer, isReRender, partialTick, packedLight, packedOverlay, colour);
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
