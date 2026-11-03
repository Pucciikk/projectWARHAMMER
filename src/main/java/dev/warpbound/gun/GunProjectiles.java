package dev.warpbound.gun;

import dev.warpbound.Warpbound;
import dev.warpbound.core.WarpboundSounds;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;

/** Снаряды: лазерный импульс и болт. Типы регистрируются при первом обращении, поэтому GunServer может их создавать в любой момент. */
public final class GunProjectiles {
    public static final EntityType<LasBolt> LAS_BOLT = Registry.register(BuiltInRegistries.ENTITY_TYPE, Warpbound.id("las_bolt"),
            EntityType.Builder.<LasBolt>of(LasBolt::new, MobCategory.MISC).sized(0.15f, 0.15f).clientTrackingRange(8).updateInterval(1).noSave().build("las_bolt"));
    public static final EntityType<BoltRound> BOLT_ROUND = Registry.register(BuiltInRegistries.ENTITY_TYPE, Warpbound.id("bolt_round"),
            EntityType.Builder.<BoltRound>of(BoltRound::new, MobCategory.MISC).sized(0.2f, 0.2f).clientTrackingRange(8).updateInterval(1).noSave().build("bolt_round"));

    private GunProjectiles() {
    }

    /** Лазерный импульс: тонкий и очень быстрый. На месте попадания искры и обожжённая точка. */
    public static final class LasBolt extends GunProjectile {
        public LasBolt(EntityType<? extends LasBolt> type, Level level) {
            super(type, level);
        }

        @Override
        protected void impactBlock(ServerLevel level, BlockHitResult hit) {
            Vec3 at = hit.getLocation();
            Vec3 n = Vec3.atLowerCornerOf(hit.getDirection().getNormal());
            level.sendParticles(ParticleTypes.SMALL_FLAME, at.x, at.y, at.z, 3, 0.03, 0.03, 0.03, 0.02);
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x + n.x * 0.05, at.y + n.y * 0.05, at.z + n.z * 0.05, 6, 0.04, 0.04, 0.04, 0.12);
            level.sendParticles(ParticleTypes.SMOKE, at.x + n.x * 0.08, at.y + n.y * 0.08, at.z + n.z * 0.08, 2, 0.02, 0.02, 0.02, 0.01);
            level.playSound(null, at.x, at.y, at.z, WarpboundSounds.GUN_LAS_HIT, SoundSource.PLAYERS, 0.5f, 0.95f + level.random.nextFloat() * 0.15f);
        }

        @Override
        protected void impactEntity(ServerLevel level, Entity target, Vec3 at) {
            level.sendParticles(ParticleTypes.SMALL_FLAME, at.x, at.y, at.z, 2, 0.05, 0.05, 0.05, 0.01);
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y, at.z, 4, 0.06, 0.06, 0.06, 0.1);
            target.igniteForSeconds(0.5f);
            level.playSound(null, at.x, at.y, at.z, WarpboundSounds.GUN_LAS_HIT, SoundSource.PLAYERS, 0.6f, 1.2f);
        }
    }

    /** Болт: реактивная ракетка с масс-реактивным зарядом, детонирует при попадании. */
    public static final class BoltRound extends GunProjectile {
        public BoltRound(EntityType<? extends BoltRound> type, Level level) {
            super(type, level);
        }

        private void explode(ServerLevel level, Vec3 at, Vec3 normal, BlockState block) {
            level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y, at.z, 1, 0, 0, 0, 0);
            level.sendParticles(ParticleTypes.FLAME, at.x, at.y, at.z, 12, 0.05, 0.05, 0.05, 0.12);
            level.sendParticles(ParticleTypes.LARGE_SMOKE, at.x, at.y, at.z, 6, 0.1, 0.1, 0.1, 0.03);
            if (block != null && !block.isAir()) {
                // крошка блока летит от точки удара
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, block), at.x + normal.x * 0.2, at.y + normal.y * 0.2, at.z + normal.z * 0.2, 24, 0.12, 0.12, 0.12, 0.3);
            }
            level.playSound(null, at.x, at.y, at.z, WarpboundSounds.GUN_BOLT_EXPLODE, SoundSource.PLAYERS, 1.3f, 0.9f + level.random.nextFloat() * 0.2f);
        }

        /** Дымный след: частицы по пути за тик, иначе при такой скорости след рвётся на отдельные клочки. */
        @Override
        public void tick() {
            Vec3 from = position();
            super.tick();
            if (level().isClientSide && isAlive() && tickCount > 1) {
                Vec3 step = position().subtract(from);
                for (int i = 0; i < 3; i++) {
                    Vec3 p = from.add(step.scale(i / 3.0));
                    level().addParticle(ParticleTypes.SMOKE, p.x, p.y, p.z, 0, 0.01, 0);
                }
            }
        }

        @Override
        protected void impactBlock(ServerLevel level, BlockHitResult hit) {
            explode(level, hit.getLocation(), Vec3.atLowerCornerOf(hit.getDirection().getNormal()), level.getBlockState(hit.getBlockPos()));
        }

        @Override
        protected void impactEntity(ServerLevel level, Entity target, Vec3 at) {
            explode(level, at, Vec3.ZERO, null);
        }
    }
}
