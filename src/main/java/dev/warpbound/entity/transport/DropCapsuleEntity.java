package dev.warpbound.entity.transport;

import dev.warpbound.core.WarpboundSounds;
import dev.warpbound.entity.WarpboundEntities;
import dev.warpbound.entity.anim.WarpAnim;
import dev.warpbound.operator.TechPriestEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.animation.AnimationController;
import software.bernie.geckolib.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.UUID;

/**
 * Десантная капсула челнока: опускается на тормозных соплах, раскрывает двери, выпускает груз
 * (техножреца или другого лоялиста) и через полминуты улетает обратно на орбиту.
 * Как и у челнока, высоту по времени считают обе стороны — движение без рывков.
 */
public class DropCapsuleEntity extends Entity implements GeoEntity {
    public enum Phase {
        FALL, LANDED, OPEN, LAUNCH
    }

    private static final EntityDataAccessor<Integer> PHASE = SynchedEntityData.defineId(DropCapsuleEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> PHASE_START = SynchedEntityData.defineId(DropCapsuleEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Float> FROM_Y = SynchedEntityData.defineId(DropCapsuleEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Float> GROUND_Y = SynchedEntityData.defineId(DropCapsuleEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Float> YAW = SynchedEntityData.defineId(DropCapsuleEntity.class, EntityDataSerializers.FLOAT);

    private static final int SETTLE_TICKS = 20, UNLOAD_AT = 22, STAY_TICKS = 20 * 30, LAUNCH_TICKS = 90;
    private static final double LAUNCH_HEIGHT = 70;

    private static final RawAnimation IDLE = RawAnimation.begin().thenLoop("misc.idle");
    private static final RawAnimation FLY = RawAnimation.begin().thenLoop("move.fly");

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private ResourceLocation payload;
    private UUID owner;

    public DropCapsuleEntity(EntityType<? extends DropCapsuleEntity> type, Level level) {
        super(type, level);
        noPhysics = true;
        setNoGravity(true);
    }

    static void release(ServerLevel level, Vec3 from, double ground, float yaw, ResourceLocation payload, UUID owner) {
        DropCapsuleEntity capsule = WarpboundEntities.DROP_CAPSULE.create(level);
        if (capsule == null) return;
        capsule.payload = payload;
        capsule.owner = owner;
        capsule.moveTo(from.x, from.y, from.z, yaw, 0);
        capsule.entityData.set(FROM_Y, (float) from.y);
        capsule.entityData.set(GROUND_Y, (float) ground);
        capsule.entityData.set(YAW, yaw);
        capsule.setPhase(Phase.FALL);
        level.addFreshEntity(capsule);
    }

    public Phase phase() {
        return Phase.values()[Math.floorMod(entityData.get(PHASE), Phase.values().length)];
    }

    private void setPhase(Phase phase) {
        entityData.set(PHASE, phase.ordinal());
        entityData.set(PHASE_START, (int) level().getGameTime());
    }

    private int phaseTicks() {
        return (int) level().getGameTime() - entityData.get(PHASE_START);
    }

    /** Время спуска: из-под стоящего челнока — мгновение, с зависшего — плавно на соплах. */
    private int fallTicks() {
        double h = entityData.get(FROM_Y) - entityData.get(GROUND_Y);
        return h < 0.6 ? 12 : Math.min(90, 24 + (int) (h * 6));
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        builder.define(PHASE, Phase.FALL.ordinal());
        builder.define(PHASE_START, 0);
        builder.define(FROM_Y, 0f);
        builder.define(GROUND_Y, 0f);
        builder.define(YAW, 0f);
    }

    @Override
    public void tick() {
        super.tick();
        if (!level().isClientSide && entityData.get(FROM_Y) == 0 && entityData.get(GROUND_Y) == 0) {
            // поставлена командой /summon: спускается с места на землю под собой
            entityData.set(FROM_Y, (float) getY());
            entityData.set(GROUND_Y, (float) level().getHeight(Heightmap.Types.MOTION_BLOCKING, getBlockX(), getBlockZ()));
            setPhase(Phase.FALL);
        }
        int t = phaseTicks();
        double ground = entityData.get(GROUND_Y);
        double y = switch (phase()) {
            case FALL -> {
                double s = Mth.clamp((double) t / fallTicks(), 0, 1);
                yield entityData.get(FROM_Y) - (entityData.get(FROM_Y) - ground) * (1 - (1 - s) * (1 - s));
            }
            case LAUNCH -> ground + LAUNCH_HEIGHT * Math.pow(Mth.clamp((double) t / LAUNCH_TICKS, 0, 1), 2.2);
            default -> ground;
        };
        setPos(getX(), y, getZ());
        setYRot(entityData.get(YAW));

        if (level().isClientSide) {
            clientFx(t);
            return;
        }
        ServerLevel server = (ServerLevel) level();
        switch (phase()) {
            case FALL -> {
                if (t % 12 == 0 && fallTicks() > 12) server.playSound(null, blockPosition(), WarpboundSounds.CAPSULE_THRUST, SoundSource.NEUTRAL, 1.5f, 0.9f);
                if (t >= fallTicks()) {
                    setPhase(Phase.LANDED);
                    server.playSound(null, blockPosition(), WarpboundSounds.SHUTTLE_TOUCHDOWN, SoundSource.NEUTRAL, 1.5f, 1.3f);
                    server.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, getX(), getY() + 0.2, getZ(), 14, 0.9, 0.1, 0.9, 0.02);
                }
            }
            case LANDED -> {
                if (t >= SETTLE_TICKS) {
                    setPhase(Phase.OPEN);
                    server.playSound(null, blockPosition(), WarpboundSounds.CAPSULE_OPEN, SoundSource.NEUTRAL, 1.5f, 0.8f);
                }
            }
            case OPEN -> {
                if (t == UNLOAD_AT) unload(server);
                if (t >= STAY_TICKS) {
                    setPhase(Phase.LAUNCH);
                    server.playSound(null, blockPosition(), WarpboundSounds.CAPSULE_THRUST, SoundSource.NEUTRAL, 2f, 0.7f);
                }
            }
            case LAUNCH -> {
                if (t >= LAUNCH_TICKS) discard();
            }
        }
    }

    private void unload(ServerLevel server) {
        if (payload == null) return;
        EntityType<?> type = BuiltInRegistries.ENTITY_TYPE.get(payload);
        Entity passenger = type.create(server);
        if (passenger == null) return;
        float yaw = entityData.get(YAW);
        Vec3 f = new Vec3(-Mth.sin(yaw * Mth.DEG_TO_RAD), 0, Mth.cos(yaw * Mth.DEG_TO_RAD));
        passenger.moveTo(getX() + f.x * 0.3, getY() + 0.25, getZ() + f.z * 0.3, yaw, 0);
        if (passenger instanceof Mob mob) {
            mob.finalizeSpawn(server, server.getCurrentDifficultyAt(BlockPos.containing(position())), MobSpawnType.EVENT, null);
            mob.setYHeadRot(yaw);
            mob.setYBodyRot(yaw);
        }
        server.addFreshEntity(passenger);
        if (passenger instanceof Mob mob) {
            Vec3 out = position().add(f.scale(3.5));
            mob.getNavigation().moveTo(out.x, out.y, out.z, 0.7);
        }
        if (passenger instanceof TechPriestEntity priest) priest.arrive(owner);
        server.sendParticles(ParticleTypes.CLOUD, getX() + f.x, getY() + 1, getZ() + f.z, 12, 0.4, 0.6, 0.4, 0.02);
    }

    private void clientFx(int t) {
        Phase p = phase();
        boolean thrust = p == Phase.FALL && fallTicks() > 12 || p == Phase.LAUNCH;
        if (thrust) {
            for (int i = 0; i < 4; i++) {
                double a = Math.PI / 4 + i * Math.PI / 2;
                double x = getX() + Math.cos(a) * 0.95, z = getZ() + Math.sin(a) * 0.95;
                level().addParticle(ParticleTypes.FLAME, x, getY() - 0.1, z, 0, -0.3, 0);
                if (random.nextInt(3) == 0) level().addParticle(ParticleTypes.SMOKE, x, getY() - 0.4, z, 0, -0.1, 0);
            }
        }
        if (p == Phase.OPEN && t < 40 && random.nextInt(2) == 0) {
            // пар из раскрытого нутра
            float yaw = entityData.get(YAW) * Mth.DEG_TO_RAD;
            level().addParticle(ParticleTypes.CLOUD, getX() - Mth.sin(yaw) * 0.9, getY() + 0.6 + random.nextDouble() * 1.6,
                    getZ() + Mth.cos(yaw) * 0.9, -Mth.sin(yaw) * 0.04, 0.02, Mth.cos(yaw) * 0.04);
        }
    }

    @Override
    public void lerpTo(double x, double y, double z, float yRot, float xRot, int steps) {
    }

    @Override
    public boolean isPickable() {
        return false;
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        return false;
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, WarpAnim.MAIN, 6, state -> switch (phase()) {
            case OPEN -> state.setAndContinue(WarpAnim.DEPLOY);
            case LAUNCH -> state.setAndContinue(FLY);
            case FALL -> state.setAndContinue(fallTicks() > 12 ? FLY : IDLE);
            default -> state.setAndContinue(IDLE);
        }));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        entityData.set(PHASE, tag.getInt("Phase"));
        entityData.set(PHASE_START, (int) level().getGameTime() - tag.getInt("PhaseTicks"));
        entityData.set(FROM_Y, tag.getFloat("FromY"));
        entityData.set(GROUND_Y, tag.getFloat("GroundY"));
        entityData.set(YAW, tag.getFloat("Yaw"));
        if (tag.contains("Payload")) payload = ResourceLocation.parse(tag.getString("Payload"));
        if (tag.hasUUID("Owner")) owner = tag.getUUID("Owner");
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        tag.putInt("Phase", entityData.get(PHASE));
        tag.putInt("PhaseTicks", phaseTicks());
        tag.putFloat("FromY", entityData.get(FROM_Y));
        tag.putFloat("GroundY", entityData.get(GROUND_Y));
        tag.putFloat("Yaw", entityData.get(YAW));
        if (payload != null) tag.putString("Payload", payload.toString());
        if (owner != null) tag.putUUID("Owner", owner);
    }
}
