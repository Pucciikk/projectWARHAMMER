package dev.warpbound.entity.cult;

import dev.warpbound.entity.WarpboundEntities;
import dev.warpbound.entity.anim.WarpAnim;
import dev.warpbound.entity.projectile.WarpBoltEntity;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RangedAttackGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.RangedAttackMob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * Одержимый жрец культа (М9), босс финала Сезона 1 в соборе варп-шрама.
 * Фаза 1 — человек: мечет ересь из посоха и зовёт культистов. На половине здоровья демон
 * рвёт его изнутри (3 секунды неуязвимости, модель растёт с 1.9 до 3 блоков), фаза 2 — когти и натиск.
 */
public class PossessedPriestEntity extends Monster implements RangedAttackMob, GeoEntity {
    public static final int TRANSFORM_TICKS = 60;
    /** Во сколько раз демон больше жреца (3.0 / 1.9 блока). */
    public static final float DAEMON_SCALE = 1.58f;

    private static final EntityDataAccessor<Boolean> DAEMON =
            SynchedEntityData.defineId(PossessedPriestEntity.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Integer> TRANSFORM =
            SynchedEntityData.defineId(PossessedPriestEntity.class, EntityDataSerializers.INT);
    private static final int SUMMON_INTERVAL = 20 * 15;

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private final ServerBossEvent bossBar = new ServerBossEvent(getDisplayName(), BossEvent.BossBarColor.PURPLE,
            BossEvent.BossBarOverlay.NOTCHED_10);
    private int summonCooldown = SUMMON_INTERVAL / 2;

    public PossessedPriestEntity(EntityType<? extends PossessedPriestEntity> type, Level level) {
        super(type, level);
        xpReward = 100;
        setPersistenceRequired();
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 200)
                .add(Attributes.ARMOR, 6)
                .add(Attributes.ATTACK_DAMAGE, 14)
                .add(Attributes.MOVEMENT_SPEED, 0.23)
                .add(Attributes.FOLLOW_RANGE, 40)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.8);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DAEMON, false);
        builder.define(TRANSFORM, 0);
    }

    public boolean isDaemon() {
        return entityData.get(DAEMON);
    }

    /** Сколько тиков превращения осталось (0 — не превращается). */
    public int transformTicks() {
        return entityData.get(TRANSFORM);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new RangedAttackGoal(this, 0.9, 30, 50, 18f) {
            @Override
            public boolean canUse() {
                return !isDaemon() && super.canUse();
            }
        });
        goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.3, true) {
            @Override
            public boolean canUse() {
                return isDaemon() && transformTicks() == 0 && super.canUse();
            }

            @Override
            public boolean canContinueToUse() {
                return transformTicks() == 0 && super.canContinueToUse();
            }
        });
        goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.7));
        goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 12f));
        goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, false));
    }

    @Override
    public void performRangedAttack(LivingEntity target, float power) {
        triggerAnim(WarpAnim.ACTION, WarpAnim.CAST);
        WarpBoltEntity.fire(this, target, WarpBoltEntity.Kind.HERESY, 7, 1.3f, 2f);
        playSound(SoundEvents.EVOKER_CAST_SPELL, 1f, 0.7f);
    }

    @Override
    public boolean doHurtTarget(Entity target) {
        triggerAnim(WarpAnim.ACTION, WarpAnim.SWING);
        return super.doHurtTarget(target);
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        if (transformTicks() > 0 && !source.is(net.minecraft.tags.DamageTypeTags.BYPASSES_INVULNERABILITY)) return false;
        boolean hurt = super.hurt(source, amount);
        if (hurt && !isDaemon() && getHealth() <= getMaxHealth() / 2 && level() instanceof ServerLevel server) {
            startTransform(server);
        }
        return hurt;
    }

    private void startTransform(ServerLevel server) {
        entityData.set(DAEMON, true);
        entityData.set(TRANSFORM, TRANSFORM_TICKS);
        getNavigation().stop();
        triggerAnim(WarpAnim.ACTION, WarpAnim.TRANSFORM);
        server.playSound(null, blockPosition(), SoundEvents.WITHER_SPAWN, getSoundSource(), 1.2f, 0.7f);
        bossBar.setColor(BossEvent.BossBarColor.RED);
    }

    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();
        bossBar.setProgress(getHealth() / getMaxHealth());
        ServerLevel server = (ServerLevel) level();

        int transform = transformTicks();
        if (transform > 0) {
            entityData.set(TRANSFORM, transform - 1);
            server.sendParticles(ParticleTypes.WITCH, getX(), getY(0.6), getZ(), 6, 0.5, 0.8, 0.5, 0.05);
            if (transform % 10 == 0) server.sendParticles(ParticleTypes.CRIMSON_SPORE, getX(), getY(0.5), getZ(), 20, 0.6, 1, 0.6, 0);
            if (transform == 1) {
                // демон вырвался: выше, быстрее, сильнее
                refreshDimensions();
                getAttribute(Attributes.MOVEMENT_SPEED).setBaseValue(0.32);
                server.playSound(null, blockPosition(), SoundEvents.RAVAGER_ROAR, getSoundSource(), 1.5f, 0.6f);
                server.sendParticles(ParticleTypes.EXPLOSION, getX(), getY(0.5), getZ(), 3, 0.6, 0.8, 0.6, 0);
            }
            return;
        }

        if (!isDaemon() && getTarget() != null && --summonCooldown <= 0) {
            summonCooldown = SUMMON_INTERVAL;
            summonCultists(server);
        }
    }

    /** Жрец зовёт паству: двое культистов выходят из варп-вспышки рядом. */
    private void summonCultists(ServerLevel server) {
        triggerAnim(WarpAnim.ACTION, WarpAnim.CAST);
        server.playSound(null, blockPosition(), SoundEvents.EVOKER_PREPARE_SUMMON, getSoundSource(), 1f, 0.8f);
        for (int i = 0; i < 2; i++) {
            CultistEntity cultist = WarpboundEntities.CULTIST.create(server);
            if (cultist == null) continue;
            double a = random.nextDouble() * Math.PI * 2;
            cultist.moveTo(getX() + Math.cos(a) * 3, getY(), getZ() + Math.sin(a) * 3, random.nextFloat() * 360, 0);
            cultist.finalizeSpawn(server, server.getCurrentDifficultyAt(cultist.blockPosition()), MobSpawnType.MOB_SUMMONED, null);
            cultist.setTarget(getTarget());
            server.addFreshEntity(cultist);
            server.sendParticles(ParticleTypes.PORTAL, cultist.getX(), cultist.getY(0.5), cultist.getZ(), 40, 0.3, 0.8, 0.3, 0.4);
        }
    }

    @Override
    public EntityDimensions getDefaultDimensions(Pose pose) {
        EntityDimensions base = super.getDefaultDimensions(pose);
        return isDaemon() && transformTicks() == 0 ? base.scale(DAEMON_SCALE * 0.95f, DAEMON_SCALE) : base;
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (DAEMON.equals(key) || TRANSFORM.equals(key)) refreshDimensions();
    }

    @Override
    public void startSeenByPlayer(ServerPlayer player) {
        super.startSeenByPlayer(player);
        bossBar.addPlayer(player);
    }

    @Override
    public void stopSeenByPlayer(ServerPlayer player) {
        super.stopSeenByPlayer(player);
        bossBar.removePlayer(player);
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(WarpAnim.locomotion(this, true));
        controllers.add(WarpAnim.actions(this, WarpAnim.CAST, WarpAnim.SWING, WarpAnim.TRANSFORM));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putBoolean("Daemon", isDaemon());
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        entityData.set(DAEMON, tag.getBoolean("Daemon"));
        if (isDaemon()) getAttribute(Attributes.MOVEMENT_SPEED).setBaseValue(0.32);
        if (hasCustomName()) bossBar.setName(getDisplayName());
    }
}
