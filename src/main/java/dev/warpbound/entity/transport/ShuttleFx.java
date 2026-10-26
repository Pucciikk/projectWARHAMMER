package dev.warpbound.entity.transport;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/** Частицы челнока на клиенте: маршевые сопла в полёте, вертикальная тяга и пыль при посадке. */
final class ShuttleFx {
    // точки модели в блоках (x вправо от модели — к её левому борту, перед — −z)
    private static final double[][] REAR = {{-0.75, 4.3, 4.6}, {0.75, 4.3, 4.6}, {-3, 3.55, 2.4}, {3, 3.55, 2.4}};
    private static final double[][] DOWN = {{-3, 2.4, 0.6}, {3, 2.4, 0.6}};
    // где старый корпус искрит: законцовки крыльев, антенны, кромки носа, орудие, моторный отсек
    private static final double[][] SPARKS = {{-4.4, 4.3, 1}, {4.4, 4.3, 1}, {-0.6, 6.8, 1.2}, {0.6, 6.8, 1.2},
            {-1.9, 3.0, -4.2}, {1.9, 3.0, -4.2}, {0, 6.2, -1}, {-1.4, 4.5, 4}, {1.4, 4.5, 4}, {-1.7, 4.6, -1.5}};

    private ShuttleFx() {
    }

    static void tick(ShuttleEntity shuttle, ShuttleEntity.Phase phase, int t) {
        Level level = shuttle.level();
        RandomSource r = shuttle.getRandom();
        boolean vertical = phase == ShuttleEntity.Phase.DESCEND || phase == ShuttleEntity.Phase.PARKED
                || phase == ShuttleEntity.Phase.APPROACH && t > ShuttleEntity.APPROACH_TICKS - 40
                || phase == ShuttleEntity.Phase.DEPART && t < 50;
        boolean cruise = phase == ShuttleEntity.Phase.APPROACH || phase == ShuttleEntity.Phase.DEPART && t > 20;

        sparks(shuttle, level, r);
        Vec3 back = shuttle.forward().scale(-1);
        if (cruise) {
            for (double[] p : REAR) {
                Vec3 at = local(shuttle, p);
                for (int i = 0; i < 2; i++) {
                    level.addParticle(ParticleTypes.FLAME, at.x + jitter(r, 0.3), at.y + jitter(r, 0.3), at.z + jitter(r, 0.3),
                            back.x * 0.5, 0, back.z * 0.5);
                }
                if (r.nextInt(2) == 0) {
                    level.addParticle(ParticleTypes.LARGE_SMOKE, at.x, at.y, at.z, back.x * 0.15, 0.02, back.z * 0.15);
                }
            }
        }
        if (!vertical) return;
        double ground = shuttle.groundY();
        for (double[] p : DOWN) {
            Vec3 at = local(shuttle, p);
            for (int i = 0; i < 3; i++) {
                level.addParticle(ParticleTypes.FLAME, at.x + jitter(r, 0.4), at.y, at.z + jitter(r, 0.6), jitter(r, 0.05), -0.45, jitter(r, 0.05));
            }
            level.addParticle(ParticleTypes.SMOKE, at.x + jitter(r, 0.5), at.y - 0.5, at.z + jitter(r, 0.5), 0, -0.25, 0);
            // поток бьёт в землю и разгоняет пыль кольцом
            if (at.y - ground < 9 && r.nextInt(2) == 0) {
                double a = r.nextDouble() * Math.PI * 2;
                double sp = 0.25 + r.nextDouble() * 0.2;
                level.addParticle(ParticleTypes.CAMPFIRE_COSY_SMOKE, at.x, ground + 0.2, at.z,
                        Math.cos(a) * sp, 0.01, Math.sin(a) * sp);
                level.addParticle(ParticleTypes.POOF, at.x + Math.cos(a), ground + 0.1, at.z + Math.sin(a),
                        Math.cos(a) * sp * 1.5, 0.02, Math.sin(a) * sp * 1.5);
            }
        }
    }

    /** Изредка искрит проводка: одиночные искры, иногда сноп с падающими угольками и дымком. */
    private static void sparks(ShuttleEntity shuttle, Level level, RandomSource r) {
        if (r.nextInt(4) != 0) return;
        Vec3 at = local(shuttle, SPARKS[r.nextInt(SPARKS.length)]);
        boolean burst = r.nextInt(6) == 0;
        for (int i = 0; i < (burst ? 7 : 2); i++) {
            level.addParticle(ParticleTypes.ELECTRIC_SPARK, at.x, at.y, at.z, jitter(r, 0.25), r.nextDouble() * 0.15, jitter(r, 0.25));
        }
        if (burst) {
            level.addParticle(ParticleTypes.LAVA, at.x, at.y, at.z, 0, 0, 0);
            level.addParticle(ParticleTypes.SMOKE, at.x, at.y + 0.1, at.z, 0, 0.04, 0);
        }
    }

    /** Точка модели (в блоках) в мире: повернуть по курсу, как это делает рендер GeckoLib. */
    static Vec3 local(ShuttleEntity shuttle, double[] p) {
        float th = (180f - shuttle.getYRot()) * Mth.DEG_TO_RAD;
        double cos = Mth.cos(th), sin = Mth.sin(th);
        return shuttle.position().add(p[0] * cos + p[2] * sin, p[1], -p[0] * sin + p[2] * cos);
    }

    private static double jitter(RandomSource r, double amp) {
        return (r.nextDouble() - 0.5) * 2 * amp;
    }
}
