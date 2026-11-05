package dev.warpbound.entity.astartes;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.animation.AnimationController;
import software.bernie.geckolib.animation.PlayState;
import software.bernie.geckolib.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

/** Двуногий в силовой броне: бродит, смотрит на игрока, отвечает ударом на удар. Каркас для Астартес и Громового воина; ноги идут в такт настоящей скорости. */
public class BipedConceptEntity extends PathfinderMob implements GeoEntity {
    private static final RawAnimation IDLE = RawAnimation.begin().thenLoop("misc.idle");
    private static final RawAnimation WALK = RawAnimation.begin().thenLoop("move.walk");
    private static final RawAnimation RUN = RawAnimation.begin().thenLoop("move.run");
    private static final RawAnimation DEATH = RawAnimation.begin().thenPlayAndHold("misc.death");
    private static final RawAnimation MELEE = RawAnimation.begin().thenPlay("attack.melee");
    private static final RawAnimation HURT = RawAnimation.begin().thenPlay("misc.hurt");
    /** Сколько тиков лежит после падения. Клип смерти 2,7 с. */
    private static final int CORPSE_TICKS = 100;
    private static final EntityDataAccessor<String> CLIP = SynchedEntityData.defineId(BipedConceptEntity.class, EntityDataSerializers.STRING);

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private final AstartesConcepts.Variant variant;

    public BipedConceptEntity(EntityType<? extends BipedConceptEntity> type, Level level, AstartesConcepts.Variant variant) {
        super(type, level);
        this.variant = variant;
        setPersistenceRequired();
    }

    public static AttributeSupplier.Builder attributes(AstartesConcepts.Variant v) {
        return PathfinderMob.createMobAttributes().add(Attributes.MAX_HEALTH, v.maxHealth()).add(Attributes.ARMOR, v.armor()).add(Attributes.ATTACK_DAMAGE, v.damage())
                .add(Attributes.MOVEMENT_SPEED, 0.2).add(Attributes.KNOCKBACK_RESISTANCE, 0.6).add(Attributes.FOLLOW_RANGE, 32);
    }

    public AstartesConcepts.Variant variant() {
        return variant;
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(CLIP, "");
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.9, true));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12f));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        if (!entityData.get(CLIP).isEmpty()) tag.putString("Clip", entityData.get(CLIP));
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.contains("Clip")) entityData.set(CLIP, tag.getString("Clip"));
    }

    @Override
    public boolean doHurtTarget(Entity target) {
        triggerAnim("action", "melee");
        return super.doHurtTarget(target);
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        boolean hurt = super.hurt(source, amount);
        if (hurt && !level().isClientSide && isAlive()) triggerAnim("flinch", "hurt");
        return hurt;
    }

    /** Лежит, пока идёт падение и ещё немного: ванильное исчезновение на 20-м тике оборвало бы анимацию. */
    @Override
    protected void tickDeath() {
        deathTime++;
        if (deathTime >= CORPSE_TICKS && !level().isClientSide) remove(RemovalReason.KILLED);
    }

    /** Тяжёлый стук брони вместо обычных шагов. Настоящие звуки подключим вместе с движениями игрока. */
    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.IRON_GOLEM_STEP, 0.3f, 1.3f + random.nextFloat() * 0.15f);
    }

    /** Скорость по настоящему смещению, блоков в секунду. */
    private double horizontalSpeed() {
        double dx = getX() - xo, dz = getZ() - zo;
        return Math.sqrt(dx * dx + dz * dz) * 20;
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "move", 5, state -> {
            state.getController().setAnimationSpeed(1);
            if (isDeadOrDying()) return state.setAndContinue(DEATH);
            String clip = entityData.get(CLIP);
            if (!clip.isEmpty()) return state.setAndContinue(RawAnimation.begin().thenLoop(clip));
            double speed = horizontalSpeed();
            double between = (variant.walkSpeed() + variant.runSpeed()) / 2;
            if (speed > between) {
                state.getController().setAnimationSpeed(Math.min(1.5, Math.max(0.6, speed / variant.runSpeed())));
                return state.setAndContinue(RUN);
            }
            if (speed > 0.12) {
                state.getController().setAnimationSpeed(Math.min(2.0, Math.max(0.5, speed / variant.walkSpeed())));
                return state.setAndContinue(WALK);
            }
            return state.setAndContinue(IDLE);
        }));
        controllers.add(new AnimationController<>(this, "action", 3, state -> PlayState.STOP).triggerableAnim("melee", MELEE));
        controllers.add(new AnimationController<>(this, "flinch", 2, state -> PlayState.STOP).triggerableAnim("hurt", HURT));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
