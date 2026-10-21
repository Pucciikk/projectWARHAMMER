package dev.warpbound.client.entity;

import dev.warpbound.entity.dreadnought.DreadnoughtEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Шаги дредноута на клиенте: глухой удар, пыль из-под ступни и тряска камеры,
 * которая слабеет с расстоянием. Пилоту трясёт сильнее всех.
 */
public final class DreadnoughtFx {
    private static final float SHAKE_RADIUS = 24f;
    private static float shake;
    private static long lastNanos;

    private DreadnoughtFx() {
    }

    public static void register() {
        DreadnoughtEntity.stepListener = DreadnoughtFx::onStep;
    }

    private static void onStep(DreadnoughtEntity e, boolean rightFoot) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null) {
            return;
        }
        float yaw = e.yBodyRot * Mth.DEG_TO_RAD;
        float side = (rightFoot ? 0.75f : -0.75f) * DreadnoughtEntity.SCALE;
        double fx = e.getX() - Mth.cos(yaw) * side - Mth.sin(yaw) * 0.5;
        double fz = e.getZ() - Mth.sin(yaw) * side + Mth.cos(yaw) * 0.5;
        double fy = e.getY();

        float strength = e.stride * (1f + 0.4f * e.run);
        mc.level.playLocalSound(fx, fy, fz, SoundEvents.IRON_GOLEM_STEP, SoundSource.NEUTRAL,
                1.6f * strength, 0.5f + mc.level.random.nextFloat() * 0.08f, false);
        mc.level.playLocalSound(fx, fy, fz, SoundEvents.RAVAGER_STEP, SoundSource.NEUTRAL,
                0.7f * strength, 0.55f, false);

        BlockState ground = mc.level.getBlockState(BlockPos.containing(fx, fy - 0.2, fz));
        if (ground.getRenderShape() != RenderShape.INVISIBLE) {
            BlockParticleOption dust = new BlockParticleOption(ParticleTypes.BLOCK, ground);
            for (int i = 0; i < 22; i++) {
                double a = mc.level.random.nextDouble() * Mth.TWO_PI;
                double r = 0.4 + mc.level.random.nextDouble() * 0.8;
                mc.level.addParticle(dust, fx + Math.cos(a) * r, fy + 0.1, fz + Math.sin(a) * r,
                        Math.cos(a) * 0.15, 0.12, Math.sin(a) * 0.15);
            }
        }

        Entity viewer = mc.getCameraEntity();
        if (viewer != null) {
            float amount;
            if (viewer.getVehicle() == e) {
                amount = 1.0f;
            } else {
                float dist = (float) viewer.position().distanceTo(e.position());
                amount = Math.max(0f, 1f - dist / SHAKE_RADIUS) * 0.6f;
            }
            shake = Math.max(shake, amount * strength);
        }
    }

    /** Смещение камеры {yaw, pitch, dy} на этот кадр. Вызывается из CameraMixin. */
    public static float[] cameraOffset(float time) {
        long now = System.nanoTime();
        float dt = lastNanos == 0 ? 0f : Math.min(0.1f, (now - lastNanos) / 1.0e9f);
        lastNanos = now;
        shake = Math.max(0f, shake - dt * 2.8f);
        if (shake <= 0f) {
            return null;
        }
        float k = shake * shake;
        return new float[]{
                Mth.sin(time * 1.7f) * 0.35f * k,
                Mth.sin(time * 2.3f + 1.3f) * 0.9f * k,
                -Math.abs(Mth.sin(time * 0.9f)) * 0.08f * k,
        };
    }
}
