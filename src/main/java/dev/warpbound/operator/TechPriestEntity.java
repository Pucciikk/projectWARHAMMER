package dev.warpbound.operator;

import dev.warpbound.faction.Faction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffects;
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

import java.util.Optional;
import java.util.UUID;

/**
 * Техножрец Механикус или тёмный техножрец. Пока это первый оператор главы 1:
 * он прибывает, бродит у маяка и ждёт Кузню (этап 3). Смертен, как решили в обсуждении.
 */
public class TechPriestEntity extends PathfinderMob {
    private final Faction faction;
    private UUID owner;
    /** Летит вниз после высадки с челнока: дымит, пока не коснётся земли. */
    private boolean descending;

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

    void startDescent() {
        descending = true;
        addEffect(new net.minecraft.world.effect.MobEffectInstance(MobEffects.SLOW_FALLING, 20 * 60, 0, false, false));
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!descending || !(level() instanceof ServerLevel server)) return;
        if (onGround()) {
            descending = false;
            removeEffect(MobEffects.SLOW_FALLING);
            server.playSound(null, blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.NEUTRAL, 0.5f, 1.6f);
            server.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, getX(), getY() + 0.2, getZ(), 25, 1.2, 0.2, 1.2, 0.02);
            OperatorArrival.landed(this);
        } else if (tickCount % 2 == 0) {
            server.sendParticles(ParticleTypes.FLAME, getX(), getY() - 0.3, getZ(), 4, 0.25, 0.1, 0.25, 0.01);
            server.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() - 0.6, getZ(), 2, 0.3, 0.2, 0.3, 0.01);
        }
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        if (owner != null) tag.putUUID("Owner", owner);
        tag.putBoolean("Descending", descending);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.hasUUID("Owner")) owner = tag.getUUID("Owner");
        descending = tag.getBoolean("Descending");
    }
}
