package dev.warpbound.entity.boarding;

import dev.warpbound.entity.WarpboundEntities;
import dev.warpbound.entity.anim.WarpAnim;
import dev.warpbound.entity.cult.CultistEntity;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.animation.AnimationController;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * Десантный модуль абордажа (М6): падает носом вниз, врезается, через секунду раскрывает
 * лепестки и выпускает десант. Через минуту остов исчезает.
 * <p>
 * Пока десант — культисты: модели Еретиков Астартес есть у автора, подключим их отдельным шагом.
 * Варп-событие «Абордаж» будет запускать модуль через {@link #launch}; {@code /summon} роняет его с высоты.
 */
public class BoardingPodEntity extends Entity implements GeoEntity {
    public enum State {
        PENDING, FLYING, LANDED, OPEN
    }

    private static final EntityDataAccessor<Integer> STATE =
            SynchedEntityData.defineId(BoardingPodEntity.class, EntityDataSerializers.INT);
    private static final int OPEN_DELAY = 30;
    private static final int UNLOAD_DELAY = 26;
    private static final int LIFETIME = 20 * 60;
    private static final int DROP_HEIGHT = 24;
    private static final int TROOPS = 3;

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private int stateTicks;

    public BoardingPodEntity(EntityType<? extends BoardingPodEntity> type, Level level) {
        super(type, level);
    }

    /** Запустить модуль из точки по направлению; он летит, пока не упрётся. */
    public void launch(Vec3 from, Vec3 velocity) {
        setPos(from);
        setDeltaMovement(velocity);
        setState(State.FLYING);
    }

    public State state() {
        return State.values()[Math.floorMod(entityData.get(STATE), State.values().length)];
    }

    private void setState(State state) {
        entityData.set(STATE, state.ordinal());
        stateTicks = 0;
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        builder.define(STATE, State.PENDING.ordinal());
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide) {
            if (state() == State.FLYING) flightTrail();
            return;
        }
        ServerLevel server = (ServerLevel) level();
        stateTicks++;
        switch (state()) {
            case PENDING -> dropFromAbove(server);
            case FLYING -> fly(server);
            case LANDED -> {
                if (stateTicks % 5 == 0) server.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY(1), getZ(), 3, 0.5, 0.2, 0.5, 0.02);
                if (stateTicks >= OPEN_DELAY) open(server);
            }
            case OPEN -> {
                if (stateTicks == UNLOAD_DELAY) unload(server);
                if (stateTicks > LIFETIME) discard();
            }
        }
    }

    /** Заспавнен командой или яйцом: поднимаемся, сколько позволяет потолок, и падаем. */
    private void dropFromAbove(ServerLevel server) {
        Vec3 here = position();
        HitResult hit = server.clip(new ClipContext(here.add(0, 4, 0), here.add(0, DROP_HEIGHT, 0),
                ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        double top = hit.getType() == HitResult.Type.MISS ? here.y + DROP_HEIGHT : hit.getLocation().y - getBbHeight() - 0.5;
        launch(new Vec3(here.x, Math.max(here.y, top), here.z), new Vec3(0, -1.4, 0));
    }

    private void fly(ServerLevel server) {
        Vec3 before = getDeltaMovement();
        move(MoverType.SELF, before);
        if (horizontalCollision || verticalCollision || onGround() || stateTicks > 200) {
            impact(server);
        }
    }

    private void impact(ServerLevel server) {
        setDeltaMovement(Vec3.ZERO);
        setState(State.LANDED);
        server.playSound(null, blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 3f, 0.6f);
        server.playSound(null, blockPosition(), SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2f, 0.5f);
        server.sendParticles(ParticleTypes.EXPLOSION_EMITTER, getX(), getY(), getZ(), 1, 0, 0, 0, 0);
        server.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, getX(), getY() + 0.5, getZ(), 30, 1.5, 0.3, 1.5, 0.03);
        // удар не ломает блоки, но отбрасывает и ранит тех, кто под ним
        for (LivingEntity victim : server.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(2.5))) {
            victim.hurt(damageSources().explosion(this, null), 8);
            Vec3 push = victim.position().subtract(position()).normalize().scale(1.2);
            victim.push(push.x, 0.4, push.z);
        }
    }

    private void open(ServerLevel server) {
        setState(State.OPEN);
        server.playSound(null, blockPosition(), SoundEvents.PISTON_EXTEND, SoundSource.HOSTILE, 2f, 0.5f);
        server.playSound(null, blockPosition(), SoundEvents.IRON_DOOR_OPEN, SoundSource.HOSTILE, 2f, 0.4f);
    }

    private void unload(ServerLevel server) {
        for (int i = 0; i < TROOPS; i++) {
            CultistEntity trooper = WarpboundEntities.CULTIST.create(server);
            if (trooper == null) continue;
            double a = Math.PI * 2 * i / TROOPS;
            trooper.moveTo(getX() + Math.cos(a) * 2.2, getY(), getZ() + Math.sin(a) * 2.2, (float) Math.toDegrees(a) - 90, 0);
            trooper.finalizeSpawn(server, server.getCurrentDifficultyAt(trooper.blockPosition()), MobSpawnType.EVENT, null);
            Player near = server.getNearestPlayer(this, 32);
            if (near != null && !near.isCreative() && !near.isSpectator()) trooper.setTarget(near);
            server.addFreshEntity(trooper);
        }
        server.playSound(null, blockPosition(), SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 1.2f, 1.4f);
    }

    private void flightTrail() {
        double top = getY() + getBbHeight();
        for (int i = 0; i < 4; i++) {
            level().addParticle(ParticleTypes.FLAME, getX() + (random.nextDouble() - 0.5), top, getZ() + (random.nextDouble() - 0.5),
                    0, 0.1, 0);
            level().addParticle(ParticleTypes.LARGE_SMOKE, getX() + (random.nextDouble() - 0.5) * 1.5, top + 0.5,
                    getZ() + (random.nextDouble() - 0.5) * 1.5, 0, 0.05, 0);
        }
    }

    @Override
    public boolean isPickable() {
        return !isRemoved();
    }

    @Override
    public boolean canBeCollidedWith() {
        return state() != State.FLYING;
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        // остов не разрушить оружием; творческий режим убирает его ударом
        if (source.getEntity() instanceof Player player && player.isCreative() && !level().isClientSide) {
            discard();
            return true;
        }
        return false;
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, WarpAnim.MAIN, 0, state ->
                state.setAndContinue(state() == State.OPEN ? WarpAnim.DEPLOY : WarpAnim.IDLE)));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        entityData.set(STATE, tag.getInt("State"));
        stateTicks = tag.getInt("StateTicks");
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        tag.putInt("State", entityData.get(STATE));
        tag.putInt("StateTicks", stateTicks);
    }
}
