package dev.warpbound.entity.cult;

import dev.warpbound.entity.anim.WarpAnim;
import dev.warpbound.entity.projectile.WarpBoltEntity;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
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
import net.minecraft.world.level.ServerLevelAccessor;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * Культист (М8): рядовой враг собора Кинериса. Три варианта на одной модели —
 * нож (ближний бой), автоган (очереди), стаббер (тяжёлые выстрелы). Раненый культист бежит.
 */
public class CultistEntity extends Monster implements RangedAttackMob, GeoEntity {
    public enum Variant {
        KNIFE, AUTOGUN, STUBBER
    }

    private static final EntityDataAccessor<Integer> VARIANT =
            SynchedEntityData.defineId(CultistEntity.class, EntityDataSerializers.INT);

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);

    public CultistEntity(EntityType<? extends CultistEntity> type, Level level) {
        super(type, level);
        xpReward = 6;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 20)
                .add(Attributes.ATTACK_DAMAGE, 4)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.FOLLOW_RANGE, 28);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(VARIANT, 0);
    }

    public Variant variant() {
        return Variant.values()[Math.floorMod(entityData.get(VARIANT), Variant.values().length)];
    }

    public void setVariant(Variant variant) {
        entityData.set(VARIANT, variant.ordinal());
    }

    private boolean ranged() {
        return variant() != Variant.KNIFE;
    }

    private boolean broken() {
        return getHealth() < getMaxHealth() * 0.3f;
    }

    @Override
    protected void registerGoals() {
        // цели выбираются по варианту, а он известен только после спавна — поэтому проверки в canUse
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new AvoidEntityGoal<>(this, Player.class, 12f, 1.0, 1.3) {
            @Override
            public boolean canUse() {
                return broken() && super.canUse();
            }
        });
        goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.2, false) {
            @Override
            public boolean canUse() {
                return !ranged() && super.canUse();
            }
        });
        goalSelector.addGoal(2, new RangedAttackGoal(this, 1.0, 20, 40, 16f) {
            @Override
            public boolean canUse() {
                return ranged() && super.canUse();
            }
        });
        goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8f));
        goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, MobSpawnType reason,
                                        @Nullable SpawnGroupData data) {
        setVariant(Variant.values()[random.nextInt(Variant.values().length)]);
        return super.finalizeSpawn(level, difficulty, reason, data);
    }

    @Override
    public boolean doHurtTarget(Entity target) {
        triggerAnim(WarpAnim.ACTION, WarpAnim.SWING);
        return super.doHurtTarget(target);
    }

    @Override
    public void performRangedAttack(LivingEntity target, float power) {
        triggerAnim(WarpAnim.ACTION, WarpAnim.SHOOT);
        boolean stubber = variant() == Variant.STUBBER;
        WarpBoltEntity.fire(this, target, WarpBoltEntity.Kind.BULLET, stubber ? 6 : 3, 2.2f, stubber ? 4f : 7f);
        playSound(SoundEvents.CROSSBOW_SHOOT, 0.8f, stubber ? 0.6f : 1.3f);
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(WarpAnim.locomotion(this, true));
        controllers.add(WarpAnim.actions(this, WarpAnim.SWING, WarpAnim.SHOOT));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("Variant", entityData.get(VARIANT));
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        entityData.set(VARIANT, tag.getInt("Variant"));
    }
}
