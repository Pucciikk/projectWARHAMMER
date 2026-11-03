package dev.warpbound.client.gun;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.warpbound.Warpbound;
import dev.warpbound.client.multiblock.MeshModelFactory;
import dev.warpbound.gun.GunItem;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.resources.ResourceLocation;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import org.joml.Vector3f;
import software.bernie.geckolib.animation.AnimationState;
import software.bernie.geckolib.cache.object.BakedGeoModel;
import software.bernie.geckolib.cache.object.GeoBone;
import software.bernie.geckolib.cache.object.GeoCube;
import software.bernie.geckolib.cache.object.GeoQuad;
import software.bernie.geckolib.cache.object.GeoVertex;
import software.bernie.geckolib.model.DefaultedItemGeoModel;
import software.bernie.geckolib.renderer.GeoItemRenderer;
import software.bernie.geckolib.renderer.GeoRenderer;
import software.bernie.geckolib.renderer.layer.GeoRenderLayer;
import software.bernie.geckolib.util.RenderUtil;

import java.util.HashMap;
import java.util.Map;

/**
 * Модель оружия на GeckoLib: меш из Blender, свечение и кости. Позу кости задаёт GunView через клипы,
 * а вне первого лица (в инвентаре, в руке у других игроков) оружие просто в покое.
 */
public final class GunRenderer extends GeoItemRenderer<GunItem> {
    /** Куда в кадре попали руки, дуло и окно выброса: заполняется при отрисовке костей. */
    static final Map<String, Matrix4f> CAPTURED = new HashMap<>();
    static final Map<String, Matrix3f> CAPTURED_NORMAL = new HashMap<>();
    private static final Map<String, GunRenderer> ALL = new HashMap<>();
    /** Включается только на время вида от первого лица. */
    static boolean viewPass;
    private boolean glowPass;

    private GunRenderer(String model) {
        super(new Model(model));
        addRenderLayer(new Glow(this));
    }

    public static GunRenderer of(String model) {
        return ALL.computeIfAbsent(model, GunRenderer::new);
    }

    /** Кости получают позу текущего клипа. Контроллеров GeckoLib нет: движением управляем сами. */
    private static final class Model extends DefaultedItemGeoModel<GunItem> {
        private final float[] out = new float[6];
        private final float[] seconds = new float[1];
        private final String name;

        Model(String name) {
            super(Warpbound.id(name));
            this.name = name;
        }

        @Override
        public void setCustomAnimations(GunItem animatable, long instanceId, AnimationState<GunItem> state) {
            GunClips.Clip clip = viewPass && GunClient.held() != null
                    ? GunClient.activeClip(GunVisual.of(GunClient.held()), net.minecraft.client.Minecraft.getInstance(), seconds)
                    : GunClips.get(name, "idle");
            if (!viewPass) seconds[0] = 0;
            for (String bone : clip.tracks().keySet()) {
                if (bone.equals("_view") || !clip.sample(bone, seconds[0], out)) continue;
                getBone(bone).ifPresent(b -> {
                    // оси Blender -> GeckoLib: те же, что в экспорте (x, z, y) и в kit.auto_tracks
                    b.setPosX(out[0] * 16);
                    b.setPosY(out[2] * 16);
                    b.setPosZ(out[1] * 16);
                    b.setRotX((float) Math.toRadians(-out[3]));
                    b.setRotY((float) Math.toRadians(out[5]));
                    b.setRotZ((float) Math.toRadians(out[4]));
                });
            }
        }
    }

    private static final class Glow extends GeoRenderLayer<GunItem> {
        Glow(GeoRenderer<GunItem> renderer) {
            super(renderer);
        }

        @Override
        public void render(PoseStack poseStack, GunItem animatable, BakedGeoModel model, RenderType renderType, MultiBufferSource bufferSource,
                           VertexConsumer buffer, float partialTick, int packedLight, int packedOverlay) {
            ResourceLocation tex = getRenderer().getTextureLocation(animatable);
            RenderType eyes = RenderType.eyes(tex.withPath(p -> p.replace(".png", "_glow.png")));
            GunRenderer owner = (GunRenderer) getRenderer();
            owner.glowPass = true;
            getRenderer().reRender(model, poseStack, bufferSource, animatable, eyes, bufferSource.getBuffer(eyes), partialTick,
                    LightTexture.FULL_BRIGHT, packedOverlay, 0xFFFFFFFF);
            owner.glowPass = false;
        }
    }

    @Override
    public void renderRecursively(PoseStack poseStack, GunItem animatable, GeoBone bone, RenderType renderType, MultiBufferSource bufferSource, VertexConsumer buffer,
                                  boolean isReRender, float partialTick, int packedLight, int packedOverlay, int colour) {
        if (viewPass && !isReRender && isLocator(bone.getName())) {
            poseStack.pushPose();
            RenderUtil.prepMatrixForBone(poseStack, bone);
            // начало координат в точке вращения: руки и вспышка строятся от неё
            poseStack.translate(bone.getPivotX() / 16f, bone.getPivotY() / 16f, bone.getPivotZ() / 16f);
            CAPTURED.put(bone.getName(), new Matrix4f(poseStack.last().pose()));
            CAPTURED_NORMAL.put(bone.getName(), new Matrix3f(poseStack.last().normal()));
            poseStack.popPose();
        }
        super.renderRecursively(poseStack, animatable, bone, renderType, bufferSource, buffer, isReRender, partialTick, packedLight, packedOverlay, colour);
    }

    private static boolean isLocator(String name) {
        return name.equals("arm_r") || name.equals("arm_l") || name.equals("muzzle") || name.equals("eject");
    }

    /** Меш рисуем напрямую, как у машин: GeckoLib считает кубы иначе и переворачивает плоские грани. */
    @Override
    public void renderCube(PoseStack poseStack, GeoCube cube, VertexConsumer buffer, int packedLight, int packedOverlay, int colour) {
        double mark = cube.size().x;
        if (mark >= 0) {
            super.renderCube(poseStack, cube, buffer, packedLight, packedOverlay, colour);
            return;
        }
        if (glowPass && mark == MeshModelFactory.MESH_PLAIN) return;
        Matrix4f m = poseStack.last().pose();
        Matrix3f n = poseStack.last().normal();
        for (GeoQuad quad : cube.quads()) {
            Vector3f q = quad.normal();
            float nx = n.m00() * q.x + n.m10() * q.y + n.m20() * q.z;
            float ny = n.m01() * q.x + n.m11() * q.y + n.m21() * q.z;
            float nz = n.m02() * q.x + n.m12() * q.y + n.m22() * q.z;
            for (GeoVertex v : quad.vertices()) {
                Vector3f p = v.position();
                buffer.addVertex(m.m00() * p.x + m.m10() * p.y + m.m20() * p.z + m.m30(),
                        m.m01() * p.x + m.m11() * p.y + m.m21() * p.z + m.m31(),
                        m.m02() * p.x + m.m12() * p.y + m.m22() * p.z + m.m32(),
                        colour, v.texU(), v.texV(), packedOverlay, packedLight, nx, ny, nz);
            }
        }
    }
}
