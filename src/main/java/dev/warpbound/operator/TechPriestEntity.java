package dev.warpbound.operator;

import dev.warpbound.entity.anim.WarpAnim;
import dev.warpbound.faction.Faction;
import dev.warpbound.core.WarpboundSounds;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.nbt.CompoundTag;
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
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.Optional;
import java.util.UUID;

/**
 * Техножрец Механикус или тёмный техножрец. Пока это первый оператор главы 1:
 * техножрец выходит из капсулы челнока, тёмный — поднимается из варп-пламени; бродит у маяка и ждёт Кузню (этап 3).
 * Смертен, как решили в обсуждении.
 */
public class TechPriestEntity extends PathfinderMob implements GeoEntity {
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private final Faction faction;
    private UUID owner;
    private static final int EMERGE_TICKS = 50;
    private static final double EMERGE_DEPTH = 3.2;
    /** Тиков до конца подъёма из-под земли (тёмный техножрец в ритуале). */
    private int emerging;
    private int steps;

    public TechPriestEntity(EntityType<? extends TechPriestEntity> type, Level level, Faction faction) {
        super(type, level);
        this.faction = faction;
        setPersistenceRequired();
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PathfinderMob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 30)
                .add(Attributes.ARMOR, 4)
                .add(Attributes.MOVEMENT_SPEED, 0.22);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.6));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 8f));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
    }

    public Faction faction() {
        return faction;
    }

    public Optional<UUID> owner() {
        return Optional.ofNullable(owner);
    }

    void setOwner(UUID owner) {
        this.owner = owner;
    }

    /** Ступил на землю (вышел из капсулы или из пламени): благословляет место и закрывает главу у владельца. */
    public void arrive(UUID owner) {
        if (owner != null) this.owner = owner;
        triggerAnim(WarpAnim.ACTION, WarpAnim.INTERACT);
        OperatorArrival.landed(this);
    }

    /** Подняться из-под земли сквозь варп-пламя: ставится на точку ритуала и начинает снизу. */
    public void startEmerging() {
        emerging = EMERGE_TICKS;
        noPhysics = true;
        setNoGravity(true);
        setNoAi(true);
        setPos(getX(), getY() - EMERGE_DEPTH, getZ());
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (emerging <= 0 || !(level() instanceof ServerLevel server)) return;
        emerging--;
        // сначала быстро, у поверхности замедляется
        double k = (double) emerging / EMERGE_TICKS;
        double step = EMERGE_DEPTH * 2 * (k + 0.5 / EMERGE_TICKS) / EMERGE_TICKS;
        setPos(getX(), getY() + step, getZ());
        if (tickCount % 2 == 0) {
            server.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, getX(), getY() + EMERGE_DEPTH * k + 0.1, getZ(), 6, 0.9, 0.05, 0.9, 0.03);
            server.sendParticles(ParticleTypes.SMOKE, getX(), getY() + EMERGE_DEPTH * k + 0.1, getZ(), 3, 0.8, 0.05, 0.8, 0.01);
        }
        if (emerging == 0) {
            setPos(getX(), Math.round(getY() * 16) / 16.0, getZ());
            noPhysics = false;
            setNoGravity(false);
            setNoAi(false);
        }
    }

    // ------------------------------------------------------------------ звуки: металл, сервоприводы, у тёмного — плоть

    private boolean dark() {
        return faction == Faction.CHAOS;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        steps++;
        playSound(dark() ? WarpboundSounds.DARK_PRIEST_STEP : WarpboundSounds.PRIEST_STEP, dark() ? 0.9f : 0.5f, 0.9f + random.nextFloat() * 0.2f);
        if (dark() && random.nextInt(2) == 0) playSound(WarpboundSounds.DARK_PRIEST_FLESH, 0.6f, 0.8f + random.nextFloat() * 0.3f);
        if (steps % 3 == 0) playSound(dark() ? WarpboundSounds.DARK_PRIEST_SERVO : WarpboundSounds.PRIEST_SERVO, 0.35f, 0.9f + random.nextFloat() * 0.3f);
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return dark() ? WarpboundSounds.DARK_PRIEST_AMBIENT : WarpboundSounds.PRIEST_AMBIENT;
    }

    @Override
    public int getAmbientSoundInterval() {
        return 160;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return dark() ? WarpboundSounds.DARK_PRIEST_HURT : WarpboundSounds.PRIEST_HURT;
    }

    @Override
    public void tick() {
        super.tick();
        // стоя сервоплечо и дендриты то и дело оживают — тихий скрип приводов
        if (!level().isClientSide && emerging <= 0 && random.nextInt(140) == 0) {
            playSound(dark() ? WarpboundSounds.DARK_PRIEST_SERVO : WarpboundSounds.PRIEST_SERVO, 0.3f, 0.8f + random.nextFloat() * 0.5f);
        }
    }

    @Override
    public boolean isInvulnerable() {
        return emerging > 0 || super.isInvulnerable();
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(WarpAnim.locomotion(this, false));
        controllers.add(WarpAnim.actions(this, WarpAnim.INTERACT));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        if (owner != null) tag.putUUID("Owner", owner);
        tag.putInt("Emerging", emerging);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.hasUUID("Owner")) owner = tag.getUUID("Owner");
        emerging = tag.getInt("Emerging");
    }
}
