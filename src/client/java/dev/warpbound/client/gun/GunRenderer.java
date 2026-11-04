package dev.warpbound.client.gun;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.warpbound.Warpbound;
import dev.warpbound.client.multiblock.MeshModelFactory;
import dev.warpbound.gun.GunItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
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
 * а вне первого лица (в инвентаре, в руке у других игроков) оружие просто в покое. Приклад в виде от первого лица не рисуем: он закрывал бы обзор.
 */
public final class GunRenderer extends GeoItemRenderer<GunItem> {
    /** Куда в кадре попали руки, дуло и окно выброса: заполняется при отрисовке костей. */
    static final Map<String, Matrix4f> CAPTURED = new HashMap<>();
    static final Map<String, Matrix3f> CAPTURED_NORMAL = new HashMap<>();
    private static final Map<String, GunRenderer> ALL = new HashMap<>();
    /** Где в мире дуло у того, кто держит оружие: снаряд должен вылетать отсюда. По id сущности. */
    private static final Map<Integer, Vec3> WORLD_MUZZLE = new HashMap<>();
    /** До какого времени (наносекунды) горит вспышка у стрелка в виде со стороны. */
    private static final Map<Integer, Long> WORLD_FLASH = new HashMap<>();
    private static final long FLASH_NANOS = 60_000_000L;
    /** Включается только на время вида от первого лица. */
    static boolean viewPass;
    /** Кто держит оружие, пока рисуется слой предмета в руке (миксин ItemInHandLayer). */
    private static LivingEntity holder;
    static boolean glowPass;
    private Matrix4f pendingFlash;
    private Matrix3f pendingFlashNormal;
    private boolean pendingLas;

    private GunRenderer(String model) {
        super(new Model(model));
        addRenderLayer(new Glow<>(this));
    }

    public static GunRenderer of(String model) {
        return ALL.computeIfAbsent(model, GunRenderer::new);
    }

    public static void setHolder(LivingEntity entity) {
        holder = entity;
    }

    static void markFlash(int entityId) {
        WORLD_FLASH.put(entityId, System.nanoTime() + FLASH_NANOS);
    }

    /** Дуло стрелка в мире: снято при последней отрисовке его оружия, иначе примерно от головы. */
    static Vec3 worldMuzzle(Entity shooter, float partial) {
        Vec3 known = WORLD_MUZZLE.get(shooter.getId());
        if (known != null && known.distanceToSqr(shooter.getEyePosition(partial)) < 16) return known;
        return GunView.approxMuzzle(shooter, partial);
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
                    ? GunClient.activeClip(GunVisual.of(GunClient.held()), Minecraft.getInstance(), seconds)
                    : GunClips.get(name, "idle");
            if (!viewPass) seconds[0] = 0;
            for (String bone : clip.tracks().keySet()) {
                if (bone.equals("_view") || !clip.sample(bone, seconds[0], out)) continue;
                getBone(bone).ifPresent(b -> applyPose(b, out));
            }
        }
    }

    /** Оси Blender -> GeckoLib: те же, что в экспорте (x, z, y) и в kit.auto_tracks. */
    static void applyPose(GeoBone b, float[] out) {
        b.setPosX(out[0] * 16);
        b.setPosY(out[2] * 16);
        b.setPosZ(out[1] * 16);
        b.setRotX((float) Math.toRadians(-out[3]));
        b.setRotY((float) Math.toRadians(out[5]));
        b.setRotZ((float) Math.toRadians(out[4]));
    }

    /** Слой свечения: те же кости, но только светящиеся грани и другая текстура. */
    static final class Glow<T extends net.minecraft.world.item.Item & software.bernie.geckolib.animatable.GeoAnimatable> extends GeoRenderLayer<T> {
        Glow(GeoRenderer<T> renderer) {
            super(renderer);
        }

        @Override
        public void render(PoseStack poseStack, T animatable, BakedGeoModel model, RenderType renderType, MultiBufferSource bufferSource,
                           VertexConsumer buffer, float partialTick, int packedLight, int packedOverlay) {
            ResourceLocation tex = getRenderer().getTextureLocation(animatable);
            RenderType eyes = RenderType.eyes(tex.withPath(p -> p.replace(".png", "_glow.png")));
            glowPass = true;
            getRenderer().reRender(model, poseStack, bufferSource, animatable, eyes, bufferSource.getBuffer(eyes), partialTick,
                    LightTexture.FULL_BRIGHT, packedOverlay, 0xFFFFFFFF);
            glowPass = false;
        }
    }

    @Override
    public void renderByItem(ItemStack stack, ItemDisplayContext context, PoseStack poseStack, MultiBufferSource buffers, int light, int overlay) {
        pendingFlash = null;
        pendingLas = stack.getItem() instanceof GunItem gun && gun.mechanics.kind() == GunItem.Kind.LAS;
        super.renderByItem(stack, context, poseStack, buffers, light, overlay);
        // вспышку рисуем после предмета: смена типа рендера посреди модели закрыла бы её буфер
        if (pendingFlash != null) {
            PoseStack p = new PoseStack();
            p.last().pose().set(pendingFlash);
            p.last().normal().set(pendingFlashNormal);
            ShotMesh.flash(buffers, p.last(), pendingLas, pendingLas ? 0.11f : 0.17f, 0.8f, System.nanoTime() % 6283 / 1000f);
            pendingFlash = null;
        }
    }

    @Override
    public void renderRecursively(PoseStack poseStack, GunItem animatable, GeoBone bone, RenderType renderType, MultiBufferSource bufferSource, VertexConsumer buffer,
                                  boolean isReRender, float partialTick, int packedLight, int packedOverlay, int colour) {
        if (viewPass && bone.getName().equals("stock")) return;
        if (!isReRender && isLocator(bone.getName())) {
            if (viewPass) {
                capture(poseStack, bone);
            } else if (holder != null && bone.getName().equals("muzzle")) {
                captureWorldMuzzle(poseStack, bone);
            }
        }
        super.renderRecursively(poseStack, animatable, bone, renderType, bufferSource, buffer, isReRender, partialTick, packedLight, packedOverlay, colour);
    }

    static void capture(PoseStack poseStack, GeoBone bone) {
        poseStack.pushPose();
        RenderUtil.prepMatrixForBone(poseStack, bone);
        // начало координат в точке вращения: руки и вспышка строятся от неё
        poseStack.translate(bone.getPivotX() / 16f, bone.getPivotY() / 16f, bone.getPivotZ() / 16f);
        CAPTURED.put(bone.getName(), new Matrix4f(poseStack.last().pose()));
        CAPTURED_NORMAL.put(bone.getName(), new Matrix3f(poseStack.last().normal()));
        poseStack.popPose();
    }

    /** Слой предмета в руке рисуется в координатах «мир минус камера», без поворота камеры: сдвиг матрицы и есть положение в мире. */
    private void captureWorldMuzzle(PoseStack poseStack, GeoBone bone) {
        poseStack.pushPose();
        RenderUtil.prepMatrixForBone(poseStack, bone);
        poseStack.translate(bone.getPivotX() / 16f, bone.getPivotY() / 16f, bone.getPivotZ() / 16f);
        Vector3f t = poseStack.last().pose().getTranslation(new Vector3f());
        Vec3 cam = Minecraft.getInstance().gameRenderer.getMainCamera().getPosition();
        WORLD_MUZZLE.put(holder.getId(), cam.add(t.x, t.y, t.z));
        Long until = WORLD_FLASH.get(holder.getId());
        if (until != null && until > System.nanoTime()) {
            pendingFlash = new Matrix4f(poseStack.last().pose());
            pendingFlashNormal = new Matrix3f(poseStack.last().normal());
        }
        poseStack.popPose();
    }

    static boolean isLocator(String name) {
        return name.equals("arm_r") || name.equals("arm_l") || name.equals("muzzle") || name.equals("eject") || name.equals("exhaust");
    }

    /** Меш рисуем напрямую, как у машин: GeckoLib считает кубы иначе и переворачивает плоские грани. */
    @Override
    public void renderCube(PoseStack poseStack, GeoCube cube, VertexConsumer buffer, int packedLight, int packedOverlay, int colour) {
        if (cube.size().x >= 0) {
            super.renderCube(poseStack, cube, buffer, packedLight, packedOverlay, colour);
            return;
        }
        drawMesh(poseStack, cube, buffer, packedLight, packedOverlay, colour);
    }

    public static void drawMesh(PoseStack poseStack, GeoCube cube, VertexConsumer buffer, int packedLight, int packedOverlay, int colour) {
        if (glowPass && cube.size().x == MeshModelFactory.MESH_PLAIN) return;
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
