package dev.warpbound.client.gun;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.warpbound.Warpbound;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import org.joml.Vector3f;

/**
 * Объёмные эффекты выстрела: настоящие тела вращения вместо лент, повёрнутых к камере. Свет рисуем обычным смешиванием, а не сложением:
 * при сложении жёлтое на ярком небе уходит в белое, а так остаётся жёлтым и днём.
 */
final class ShotMesh {
    static final ResourceLocation WHITE = Warpbound.id("textures/effect/white.png");

    private ShotMesh() {
    }

    static RenderType solid() {
        return RenderType.beaconBeam(WHITE, false);
    }

    static RenderType glow() {
        return RenderType.beaconBeam(WHITE, true);
    }

    /** Ось a, перпендикулярная направлению. b получается как a × dir. */
    static Vector3f axisA(Vector3f dir) {
        Vector3f up = Math.abs(dir.y) > 0.95f ? new Vector3f(1, 0, 0) : new Vector3f(0, 1, 0);
        return new Vector3f(dir).cross(up).normalize();
    }

    /**
     * Тело вращения вдоль dir от точки c. rings: {смещение вдоль dir, радиус, r, g, b, a}, цвет 0..255, кольца идут от головы к хвосту (смещение убывает).
     * Обход граней наружу: у этих типов рендера задние грани отсекаются.
     */
    static void tube(VertexConsumer vc, PoseStack.Pose pose, Vector3f c, Vector3f dir, float[][] rings, int sides) {
        Vector3f a = axisA(dir), b = new Vector3f(a).cross(dir).normalize();
        for (int i = 0; i + 1 < rings.length; i++) {
            float[] r0 = rings[i], r1 = rings[i + 1];
            for (int j = 0; j < sides; j++) {
                float t0 = j * Mth.TWO_PI / sides, t1 = (j + 1) * Mth.TWO_PI / sides;
                // голова впереди: кольцо r0 дальше по dir, поэтому обход такой
                vertex(vc, pose, c, dir, a, b, t0, r1);
                vertex(vc, pose, c, dir, a, b, t0, r0);
                vertex(vc, pose, c, dir, a, b, t1, r0);
                vertex(vc, pose, c, dir, a, b, t1, r1);
            }
        }
    }

    private static void vertex(VertexConsumer vc, PoseStack.Pose pose, Vector3f c, Vector3f dir, Vector3f a, Vector3f b, float t, float[] r) {
        float cos = Mth.cos(t) * r[1], sin = Mth.sin(t) * r[1];
        vc.addVertex(pose, c.x + dir.x * r[0] + a.x * cos + b.x * sin, c.y + dir.y * r[0] + a.y * cos + b.y * sin, c.z + dir.z * r[0] + a.z * cos + b.z * sin)
                .setColor((int) r[2], (int) r[3], (int) r[4], (int) r[5]).setUv(0.5f, 0.5f).setLight(LightTexture.FULL_BRIGHT).setNormal(pose, 0, 1, 0);
    }

    /**
     * Вспышка у дула в пространстве кости: ствол смотрит в -Z. Язык пламени вперёд, лучи вбок и горячая сердцевина.
     * life от 1 (только что) до 0 (гаснет), size — радиус в единицах позы.
     */
    static void flash(MultiBufferSource buffers, PoseStack.Pose pose, boolean las, float size, float life, float spin) {
        Vector3f forward = new Vector3f(0, 0, -1), at = new Vector3f();
        int hr = 255, hg = las ? 246 : 244, hb = las ? 170 : 190;
        int or = 255, og = las ? 176 : 124, ob = las ? 24 : 26;
        float s = size * (0.75f + 0.45f * life);
        int alpha = (int) (150 + 90 * life);
        VertexConsumer glow = buffers.getBuffer(glow());
        // язык вперёд, виден сбоку и от бедра
        tube(glow, pose, at, forward, new float[][]{{s * 3.4f, 0, or, og, ob, 0}, {s * 1.8f, s * 0.3f, or, og, ob, alpha / 2f}, {s * 0.4f, s * 0.42f, or, og, ob, alpha}, {-s * 0.02f, s * 0.2f, or, og, ob, alpha}}, 10);
        // мягкий диск к стрелку: от прозрачного края к плотной середине, грани смотрят назад
        tube(glow, pose, at, forward, new float[][]{{0, s * 0.85f, or, og, ob, 0}, {-s * 0.04f, s * 0.42f, or, og, ob, alpha * 0.5f}, {-s * 0.1f, s * 0.2f, hr, hg, hb, alpha}, {-s * 0.13f, 0, hr, hg, hb, 255}}, 20);
        // лучи вбок: тормоз болтера выбрасывает газы в стороны, у лазгана они короче
        int rays = las ? 5 : 6;
        float rayLen = s * (las ? 1.15f : 1.9f);
        for (int i = 0; i < rays; i++) {
            float t = spin + i * Mth.TWO_PI / rays;
            float len = rayLen * (0.75f + 0.25f * Mth.sin(spin * 3 + i * 2.1f));
            Vector3f d = new Vector3f(Mth.cos(t), Mth.sin(t), -0.22f).normalize();
            tube(glow, pose, at, d, new float[][]{{len, 0, or, og, ob, 0}, {len * 0.45f, s * 0.2f, or, og, ob, alpha * 0.7f}, {0, s * 0.1f, or, og, ob, alpha}}, 5);
        }
        // сердцевина рисуется последней и почти непрозрачная
        tube(glow, pose, at, forward, new float[][]{{s * 1.9f, 0, hr, hg, hb, 0}, {s * 0.9f, s * 0.22f, hr, hg, hb, 235}, {s * 0.1f, s * 0.34f, hr, hg, hb, 255}, {-s * 0.1f, 0, hr, hg, hb, 255}}, 8);
    }
}
