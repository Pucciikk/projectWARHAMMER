package dev.warpbound.gun;

import dev.warpbound.network.GunHitPayload;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Снаряд оружия: летит по прямой, быстро, без гравитации. Попадания считает сервер; на клиенте тот же полёт нужен только для картинки,
 * поэтому там снаряд просто исчезает при столкновении.
 */
public abstract class GunProjectile extends Projectile {
    protected float damage, blastDamage, blastRadius, headMultiplier = 1.5f, knockback = 0.1f;
    protected int lifeTicks = 30;

    protected GunProjectile(EntityType<? extends GunProjectile> type, Level level) {
        super(type, level);
        noPhysics = false;
    }

    public void configure(GunSpec spec) {
        damage = spec.damage();
        blastDamage = spec.blastDamage();
        blastRadius = spec.blastRadius();
        headMultiplier = spec.head();
        knockback = spec.knockback();
        lifeTicks = spec.lifeTicks();
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
    }

    @Override
    public void tick() {
        super.tick();
        Vec3 v = getDeltaMovement();
        if (level() instanceof ServerLevel && tickCount > lifeTicks) {
            discard();
            return;
        }
        HitResult hit = ProjectileUtil.getHitResultOnMoveVector(this, this::canHitEntity);
        if (hit.getType() != HitResult.Type.MISS) {
            if (level().isClientSide) {
                // картинка: дотягиваем снаряд до точки удара, дальше его убирает сервер
                setPos(hit.getLocation());
                discard();
            } else {
                setPos(hit.getLocation());
                onHit(hit);
                discard();
            }
            return;
        }
        setPos(position().add(v));
        // поворот нужен только рендеру: снаряд с первого тика смотрит по скорости
        updateRotation();
    }

    @Override
    protected void onHitEntity(EntityHitResult result) {
        if (!(level() instanceof ServerLevel server)) return;
        Entity target = result.getEntity();
        Entity owner = getOwner();
        boolean head = target instanceof LivingEntity living && result.getLocation().y >= living.getEyeY() - 0.3;
        float dealt = head ? damage * headMultiplier : damage;
        target.invulnerableTime = 0;
        DamageSource source = damageSources().mobProjectile(this, owner instanceof LivingEntity l ? l : null);
        boolean hurt = target.hurt(source, dealt);
        if (hurt && target instanceof LivingEntity living) {
            Vec3 dir = getDeltaMovement().normalize();
            living.knockback(knockback, -dir.x, -dir.z);
            living.invulnerableTime = 0;
        }
        impactEntity(server, target, result.getLocation());
        blast(server, result.getLocation(), target);
        if (hurt && owner instanceof ServerPlayer shooter) {
            boolean killed = target instanceof LivingEntity living && !living.isAlive();
            ServerPlayNetworking.send(shooter, new GunHitPayload(head, killed));
        }
    }

    @Override
    protected void onHitBlock(BlockHitResult result) {
        if (!(level() instanceof ServerLevel server)) return;
        impactBlock(server, result);
        blast(server, result.getLocation(), null);
    }

    /** Разрыв: задевает всех рядом, кроме цели прямого попадания. Блоки не ломает: терять стены от каждого выстрела неинтересно. */
    private void blast(ServerLevel level, Vec3 at, Entity direct) {
        if (blastRadius <= 0 || blastDamage <= 0) return;
        Entity owner = getOwner();
        DamageSource source = damageSources().mobProjectile(this, owner instanceof LivingEntity l ? l : null);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new net.minecraft.world.phys.AABB(at, at).inflate(blastRadius))) {
            if (e == direct || e == owner || !e.isAlive()) continue;
            double d = e.position().add(0, e.getBbHeight() / 2, 0).distanceTo(at);
            if (d > blastRadius) continue;
            e.invulnerableTime = 0;
            e.hurt(source, blastDamage * (float) (1 - d / blastRadius / 2));
            e.invulnerableTime = 0;
        }
    }

    protected abstract void impactBlock(ServerLevel level, BlockHitResult hit);

    protected abstract void impactEntity(ServerLevel level, Entity target, Vec3 at);

    @Override
    protected boolean canHitEntity(Entity entity) {
        return entity != getOwner() && super.canHitEntity(entity);
    }

    /** Без этой настройки быстрый снаряд исчезает из вида при большой скорости. */
    @Override
    public boolean shouldRenderAtSqrDistance(double distance) {
        return distance < 256 * 256;
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        // выгруженный снаряд в полёте не нужен: снова появится только при следующем выстреле
        discard();
    }
}
