package dev.warpbound.entity.transport;

import dev.warpbound.core.WarpboundSounds;
import dev.warpbound.entity.WarpboundEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtUtils;
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
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.animation.AnimationController;
import software.bernie.geckolib.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;
import dev.warpbound.entity.anim.WarpAnim;

import java.util.UUID;

/**
 * Имперский челнок — транспорт всех лоялистов: заходит издалека, гасит скорость над точкой,
 * садится на ровную площадку (или зависает низко, если площадка неровная), сбрасывает десантную капсулу
 * с грузом ({@link DropCapsuleEntity}) и улетает.
 * <p>
 * Траектория — функция от фазы и времени, её считают и сервер, и клиент: челнок движется плавно,
 * без рывков от пакетов позиции. Синхронизируются только фаза, её начало, точка посадки и курс.
 */
public class ShuttleEntity extends Entity implements GeoEntity {
    public enum Phase {
        PENDING, APPROACH, DESCEND, PARKED, DEPART
    }

    private static final EntityDataAccessor<Integer> PHASE = SynchedEntityData.defineId(ShuttleEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> PHASE_START = SynchedEntityData.defineId(ShuttleEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<BlockPos> TARGET = SynchedEntityData.defineId(ShuttleEntity.class, EntityDataSerializers.BLOCK_POS);
    private static final EntityDataAccessor<Float> HOVER = SynchedEntityData.defineId(ShuttleEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Float> COURSE = SynchedEntityData.defineId(ShuttleEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Boolean> CARGO = SynchedEntityData.defineId(ShuttleEntity.class, EntityDataSerializers.BOOLEAN);

    // длительности фаз в тиках и геометрия захода (в блоках)
    static final int APPROACH_TICKS = 170, DESCEND_TICKS = 80, PARKED_TICKS = 130, DEPART_TICKS = 170;
    static final int RELEASE_AT = 25;
    private static final double APPROACH_DIST = 80, APPROACH_ALT = 45, HOLD_ALT = 14;
    /** Высота подвеса капсулы над землёй, когда челнок стоит на опорах. */
    static final double CAPSULE_DROP = 5 / 16.0;
    /** Неровная площадка: челнок висит на столько блоков выше самой высокой точки под собой. */
    private static final double HOVER_CLEARANCE = 3.5;

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private ResourceLocation payload = BuiltInRegistries.ENTITY_TYPE.getKey(WarpboundEntities.TECH_PRIEST);
    private UUID owner;
    /** Курс из NBT команды /summon (для автотестов); иначе случайный. */
    private float presetCourse = Float.NaN;

    public ShuttleEntity(EntityType<? extends ShuttleEntity> type, Level level) {
        super(type, level);
        noPhysics = true;
        setNoGravity(true);
    }

    /** Вызвать челнок к точке на земле: он прилетит с грузом {@code payload} и высадит его в капсуле. */
    public static ShuttleEntity dispatch(ServerLevel level, BlockPos ground, EntityType<?> payload, UUID owner) {
        ShuttleEntity shuttle = WarpboundEntities.SHUTTLE.create(level);
        if (shuttle == null) return null;
        shuttle.payload = BuiltInRegistries.ENTITY_TYPE.getKey(payload);
        shuttle.owner = owner;
        shuttle.moveTo(ground.getX() + 0.5, ground.getY(), ground.getZ() + 0.5, 0, 0);
        shuttle.plan(level, ground, level.random.nextFloat() * 360f);
        level.addFreshEntity(shuttle);
        return shuttle;
    }

    /** Выбор площадки: ровно — садимся на опоры, неровно или деревья — зависаем над препятствиями. */
    private void plan(ServerLevel level, BlockPos ground, float course) {
        BlockPos center = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, ground);
        int min = Integer.MAX_VALUE, max = Integer.MIN_VALUE, top = Integer.MIN_VALUE;
        boolean wet = false;
        for (int dx = -4; dx <= 4; dx++) {
            for (int dz = -5; dz <= 5; dz++) {
                BlockPos column = center.offset(dx, 0, dz);
                int solid = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, column.getX(), column.getZ());
                int any = level.getHeight(Heightmap.Types.MOTION_BLOCKING, column.getX(), column.getZ());
                min = Math.min(min, solid);
                max = Math.max(max, solid);
                top = Math.max(top, any);
                if (!level.getFluidState(new BlockPos(column.getX(), solid - 1, column.getZ())).isEmpty()) wet = true;
            }
        }
        boolean flat = max - min <= 1 && top == max && !wet;
        BlockPos target = new BlockPos(center.getX(), flat ? max : center.getY(), center.getZ());
        entityData.set(TARGET, target);
        entityData.set(HOVER, flat ? 0f : (float) (top - center.getY() + HOVER_CLEARANCE));
        entityData.set(COURSE, course);
        entityData.set(CARGO, true);
        setPhase(Phase.APPROACH);
    }

    public Phase phase() {
        return Phase.values()[Math.floorMod(entityData.get(PHASE), Phase.values().length)];
    }

    public boolean hasCargo() {
        return entityData.get(CARGO);
    }

    public boolean isHovering() {
        return entityData.get(HOVER) > 0;
    }

    private void setPhase(Phase phase) {
        entityData.set(PHASE, phase.ordinal());
        entityData.set(PHASE_START, (int) level().getGameTime());
    }

    private int phaseTicks() {
        return (int) level().getGameTime() - entityData.get(PHASE_START);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        builder.define(PHASE, Phase.PENDING.ordinal());
        builder.define(PHASE_START, 0);
        builder.define(TARGET, BlockPos.ZERO);
        builder.define(HOVER, 0f);
        builder.define(COURSE, 0f);
        builder.define(CARGO, true);
    }

    // ------------------------------------------------------------------ траектория

    /** Куда смотрит нос (единичный вектор по курсу). */
    Vec3 forward() {
        float yaw = entityData.get(COURSE) * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    /** Точка стоянки: центр площадки, поднятый на высоту зависания. */
    Vec3 base() {
        BlockPos t = entityData.get(TARGET);
        return new Vec3(t.getX() + 0.5, t.getY() + entityData.get(HOVER), t.getZ() + 0.5);
    }

    /** Высота земли под площадкой (при зависании челнок выше неё на HOVER). */
    double groundY() {
        return entityData.get(TARGET).getY();
    }

    static double smooth(double s) {
        s = Mth.clamp(s, 0, 1);
        return s * s * (3 - 2 * s);
    }

    /** Положение и тангаж в момент {@code t} фазы. */
    private void pose(Phase phase, double t) {
        Vec3 base = base(), f = forward();
        Vec3 pos;
        float pitch = 0;
        switch (phase) {
            case APPROACH -> {
                double s = Mth.clamp(t / APPROACH_TICKS, 0, 1);
                double e = 1 - Math.pow(1 - s, 3);                       // гасит скорость к точке
                double alt = HOLD_ALT + (APPROACH_ALT - HOLD_ALT) * (1 - smooth(s));
                pos = base.add(f.scale(-APPROACH_DIST * (1 - e))).add(0, alt, 0);
                // идёт носом вниз, у точки задирает нос, гася скорость, и выравнивается
                pitch = (float) (7 * (1 - s) - 16 * Math.sin(Math.PI * Mth.clamp((s - 0.45) / 0.55, 0, 1)));
            }
            case DESCEND -> {
                double s = Mth.clamp(t / DESCEND_TICKS, 0, 1);
                pos = base.add(0, HOLD_ALT * (1 - smooth(s)), 0);
            }
            case DEPART -> {
                double s = Mth.clamp(t / DEPART_TICKS, 0, 1);
                double up = 24 * smooth(s * 2.2);
                double ahead = 160 * Math.pow(Math.max(0, s - 0.3) / 0.7, 2);
                pos = base.add(f.scale(ahead)).add(0, up + ahead * 0.25, 0);
                pitch = (float) (-10 * Math.sin(Math.PI * Mth.clamp((s - 0.2) / 0.8, 0, 1)));
            }
            default -> pos = base;
        }
        setPos(pos);
        setYRot(entityData.get(COURSE));
        setXRot(pitch);
    }

    // ------------------------------------------------------------------ тик

    @Override
    public void tick() {
        super.tick();
        if (phase() == Phase.PENDING) {
            // поставлен командой /summon: садимся там, где поставили
            if (level() instanceof ServerLevel server) {
                plan(server, blockPosition(), Float.isNaN(presetCourse) ? random.nextFloat() * 360f : presetCourse);
            }
            return;
        }
        int t = phaseTicks();
        pose(phase(), t);
        if (level().isClientSide) {
            ShuttleFx.tick(this, phase(), t);
            return;
        }
        ServerLevel server = (ServerLevel) level();
        switch (phase()) {
            case APPROACH -> {
                if (t == 0) server.playSound(null, blockPosition(), WarpboundSounds.SHUTTLE_ROAR, SoundSource.NEUTRAL, 6f, 0.8f);
                if (t >= APPROACH_TICKS) setPhase(Phase.DESCEND);
            }
            case DESCEND -> {
                if (t >= DESCEND_TICKS) {
                    setPhase(Phase.PARKED);
                    if (!isHovering()) server.playSound(null, blockPosition(), WarpboundSounds.SHUTTLE_TOUCHDOWN, SoundSource.NEUTRAL, 3f, 0.7f);
                }
            }
            case PARKED -> {
                if (t == RELEASE_AT && hasCargo()) releaseCapsule(server);
                if (t >= PARKED_TICKS) {
                    setPhase(Phase.DEPART);
                    server.playSound(null, blockPosition(), WarpboundSounds.SHUTTLE_ROAR, SoundSource.NEUTRAL, 6f, 0.9f);
                }
            }
            case DEPART -> {
                if (t >= DEPART_TICKS) discard();
            }
            default -> {
            }
        }
    }

    private void releaseCapsule(ServerLevel server) {
        entityData.set(CARGO, false);
        triggerAnim(WarpAnim.ACTION, WarpAnim.DEPLOY_NAME);
        Vec3 drop = base().add(0, CAPSULE_DROP, 0);
        BlockPos below = BlockPos.containing(drop);
        double ground = server.getHeight(Heightmap.Types.MOTION_BLOCKING, below.getX(), below.getZ());
        DropCapsuleEntity.release(server, drop, Math.min(ground, drop.y), entityData.get(COURSE), payload, owner);
        server.playSound(null, below, WarpboundSounds.CAPSULE_RELEASE, SoundSource.NEUTRAL, 2f, 0.8f);
    }

    // ------------------------------------------------------------------ прочее

    /** Позицию считает сам клиент — пакеты позиции с сервера не нужны. */
    @Override
    public void lerpTo(double x, double y, double z, float yRot, float xRot, int steps) {
    }

    @Override
    public boolean shouldRenderAtSqrDistance(double distance) {
        return distance < 256 * 256;
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
        controllers.add(new AnimationController<>(this, WarpAnim.MAIN, 20, state -> {
            Phase p = phase();
            boolean landing = p == Phase.DESCEND || p == Phase.PARKED || p == Phase.DEPART && phaseTicks() < 30;
            return state.setAndContinue(landing ? LAND : FLY);
        }));
        controllers.add(WarpAnim.actions(this, WarpAnim.DEPLOY_NAME));
    }

    private static final RawAnimation FLY = RawAnimation.begin().thenLoop("move.fly");
    private static final RawAnimation LAND = RawAnimation.begin().thenLoop("misc.land");

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        entityData.set(PHASE, tag.getInt("Phase"));
        entityData.set(PHASE_START, (int) level().getGameTime() - tag.getInt("PhaseTicks"));
        NbtUtils.readBlockPos(tag, "Target").ifPresent(pos -> entityData.set(TARGET, pos));
        entityData.set(HOVER, tag.getFloat("Hover"));
        entityData.set(COURSE, tag.getFloat("Course"));
        if (tag.contains("Course")) presetCourse = tag.getFloat("Course");
        entityData.set(CARGO, tag.getBoolean("Cargo"));
        if (tag.contains("Payload")) payload = ResourceLocation.parse(tag.getString("Payload"));
        if (tag.hasUUID("Owner")) owner = tag.getUUID("Owner");
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        tag.putInt("Phase", entityData.get(PHASE));
        tag.putInt("PhaseTicks", phaseTicks());
        tag.put("Target", NbtUtils.writeBlockPos(entityData.get(TARGET)));
        tag.putFloat("Hover", entityData.get(HOVER));
        tag.putFloat("Course", entityData.get(COURSE));
        tag.putBoolean("Cargo", entityData.get(CARGO));
        tag.putString("Payload", payload.toString());
        if (owner != null) tag.putUUID("Owner", owner);
    }
}
