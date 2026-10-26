package dev.warpbound.entity.ritual;

import dev.warpbound.core.WarpboundParticles;
import dev.warpbound.core.WarpboundSounds;
import net.minecraft.util.Mth;
import dev.warpbound.entity.WarpboundEntities;
import dev.warpbound.operator.TechPriestEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.level.Level;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.animation.AnimationController;
import software.bernie.geckolib.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.UUID;

/**
 * Ритуал призыва тёмного техножреца: на земле разгорается знак Хаоса синим варп-пламенем,
 * пламя закручивается столбом, гаснет свет, вспышка — и магос поднимается из-под земли сквозь огонь.
 * <p>
 * Знак и столб пламени — модель warp_rift (одна анимация misc.summon на всё время ритуала),
 * искры и языки огня — частицы.
 */
public class WarpRiftEntity extends Entity implements GeoEntity {
    public static final int CHARGE_TICKS = 50, BURST_AT = 115, LIFETIME = 230;
    private static final double RADIUS = 3.2;
    private static final RawAnimation SUMMON = RawAnimation.begin().thenPlayAndHold("misc.summon");

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private UUID owner;
    private int age;

    public WarpRiftEntity(EntityType<? extends WarpRiftEntity> type, Level level) {
        super(type, level);
        noPhysics = true;
        setNoGravity(true);
    }

    public static void open(ServerLevel level, BlockPos ground, UUID owner) {
        WarpRiftEntity rift = WarpboundEntities.WARP_RIFT.create(level);
        if (rift == null) return;
        rift.owner = owner;
        rift.moveTo(ground.getX() + 0.5, ground.getY() + 0.02, ground.getZ() + 0.5, level.random.nextFloat() * 360f, 0);
        level.addFreshEntity(rift);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
    }

    @Override
    public void tick() {
        super.tick();
        age++;
        if (level().isClientSide) {
            clientFx();
            return;
        }
        ServerLevel server = (ServerLevel) level();
        BlockPos pos = blockPosition();
        if (age == 1) server.playSound(null, pos, WarpboundSounds.WARP_RITUAL, SoundSource.HOSTILE, 2.5f, 0.6f);
        if (age % 20 == 5 && age < BURST_AT + 60) server.playSound(null, pos, WarpboundSounds.WARP_FLAME, SoundSource.HOSTILE, 1.6f, 0.7f);
        if (age == CHARGE_TICKS) {
            server.playSound(null, pos, WarpboundSounds.WARP_WHISPER, SoundSource.HOSTILE, 2f, 0.7f);
            server.playSound(null, pos, WarpboundSounds.WARP_RITUAL, SoundSource.HOSTILE, 2.5f, 0.45f);
        }
        if (age == BURST_AT - 25) {
            // свет меркнет: тьма у всех, кто рядом
            for (ServerPlayer p : server.getPlayers(p -> p.distanceToSqr(this) < 20 * 20)) {
                p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 90, 0, false, false));
            }
        }
        if (age == BURST_AT) burst(server);
        if (age > BURST_AT && age < BURST_AT + 24 && age % 3 == 0) geyser(server);
        if (age >= LIFETIME) discard();
    }

    private void burst(ServerLevel server) {
        BlockPos pos = blockPosition();
        double x = getX(), y = getY(), z = getZ();
        server.playSound(null, pos, WarpboundSounds.WARP_BURST, SoundSource.HOSTILE, 3f, 0.7f);
        server.playSound(null, pos, WarpboundSounds.WARP_WHISPER, SoundSource.HOSTILE, 2.5f, 0.5f);
        // молния без поджога и урона — только вспышка и гром
        LightningBolt bolt = EntityType.LIGHTNING_BOLT.create(server);
        if (bolt != null) {
            bolt.moveTo(x, y, z);
            bolt.setVisualOnly(true);
            server.addFreshEntity(bolt);
        }
        server.sendParticles(ParticleTypes.FLASH, x, y + 1.5, z, 4, 0.6, 0.8, 0.6, 0);
        server.sendParticles(ParticleTypes.SONIC_BOOM, x, y + 1.2, z, 3, 0.5, 0.6, 0.5, 0);
        // взрыв пламени: вверх столбом и во все стороны
        for (int i = 0; i < 160; i++) {
            double a = random.nextDouble() * Math.PI * 2, up = random.nextDouble();
            double sp = 0.15 + random.nextDouble() * 0.5;
            server.sendParticles(WarpboundParticles.WARP_FLAME, x + Math.cos(a) * 0.4, y + 0.3 + up * 2, z + Math.sin(a) * 0.4,
                    0, Math.cos(a) * sp * (1 - up), 0.2 + up * 0.9, Math.sin(a) * sp * (1 - up), 1);
        }
        // ударная волна огня по знаку кольцом
        for (int i = 0; i < 96; i++) {
            double a = i * Math.PI * 2 / 96;
            server.sendParticles(WarpboundParticles.WARP_FLAME, x + Math.cos(a) * 0.6, y + 0.2, z + Math.sin(a) * 0.6,
                    0, Math.cos(a), 0.06, Math.sin(a), 0.55);
        }
        server.sendParticles(WarpboundParticles.WARP_RUNE, x, y + 1.5, z, 40, 1.5, 1.2, 1.5, 0.08);
        server.sendParticles(ParticleTypes.REVERSE_PORTAL, x, y + 1.5, z, 150, 1.0, 2.0, 1.0, 0.8);
        // отбрасывает всех рядом
        for (LivingEntity near : server.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(3, 2, 3))) {
            Vec3 push = near.position().subtract(position()).multiply(1, 0, 1).normalize().scale(1.1);
            near.push(push.x, 0.45, push.z);
            near.hurtMarked = true;
        }

        TechPriestEntity priest = WarpboundEntities.DARK_TECH_PRIEST.create(server);
        if (priest == null) return;
        priest.moveTo(getX(), getY(), getZ(), getYRot(), 0);
        priest.finalizeSpawn(server, server.getCurrentDifficultyAt(pos), MobSpawnType.EVENT, null);
        priest.startEmerging();
        server.addFreshEntity(priest);
        priest.arrive(owner);
    }

    /** После вспышки ещё секунду из знака бьют гейзеры пламени. */
    private void geyser(ServerLevel server) {
        double a = random.nextDouble() * Math.PI * 2, r = 0.5 + random.nextDouble() * (RADIUS - 0.5);
        double gx = getX() + Math.cos(a) * r, gz = getZ() + Math.sin(a) * r;
        for (int i = 0; i < 14; i++) {
            server.sendParticles(WarpboundParticles.WARP_FLAME, gx + (random.nextDouble() - 0.5) * 0.3, getY() + 0.2, gz + (random.nextDouble() - 0.5) * 0.3,
                    0, (random.nextDouble() - 0.5) * 0.15, 0.5 + random.nextDouble() * 0.6, (random.nextDouble() - 0.5) * 0.15, 1);
        }
        server.sendParticles(ParticleTypes.ELECTRIC_SPARK, gx, getY() + 0.8, gz, 8, 0.2, 0.6, 0.2, 0.3);
        if (random.nextInt(3) == 0) server.playSound(null, BlockPos.containing(gx, getY(), gz), WarpboundSounds.WARP_FLAME, SoundSource.HOSTILE, 1.5f, 0.9f + random.nextFloat() * 0.4f);
    }

    // моменты анимации misc.summon (тики): когда проступают руны, щупальца, стрелы и метка в центре
    private static final int RUNES_AT = 18, RUNE_STEP = 2, RUNES = 16, TENTACLES_AT = 52, ARROWS_AT = 74, MARK_AT = 92;

    /** Точка знака (в блоках, оси модели) в мире: модель повёрнута на 180° − курс, как у рендера. */
    private Vec3 onSigil(double mx, double mz) {
        float th = (180f - getYRot()) * Mth.DEG_TO_RAD;
        double cos = Mth.cos(th), sin = Mth.sin(th);
        return position().add(mx * cos + mz * sin, 0.05, -mx * sin + mz * cos);
    }

    private void flame(Vec3 at, double spread, double dy, int n) {
        for (int i = 0; i < n; i++) {
            level().addParticle(WarpboundParticles.WARP_FLAME, at.x + (random.nextDouble() - 0.5) * spread, at.y,
                    at.z + (random.nextDouble() - 0.5) * spread, (random.nextDouble() - 0.5) * 0.03, dy * (0.5 + random.nextDouble()),
                    (random.nextDouble() - 0.5) * 0.03);
        }
    }

    private void clientFx() {
        Level level = level();
        double x = getX(), y = getY(), z = getZ();
        // каждая руна вспыхивает огнём, когда проступает, и выпускает свой знак в воздух
        for (int i = 0; i < RUNES; i++) {
            int at = RUNES_AT + i * RUNE_STEP;
            double a = Math.toRadians(i * 360.0 / RUNES);
            Vec3 p = onSigil(Math.sin(a) * 2.6, -Math.cos(a) * 2.6);
            if (age == at) {
                flame(p, 0.4, 0.12, 10);
                level.addParticle(WarpboundParticles.WARP_RUNE, p.x, p.y + 0.4, p.z, 0, 0.02, 0);
            } else if (age > at && age < BURST_AT + 60 && random.nextInt(28) == 0) {
                flame(p, 0.3, 0.05, 1);  // руны тлеют
            }
        }
        // щупальца выползают — по ним бежит пламя
        if (age >= TENTACLES_AT && age < TENTACLES_AT + 20) {
            for (int i = 0; i < 6; i++) {
                double a = Math.toRadians(i * 60 + 15), r = 2.25 - (age - TENTACLES_AT) / 20.0 * 1.3;
                flame(onSigil(Math.sin(a) * r, -Math.cos(a) * r), 0.2, 0.06, 1);
            }
        }
        // стрелы звезды: огонь выстреливает из центра по лучам
        if (age >= ARROWS_AT && age < ARROWS_AT + 8) {
            int k = age - ARROWS_AT;
            double a = Math.toRadians(k * 45 + 22.5);
            for (int s = 0; s < 3; s++) {
                double r = 0.5 + s * 0.4;
                Vec3 p = onSigil(Math.sin(a) * r, -Math.cos(a) * r);
                level.addParticle(WarpboundParticles.WARP_FLAME, p.x, p.y, p.z, Math.sin(a) * 0.08, 0.08, -Math.cos(a) * 0.08);
            }
        }
        if (age == MARK_AT) flame(position(), 0.4, 0.4, 12);
        // столб: пламя закручивается спиралью и густеет к вспышке, вокруг всплывают руны
        // столб загорается, когда знак собран целиком (после метки в центре), и до вспышки набирает силу
        if (age > MARK_AT + 3 && age < BURST_AT) {
            double k = (age - MARK_AT - 3) / (double) (BURST_AT - MARK_AT - 3);
            int n = 3 + (int) (k * 9);
            for (int i = 0; i < n; i++) {
                double a = age * 0.3 + i * Math.PI * 2 / n;
                double r = 1.1 * (1 - k * 0.5) + random.nextDouble() * 0.2;
                level.addParticle(WarpboundParticles.WARP_FLAME, x + Math.cos(a) * r, y + 0.1 + random.nextDouble() * 0.3, z + Math.sin(a) * r,
                        -Math.sin(a) * 0.06, 0.15 + 0.35 * k, Math.cos(a) * 0.06);
            }
            if (random.nextInt(4) == 0) {
                double a = random.nextDouble() * Math.PI * 2, r = 1.5 + random.nextDouble() * 1.5;
                level.addParticle(WarpboundParticles.WARP_RUNE, x + Math.cos(a) * r, y + 0.3 + random.nextDouble(), z + Math.sin(a) * r,
                        0, 0.025, 0);
            }
            if (random.nextInt(3) == 0) {
                level.addParticle(ParticleTypes.ELECTRIC_SPARK, x + (random.nextDouble() - 0.5) * 2.5, y + random.nextDouble() * 3.5,
                        z + (random.nextDouble() - 0.5) * 2.5, 0, 0, 0);
            }
        }
        // после вспышки: столб бьёт ещё секунду, потом знак догорает
        if (age >= BURST_AT && age < BURST_AT + 30) {
            double k = 1 - (age - BURST_AT) / 30.0;
            for (int i = 0; i < 10 * k + 2; i++) {
                double a = random.nextDouble() * Math.PI * 2, r = random.nextDouble() * 0.7;
                level.addParticle(WarpboundParticles.WARP_FLAME, x + Math.cos(a) * r, y + random.nextDouble() * 2.5, z + Math.sin(a) * r,
                        Math.cos(a) * 0.05, 0.4 + random.nextDouble() * 0.6 * k, Math.sin(a) * 0.05);
            }
        }
        if (age >= BURST_AT + 30 && age < LIFETIME - 20 && random.nextInt(2) == 0) {
            double a = random.nextDouble() * Math.PI * 2, r = random.nextDouble() * RADIUS;
            level.addParticle(random.nextInt(3) == 0 ? ParticleTypes.SMOKE : WarpboundParticles.WARP_FLAME,
                    x + Math.cos(a) * r, y + 0.1, z + Math.sin(a) * r, 0, 0.03, 0);
        }
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
    public boolean shouldRenderAtSqrDistance(double distance) {
        return distance < 128 * 128;
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "main", 0, state -> state.setAndContinue(SUMMON)));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        age = tag.getInt("Age");
        if (tag.hasUUID("Owner")) owner = tag.getUUID("Owner");
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        tag.putInt("Age", age);
        if (owner != null) tag.putUUID("Owner", owner);
    }
}
