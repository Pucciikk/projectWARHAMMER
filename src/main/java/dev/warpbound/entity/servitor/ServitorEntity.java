package dev.warpbound.entity.servitor;

import dev.warpbound.entity.anim.WarpAnim;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.animation.AnimationController;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * Сервитор-ремонтник (М3). Пока заглушка: бродит, умеет «чинить» (сварка с искрами) и «выключаться».
 * Варп-события пошлют его к пробитым узлам Поля Геллера и утечкам — тогда у него появятся цели.
 * Для проверки: {@code /data merge entity @e[type=warpbound:servitor,limit=1] {Working:1b}} или {@code {Dormant:1b}}.
 */
public class ServitorEntity extends PathfinderMob implements GeoEntity {
    private static final EntityDataAccessor<Boolean> WORKING =
            SynchedEntityData.defineId(ServitorEntity.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> DORMANT =
            SynchedEntityData.defineId(ServitorEntity.class, EntityDataSerializers.BOOLEAN);

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);

    public ServitorEntity(EntityType<? extends ServitorEntity> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PathfinderMob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 24)
                .add(Attributes.ARMOR, 6)
                .add(Attributes.MOVEMENT_SPEED, 0.18);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(WORKING, false);
        builder.define(DORMANT, false);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.7) {
            @Override
            public boolean canUse() {
                return isFree() && super.canUse();
            }
        });
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 6f) {
            @Override
            public boolean canUse() {
                return !isDormant() && super.canUse();
            }
        });
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
    }

    public boolean isWorking() {
        return entityData.get(WORKING);
    }

    public boolean isDormant() {
        return entityData.get(DORMANT);
    }

    public void setWorking(boolean working) {
        entityData.set(WORKING, working);
    }

    public void setDormant(boolean dormant) {
        entityData.set(DORMANT, dormant);
    }

    private boolean isFree() {
        return !isWorking() && !isDormant();
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!isFree()) getNavigation().stop();
        if (isWorking() && tickCount % 3 == 0 && level() instanceof ServerLevel server) {
            // искры у сварочного аппарата: правая рука, чуть впереди
            Vec3 hand = position().add(Vec3.directionFromRotation(0, yBodyRot).scale(0.7))
                    .add(Vec3.directionFromRotation(0, yBodyRot - 90).scale(0.35)).add(0, 0.9, 0);
            server.sendParticles(ParticleTypes.ELECTRIC_SPARK, hand.x, hand.y, hand.z, 3, 0.08, 0.08, 0.08, 0.15);
            if (random.nextInt(4) == 0) {
                server.sendParticles(ParticleTypes.SMALL_FLAME, hand.x, hand.y, hand.z, 1, 0.02, 0.02, 0.02, 0.01);
            }
        }
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, WarpAnim.MAIN, 6, state -> {
            if (isDormant()) return state.setAndContinue(WarpAnim.REST);
            if (isWorking()) return state.setAndContinue(WarpAnim.REPAIR);
            return state.setAndContinue(state.isMoving() ? WarpAnim.WALK : WarpAnim.IDLE);
        }));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putBoolean("Working", isWorking());
        tag.putBoolean("Dormant", isDormant());
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        setWorking(tag.getBoolean("Working"));
        setDormant(tag.getBoolean("Dormant"));
    }
}
