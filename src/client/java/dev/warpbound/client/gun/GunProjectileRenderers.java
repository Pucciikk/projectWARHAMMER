package dev.warpbound.client.gun;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.warpbound.Warpbound;
import dev.warpbound.gun.GunProjectile;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;

import java.util.Map;
import java.util.WeakHashMap;

/**
 * Снаряд вылетает из дула на сервере, но дуло на экране стоит чуть иначе, чем в расчёте сервера: разницу запоминаем при первом кадре
 * и убираем за несколько блоков. Пока снаряд близко, хвост привязан к дулу на экране.
 */
public final class GunProjectileRenderers {
    private static final ResourceLocation LAS_CORE = Warpbound.id("textures/effect/las_bolt.png"), BOLT_TEX = Warpbound.id("textures/entity/bolt_round.png"),
            BOLT_FLAME = Warpbound.id("textures/effect/bolt_flame.png"), BOLT_TRAIL = Warpbound.id("textures/effect/bolt_trail.png");
    /** За сколько блоков полёта картинка сходится с настоящей траекторией. */
    private static final float CONVERGE = 8f;
    private static final Map<GunProjectile, Anchor> ANCHORS = new WeakHashMap<>();

    /** Откуда снаряд вылетел и где на экране дуло относительно этой точки. */
    private record Anchor(Vec3 origin, Vec3 toMuzzle) {
    }

    private static Anchor anchor(GunProjectile p, float partial) {
        return ANCHORS.computeIfAbsent(p, e -> {
            Minecraft mc = Minecraft.getInstance();
            Vec3 origin = e.getPosition(partial);
            boolean mine = e.getOwner() == mc.player && mc.options.getCameraType().isFirstPerson();
            Vec3 muzzle = mine ? GunView.muzzleWorld(mc, partial) : e.getOwner() != null ? GunView.approxMuzzle(e.getOwner(), partial) : origin;
            Vec3 d = muzzle.subtract(origin);
            return new Anchor(origin, d.length() > 6 ? Vec3.ZERO : d);
        });
    }

    /** Сдвиг головы снаряда в кадре: от дула к настоящей траектории. */
    private static Vec3 visualShift(GunProjectile p, float partial) {
        Anchor a = anchor(p, partial);
        float flown = (float) p.getPosition(partial).distanceTo(a.origin());
        float k = 1 - Mth.clamp(flown / CONVERGE, 0, 1);
        return a.toMuzzle().scale(k * k * (3 - 2 * k));
    }

    /** Хвост: на длину следа от головы, но не дальше дула. Координаты относительно снаряда. */
    private static Vector3f tailPoint(GunProjectile p, float partial, Vector3f head, Vec3 dir, float length) {
        Anchor a = anchor(p, partial);
        Vec3 pos = p.getPosition(partial);
        if (pos.distanceTo(a.origin()) <= length) {
            Vec3 muzzle = a.origin().add(a.toMuzzle()).subtract(pos);
            return new Vector3f((float) muzzle.x, (float) muzzle.y, (float) muzzle.z);
        }
        return new Vector3f(head).sub((float) (dir.x * length), (float) (dir.y * length), (float) (dir.z * length));
    }

    private static void ribbon(VertexConsumer vc, PoseStack.Pose pose, Vector3f head, Vector3f tail, float width, float tailWidth, Vector3f cam, int r, int g, int b, int a, int tailA) {
        Vector3f dir = new Vector3f(head).sub(tail);
        if (dir.lengthSquared() < 1e-6f) return;
        Vector3f toCam = new Vector3f(cam).sub(head);
        Vector3f side = new Vector3f(dir).cross(toCam);
        if (side.lengthSquared() < 1e-8f) return;
        side.normalize();
        v(vc, pose, head.x + side.x * width, head.y + side.y * width, head.z + side.z * width, 1, 1, r, g, b, a);
        v(vc, pose, head.x - side.x * width, head.y - side.y * width, head.z - side.z * width, 1, 0, r, g, b, a);
        v(vc, pose, tail.x - side.x * tailWidth, tail.y - side.y * tailWidth, tail.z - side.z * tailWidth, 0, 0, r, g, b, tailA);
        v(vc, pose, tail.x + side.x * tailWidth, tail.y + side.y * tailWidth, tail.z + side.z * tailWidth, 0, 1, r, g, b, tailA);
    }

    private static void v(VertexConsumer vc, PoseStack.Pose p, float x, float y, float z, float u, float tv, int r, int g, int b, int a) {
        vc.addVertex(p, x, y, z).setColor(r, g, b, a).setUv(u, tv).setOverlay(OverlayTexture.NO_OVERLAY).setLight(LightTexture.FULL_BRIGHT).setNormal(p, 0, 1, 0);
    }

    /** Лазерный импульс: светло-жёлтая сердцевина в жёлтом ореоле, длинный хвост. */
    public static final class Las<T extends GunProjectile> extends EntityRenderer<T> {
        public Las(EntityRendererProvider.Context ctx) {
            super(ctx);
        }

        @Override
        public void render(T e, float yaw, float partial, PoseStack pose, MultiBufferSource buffers, int light) {
            Vec3 velocity = e.getDeltaMovement();
            if (velocity.lengthSqr() < 1e-4) return;
            Vec3 dir = velocity.normalize();
            Vec3 shift = visualShift(e, partial);
            Vector3f head = new Vector3f((float) shift.x, (float) shift.y, (float) shift.z);
            Vector3f tail = tailPoint(e, partial, head, dir, 5.5f);
            Vec3 camWorld = Minecraft.getInstance().gameRenderer.getMainCamera().getPosition();
            Vec3 pos = e.getPosition(partial);
            Vector3f cam = new Vector3f((float) (camWorld.x - pos.x), (float) (camWorld.y - pos.y), (float) (camWorld.z - pos.z));
            VertexConsumer vc = buffers.getBuffer(RenderType.eyes(LAS_CORE));
            PoseStack.Pose p = pose.last();
            // жёлтый ореол и светлая сердцевина: у головы ярче и толще, к хвосту истончается
            ribbon(vc, p, head, tail, 0.17f, 0.05f, cam, 255, 176, 20, 215, 30);
            ribbon(vc, p, head, tail, 0.065f, 0.022f, cam, 255, 240, 150, 255, 90);
            super.render(e, yaw, partial, pose, buffers, light);
        }

        @Override
        public ResourceLocation getTextureLocation(T e) {
            return LAS_CORE;
        }
    }

    /** Болт: металлическая ракетка с огнём сзади и дымным следом. */
    public static final class Bolt<T extends GunProjectile> extends EntityRenderer<T> {
        private static final int SIDES = 6;
        private static final float LEN = 0.34f, R = 0.05f;

        public Bolt(EntityRendererProvider.Context ctx) {
            super(ctx);
        }

        @Override
        public void render(T e, float yaw, float partial, PoseStack pose, MultiBufferSource buffers, int light) {
            Vec3 velocity = e.getDeltaMovement();
            if (velocity.lengthSqr() < 1e-4) return;
            Vec3 dv = velocity.normalize();
            Vector3f dir = new Vector3f((float) dv.x, (float) dv.y, (float) dv.z);
            Vector3f up = Math.abs(dir.y) > 0.95f ? new Vector3f(1, 0, 0) : new Vector3f(0, 1, 0);
            Vector3f a = new Vector3f(dir).cross(up).normalize(), b = new Vector3f(a).cross(dir).normalize();
            Vec3 shift = visualShift(e, partial);
            Vector3f c = new Vector3f((float) shift.x, (float) shift.y, (float) shift.z);
            VertexConsumer vc = buffers.getBuffer(RenderType.entityCutoutNoCull(BOLT_TEX));
            PoseStack.Pose p = pose.last();
            float spin = (e.tickCount + partial) * 1.1f;
            // корпус: шестигранник, у носа сходится к конусу, сзади поясок
            for (int i = 0; i < SIDES; i++) {
                float a0 = spin + i * Mth.TWO_PI / SIDES, a1 = spin + (i + 1) * Mth.TWO_PI / SIDES;
                body(vc, p, c, dir, a, b, a0, a1, -LEN * 0.5f, LEN * 0.18f, R, R, 0f, 0.5f, light);
                body(vc, p, c, dir, a, b, a0, a1, LEN * 0.18f, LEN * 0.5f, R, R * 0.3f, 0.5f, 1f, light);
            }
            // огонь и след
            Vector3f tailPoint = new Vector3f(c).sub(new Vector3f(dir).mul(LEN * 0.5f));
            Vec3 camWorld = Minecraft.getInstance().gameRenderer.getMainCamera().getPosition();
            Vec3 pos = e.getPosition(partial);
            Vector3f cam = new Vector3f((float) (camWorld.x - pos.x), (float) (camWorld.y - pos.y), (float) (camWorld.z - pos.z));
            VertexConsumer flame = buffers.getBuffer(RenderType.eyes(BOLT_FLAME));
            float pulse = 0.85f + 0.3f * Mth.sin((e.tickCount + partial) * 5f);
            ribbon(flame, p, tailPoint, new Vector3f(tailPoint).sub(new Vector3f(dir).mul(0.9f * pulse)), 0.11f, 0.02f, cam, 255, 190, 90, 255, 0);
            VertexConsumer trail = buffers.getBuffer(RenderType.eyes(BOLT_TRAIL));
            ribbon(trail, p, tailPoint, tailPoint(e, partial, tailPoint, dv, 7f), 0.05f, 0.15f, cam, 200, 170, 140, 170, 0);
            super.render(e, yaw, partial, pose, buffers, light);
        }

        private static void body(VertexConsumer vc, PoseStack.Pose p, Vector3f c, Vector3f dir, Vector3f a, Vector3f b, float a0, float a1, float s0, float s1, float r0, float r1, float v0, float v1, int light) {
            int full = LightTexture.pack(15, 15);
            float[][] q = {{a0, s0, r0, 0, v0}, {a1, s0, r0, 1, v0}, {a1, s1, r1, 1, v1}, {a0, s1, r1, 0, v1}};
            for (float[] k : q) {
                float cos = Mth.cos(k[0]) * k[2], sin = Mth.sin(k[0]) * k[2];
                float x = c.x + dir.x * k[1] + a.x * cos + b.x * sin;
                float y = c.y + dir.y * k[1] + a.y * cos + b.y * sin;
                float z = c.z + dir.z * k[1] + a.z * cos + b.z * sin;
                vc.addVertex(p, x, y, z).setColor(255, 255, 255, 255).setUv(k[3], 1 - k[4]).setOverlay(OverlayTexture.NO_OVERLAY).setLight(full).setNormal(p, a.x * cos + b.x * sin, a.y * cos + b.y * sin, a.z * cos + b.z * sin);
            }
        }

        @Override
        public ResourceLocation getTextureLocation(T e) {
            return BOLT_TEX;
        }
    }
}
