package dev.warpbound.entity.daemon;

import dev.warpbound.entity.WarpboundEntities;
import dev.warpbound.entity.anim.WarpAnim;
import dev.warpbound.entity.projectile.WarpBoltEntity;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
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
 * Ужасы Тзинча (М5). Розовый — колдун: бросает варп-пламя, а погибая, распадается на двух синих.
 * Синий — та же модель меньше, злее и быстрее, бьёт чаще и слабее.
 */
public class HorrorEntity extends Monster implements RangedAttackMob, GeoEntity {
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);

    public HorrorEntity(EntityType<? extends HorrorEntity> type, Level level) {
        super(type, level);
        xpReward = isPink() ? 10 : 4;
    }

    /** По типу, а не по полю: registerGoals вызывается из конструктора Mob раньше, чем заполнились бы поля. */
    public boolean isPink() {
        return getType() == WarpboundEntities.PINK_HORROR;
    }

    public static AttributeSupplier.Builder createPinkAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 26)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.FOLLOW_RANGE, 28);
    }

    public static AttributeSupplier.Builder createBlueAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 12)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 28);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        boolean pink = isPink();
        goalSelector.addGoal(2, pink ? new RangedAttackGoal(this, 1.0, 40, 14f) : new RangedAttackGoal(this, 1.15, 25, 10f));
        goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 10f));
        goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public void performRangedAttack(LivingEntity target, float power) {
        boolean pink = isPink();
        triggerAnim(WarpAnim.ACTION, WarpAnim.CAST);
        WarpBoltEntity.fire(this, target, pink ? WarpBoltEntity.Kind.PINK_FIRE : WarpBoltEntity.Kind.BLUE_FIRE,
                pink ? 6 : 3, 1.1f, pink ? 3f : 6f);
        playSound(SoundEvents.BLAZE_SHOOT, 0.6f, pink ? 1.4f : 1.8f);
    }

    @Override
    public void die(DamageSource source) {
        if (isPink() && level() instanceof ServerLevel server && !isRemoved()) split(server);
        super.die(source);
    }

    /** Розовый ужас лопается на двух синих — с хохотом и вспышкой варп-пламени. */
    private void split(ServerLevel server) {
        server.sendParticles(ParticleTypes.WITCH, getX(), getY(0.5), getZ(), 30, 0.4, 0.5, 0.4, 0.1);
        server.playSound(null, blockPosition(), SoundEvents.EVOKER_CAST_SPELL, getSoundSource(), 1f, 1.6f);
        for (int i = 0; i < 2; i++) {
            HorrorEntity blue = WarpboundEntities.BLUE_HORROR.create(server);
            if (blue == null) continue;
            double side = i == 0 ? -0.5 : 0.5;
            blue.moveTo(getX() + side, getY(), getZ() + side * 0.6, getYRot(), 0);
            if (getTarget() != null) blue.setTarget(getTarget());
            server.addFreshEntity(blue);
        }
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(WarpAnim.locomotion(this, false));
        controllers.add(WarpAnim.actions(this, WarpAnim.CAST));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
