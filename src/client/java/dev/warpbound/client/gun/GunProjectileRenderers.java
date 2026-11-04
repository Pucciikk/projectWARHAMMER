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
 * Снаряды объёмные. Свой выстрел игрок видит как предсказанный снаряд: он создаётся на клиенте у дула на экране (GunClient), настоящий снаряд сервера у стрелка не рисуется.
 * Чужой снаряд приходит от сервера, поэтому первые блоки полёта картинка сводится от дула чужого оружия к настоящей траектории.
 */
public final class GunProjectileRenderers {
    private static final ResourceLocation BOLT_TEX = Warpbound.id("textures/entity/bolt_round.png");
    /** За сколько блоков полёта картинка чужого снаряда сходится с настоящей траекторией. */
    private static final float CONVERGE = 8f;
    /** С какого расстояния снаряд начинает расти, чтобы вдали не пропадал совсем. */
    private static final float FAR = 14f;
    private static final Map<GunProjectile, Anchor> ANCHORS = new WeakHashMap<>();

    private record Anchor(Vec3 origin, Vec3 toMuzzle) {
    }

    private static Anchor anchor(GunProjectile p, float partial) {
        return ANCHORS.computeIfAbsent(p, e -> {
            if (e.predicted && e.origin != null) return new Anchor(e.origin, Vec3.ZERO);
            Vec3 origin = e.getPosition(partial);
            Vec3 muzzle = e.getOwner() instanceof net.minecraft.world.entity.player.Player ? GunRenderer.worldMuzzle(e.getOwner(), partial) : origin;
            Vec3 d = muzzle.subtract(origin);
            return new Anchor(origin, d.length() > 6 ? Vec3.ZERO : d);
        });
    }

    /** Свой настоящий снаряд не рисуем: вместо него предсказанный. */
    private static boolean hidden(GunProjectile e) {
        return !e.predicted && e.getOwner() == Minecraft.getInstance().player;
    }

    /** Сдвиг головы снаряда в кадре: от дула к настоящей траектории. */
    private static Vector3f headOffset(GunProjectile p, float partial, Anchor a) {
        float flown = (float) p.getPosition(partial).distanceTo(a.origin());
        float k = 1 - Mth.clamp(flown / CONVERGE, 0, 1);
        Vec3 s = a.toMuzzle().scale(k * k * (3 - 2 * k));
        return new Vector3f((float) s.x, (float) s.y, (float) s.z);
    }

    private static Vector3f direction(GunProjectile e) {
        Vec3 d = e.getDeltaMovement().normalize();
        return new Vector3f((float) d.x, (float) d.y, (float) d.z);
    }

    private static float farScale(GunProjectile e, float partial) {
        Vec3 cam = Minecraft.getInstance().gameRenderer.getMainCamera().getPosition();
        return Math.max(1f, (float) e.getPosition(partial).distanceTo(cam) / FAR);
    }

    /** Лазерный импульс: плотная светло-жёлтая игла в двух жёлтых оболочках, хвост начинается у дула и не длиннее пройденного пути. */
    public static final class Las<T extends GunProjectile> extends EntityRenderer<T> {
        private static final float TAIL = 7.5f;

        public Las(EntityRendererProvider.Context ctx) {
            super(ctx);
        }

        @Override
        public void render(T e, float yaw, float partial, PoseStack pose, MultiBufferSource buffers, int light) {
            if (e.getDeltaMovement().lengthSqr() < 1e-4 || hidden(e)) return;
            Anchor a = anchor(e, partial);
            Vector3f dir = direction(e), head = headOffset(e, partial, a);
            float flown = (float) e.getPosition(partial).distanceTo(a.origin());
            float len = Mth.clamp(flown, 0.05f, TAIL);
            float k = farScale(e, partial);
            PoseStack.Pose p = pose.last();
            float r = 0.05f * k;
            ShotMesh.tube(buffers.getBuffer(ShotMesh.solid()), p, head, dir, new float[][]{
                    {r * 3.2f, 0, 255, 240, 130, 255}, {r * 1.6f, r * 0.8f, 255, 240, 130, 255}, {0, r, 255, 236, 110, 255},
                    {-len * 0.45f, r * 0.72f, 255, 214, 60, 255}, {-len, 0, 255, 184, 30, 255}}, 8);
            VertexConsumer glow = buffers.getBuffer(ShotMesh.glow());
            float r1 = r * 2.3f, r2 = r * 4.2f;
            ShotMesh.tube(glow, p, head, dir, new float[][]{
                    {r1 * 2.4f, 0, 255, 206, 50, 0}, {r1 * 1.1f, r1 * 0.85f, 255, 206, 50, 150}, {0, r1, 255, 200, 40, 165},
                    {-len * 0.5f, r1 * 0.62f, 255, 186, 30, 110}, {-len, 0, 255, 170, 20, 0}}, 8);
            ShotMesh.tube(glow, p, head, dir, new float[][]{
                    {r2 * 1.8f, 0, 255, 170, 20, 0}, {r2 * 0.7f, r2 * 0.85f, 255, 170, 20, 62}, {0, r2, 255, 160, 16, 70},
                    {-len * 0.42f, r2 * 0.5f, 255, 150, 12, 36}, {-len * 0.85f, 0, 255, 140, 10, 0}}, 8);
            super.render(e, yaw, partial, pose, buffers, light);
        }

        @Override
        public ResourceLocation getTextureLocation(T e) {
            return ShotMesh.WHITE;
        }
    }

    /** Болт: стальной нос, латунный корпус, стабилизаторы, факел двигателя и дымный след, который начинается от дула. */
    public static final class Bolt<T extends GunProjectile> extends EntityRenderer<T> {
        private static final int SIDES = 12;
        private static final float LEN = 0.46f, R = 0.062f, TRAIL = 6.5f;
        /** Профиль корпуса: {доля длины от середины к носу, доля радиуса, v текстуры}. */
        private static final float[][] PROFILE = {
                {0.5f, 0.03f, 0f}, {0.42f, 0.36f, 0.1f}, {0.27f, 0.74f, 0.24f}, {0.14f, 1f, 0.36f}, {0.1f, 1f, 0.4f}, {-0.3f, 1f, 0.78f}, {-0.33f, 0.86f, 0.82f}, {-0.42f, 0.8f, 0.9f}, {-0.5f, 0.62f, 1f}};

        public Bolt(EntityRendererProvider.Context ctx) {
            super(ctx);
        }

        @Override
        public void render(T e, float yaw, float partial, PoseStack pose, MultiBufferSource buffers, int light) {
            if (e.getDeltaMovement().lengthSqr() < 1e-4 || hidden(e)) return;
            Anchor anchor = anchor(e, partial);
            Vector3f dir = direction(e), c = headOffset(e, partial, anchor);
            float flown = (float) e.getPosition(partial).distanceTo(anchor.origin());
            float k = farScale(e, partial);
            float len = LEN * k, rad = R * k;
            PoseStack.Pose p = pose.last();
            float time = e.tickCount + partial;
            float spin = time * 1.4f;
            Vector3f a = ShotMesh.axisA(dir), b = new Vector3f(a).cross(dir).normalize();
            VertexConsumer vc = buffers.getBuffer(RenderType.entityCutoutNoCull(BOLT_TEX));
            int lit = LightTexture.pack(15, 15);
            for (int i = 0; i + 1 < PROFILE.length; i++) {
                float[] p0 = PROFILE[i], p1 = PROFILE[i + 1];
                for (int j = 0; j < SIDES; j++) {
                    float t0 = spin + j * Mth.TWO_PI / SIDES, t1 = spin + (j + 1) * Mth.TWO_PI / SIDES;
                    body(vc, p, c, dir, a, b, t0, p0, j / (float) SIDES, len, rad, lit);
                    body(vc, p, c, dir, a, b, t1, p0, (j + 1) / (float) SIDES, len, rad, lit);
                    body(vc, p, c, dir, a, b, t1, p1, (j + 1) / (float) SIDES, len, rad, lit);
                    body(vc, p, c, dir, a, b, t0, p1, j / (float) SIDES, len, rad, lit);
                }
            }
            // четыре стабилизатора
            for (int i = 0; i < 4; i++) {
                float t = spin + i * Mth.HALF_PI;
                float cos = Mth.cos(t), sin = Mth.sin(t);
                Vector3f out = new Vector3f(a).mul(cos).add(new Vector3f(b).mul(sin));
                fin(vc, p, c, dir, out, -0.26f * len, rad, 0f, lit);
                fin(vc, p, c, dir, out, -0.5f * len, rad, rad * 0.95f, lit);
                fin(vc, p, c, dir, out, -0.5f * len, rad, 0f, lit);
                fin(vc, p, c, dir, out, -0.26f * len, rad, rad * 0.25f, lit);
            }
            // двигатель загорается не сразу: первые блоки болт идёт на вышибном заряде
            float burn = Mth.clamp((flown - 0.6f) / 1.4f, 0, 1);
            Vector3f nozzle = new Vector3f(c).sub(new Vector3f(dir).mul(len * 0.5f));
            if (burn > 0) {
                float pulse = 0.85f + 0.25f * Mth.sin(time * 9f);
                float fl = 1.1f * k * pulse * burn;
                VertexConsumer glow = buffers.getBuffer(ShotMesh.glow());
                ShotMesh.tube(glow, p, nozzle, dir, new float[][]{
                        {0.02f, rad * 0.9f, 255, 150, 30, 200}, {-fl * 0.32f, rad * 1.15f, 255, 120, 20, 150}, {-fl, 0, 255, 70, 10, 0}}, 8);
                ShotMesh.tube(glow, p, nozzle, dir, new float[][]{
                        {0.03f, rad * 0.62f, 255, 244, 190, 255}, {-fl * 0.3f, rad * 0.5f, 255, 224, 120, 230}, {-fl * 0.62f, 0, 255, 180, 50, 0}}, 8);
            }
            // дымный след: расширяется и тает, не длиннее пройденного пути
            float trail = Math.min(TRAIL, flown) - len * 0.5f;
            if (trail > 0.1f) {
                VertexConsumer glow = buffers.getBuffer(ShotMesh.glow());
                ShotMesh.tube(glow, p, nozzle, dir, new float[][]{
                        {0, rad * 0.7f, 190, 182, 170, 120}, {-trail * 0.3f, rad * 1.5f, 170, 165, 158, 74}, {-trail * 0.65f, rad * 2.4f, 150, 148, 145, 34}, {-trail, rad * 3.2f, 140, 140, 140, 0}}, 7);
            }
            super.render(e, yaw, partial, pose, buffers, light);
        }

        private static void body(VertexConsumer vc, PoseStack.Pose p, Vector3f c, Vector3f dir, Vector3f a, Vector3f b, float t, float[] prof, float u, float len, float rad, int lit) {
            float cos = Mth.cos(t), sin = Mth.sin(t), r = prof[1] * rad, s = prof[0] * len;
            float nx = a.x * cos + b.x * sin, ny = a.y * cos + b.y * sin, nz = a.z * cos + b.z * sin;
            vc.addVertex(p, c.x + dir.x * s + nx * r, c.y + dir.y * s + ny * r, c.z + dir.z * s + nz * r)
                    .setColor(255, 255, 255, 255).setUv(u, prof[2]).setOverlay(OverlayTexture.NO_OVERLAY).setLight(lit).setNormal(p, nx, ny, nz);
        }

        private static void fin(VertexConsumer vc, PoseStack.Pose p, Vector3f c, Vector3f dir, Vector3f out, float s, float rad, float extra, int lit) {
            float r = rad * 0.9f + extra;
            vc.addVertex(p, c.x + dir.x * s + out.x * r, c.y + dir.y * s + out.y * r, c.z + dir.z * s + out.z * r)
                    .setColor(255, 255, 255, 255).setUv(0.5f, 0.95f).setOverlay(OverlayTexture.NO_OVERLAY).setLight(lit).setNormal(p, out.x, out.y, out.z);
        }

        @Override
        public ResourceLocation getTextureLocation(T e) {
            return BOLT_TEX;
        }
    }
}
