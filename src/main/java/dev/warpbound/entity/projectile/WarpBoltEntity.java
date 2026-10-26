package dev.warpbound.entity.projectile;

import dev.warpbound.entity.WarpboundEntities;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.ThrowableProjectile;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;

/**
 * Снаряд без модели: варп-пламя ужасов, пуля культиста, ересь жреца. Виден только по следу частиц.
 * Летит прямо, без гравитации, через 3 секунды гаснет.
 */
public class WarpBoltEntity extends ThrowableProjectile {
    public enum Kind {
        PINK_FIRE, BLUE_FIRE, BULLET, HERESY
    }

    private static final EntityDataAccessor<Integer> KIND =
            SynchedEntityData.defineId(WarpBoltEntity.class, EntityDataSerializers.INT);
    private static final int LIFETIME = 60;

    private float damage = 4;

    public WarpBoltEntity(EntityType<? extends WarpBoltEntity> type, Level level) {
        super(type, level);
    }

    public WarpBoltEntity(Level level, LivingEntity owner, Kind kind, float damage) {
        super(WarpboundEntities.WARP_BOLT, owner, level);
        this.entityData.set(KIND, kind.ordinal());
        this.damage = damage;
    }

    /** Выстрел из рук стрелка по цели с разбросом. */
    public static void fire(LivingEntity shooter, LivingEntity target, Kind kind, float damage, float speed, float spread) {
        WarpBoltEntity bolt = new WarpBoltEntity(shooter.level(), shooter, kind, damage);
        Vec3 from = bolt.position();
        double dx = target.getX() - from.x;
        double dy = target.getY(0.5) - from.y;
        double dz = target.getZ() - from.z;
        bolt.shoot(dx, dy, dz, speed, spread);
        shooter.level().addFreshEntity(bolt);
    }

    public Kind kind() {
        return Kind.values()[Math.floorMod(entityData.get(KIND), Kind.values().length)];
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        builder.define(KIND, 0);
    }

    @Override
    protected double getDefaultGravity() {
        return 0;
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide) {
            trail();
        } else if (tickCount > LIFETIME) {
            discard();
        }
    }

    private void trail() {
        Vec3 v = getDeltaMovement();
        for (int i = 0; i < 3; i++) {
            double k = i / 3.0;
            double x = getX() - v.x * k, y = getY() - v.y * k, z = getZ() - v.z * k;
            level().addParticle(particle(), x, y, z, 0, 0, 0);
        }
        if (kind() == Kind.BULLET && tickCount % 2 == 0) {
            level().addParticle(ParticleTypes.SMOKE, getX(), getY(), getZ(), 0, 0, 0);
        }
    }

    private ParticleOptions particle() {
        return switch (kind()) {
            case PINK_FIRE -> new DustParticleOptions(new Vector3f(1f, 0.4f, 0.9f), 1.2f);
            case BLUE_FIRE -> new DustParticleOptions(new Vector3f(0.4f, 0.75f, 1f), 1.2f);
            case BULLET -> ParticleTypes.CRIT;
            case HERESY -> new DustParticleOptions(new Vector3f(0.75f, 0.1f, 0.9f), 1.5f);
        };
    }

    @Override
    protected void onHitEntity(EntityHitResult result) {
        super.onHitEntity(result);
        Entity target = result.getEntity();
        Entity owner = getOwner();
        if (target == owner) return;
        target.hurt(damageSources().mobProjectile(this, owner instanceof LivingEntity living ? living : null), damage);
    }

    @Override
    protected void onHit(HitResult result) {
        super.onHit(result);
        if (!level().isClientSide) discard();
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("Kind", entityData.get(KIND));
        tag.putFloat("Damage", damage);
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        entityData.set(KIND, tag.getInt("Kind"));
        damage = tag.getFloat("Damage");
    }
}
