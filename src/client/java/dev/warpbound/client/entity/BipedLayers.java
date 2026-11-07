package dev.warpbound.client.entity;

import net.minecraft.util.Mth;
import software.bernie.geckolib.animation.AnimationProcessor;
import software.bernie.geckolib.cache.object.GeoBone;

/**
 * Добавки поверх позы двуногих в броне (NPC Астартес и игрок в этой модели), раз в кадр после BipedMotion.
 * Внутренние оси GeckoLib: rotX > 0 запрокидывает назад (у руки — вперёд), rotY > 0 поворачивает влево. Значения — в градусах.
 */
public final class BipedLayers {
    private static final float DEG = Mth.DEG_TO_RAD;

    private BipedLayers() {
    }

    /** Вес ног в ударе по скорости тела: на месте подшаг, с 1,2 блока в секунду ноги не трогаем. */
    public static float lowerWeight(float speed) {
        return 1 - Mth.clamp(speed / 1.2f, 0, 1);
    }

    /** Толчок назад от попадания: грудь откидывается, голова по инерции кивает, руки разлетаются. Затухает за 0,4 с. */
    public static void flinch(AnimationProcessor<?> p, int hurtTime, int hurtDuration, float pt, boolean leftSide) {
        if (hurtTime <= 0 || hurtDuration <= 0) return;
        float sec = (hurtDuration - hurtTime + pt) / 20f;
        float k = (float) Math.exp(-sec * 7) * Math.min(1, sec * 25);
        float side = leftSide ? 1 : -1;
        add(p, "abdomen", 4 * k, 2 * side * k, 0);
        add(p, "chest", 9 * k, 5 * side * k, 2 * side * k);
        add(p, "head", -7 * k, -4 * side * k, 0);
        add(p, "arm_l", -7 * k, -6 * k, 0);
        add(p, "arm_r", -7 * k, 6 * k, 0);
        add(p, "forearm_l", -10 * k, 0, 0);
        add(p, "forearm_r", -10 * k, 0, 0);
    }

    /** Голова за взглядом, грудь берёт четверть поворота. Смотрит вниз (pitch > 0) — голова опускается. */
    public static void look(AnimationProcessor<?> p, float yaw, float pitch) {
        yaw = Mth.clamp(yaw, -60f, 60f);
        pitch = Mth.clamp(pitch, -40f, 45f);
        add(p, "head", -pitch * 0.8f, -yaw * 0.75f, 0);
        add(p, "chest", -pitch * 0.2f, -yaw * 0.25f, 0);
    }

    /** Добавка в градусах к текущему повороту кости. */
    public static void add(AnimationProcessor<?> p, String name, float x, float y, float z) {
        GeoBone b = p.getBone(name);
        if (b == null) return;
        b.setRotX(b.getRotX() + x * DEG);
        b.setRotY(b.getRotY() + y * DEG);
        b.setRotZ(b.getRotZ() + z * DEG);
    }
}
