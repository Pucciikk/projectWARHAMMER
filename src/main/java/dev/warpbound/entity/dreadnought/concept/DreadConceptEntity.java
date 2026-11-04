package dev.warpbound.entity.dreadnought.concept;

import dev.warpbound.Warpbound;
import dev.warpbound.core.WarpboundItems;
import dev.warpbound.entity.multipart.HitboxPart;
import dev.warpbound.entity.multipart.MultipartHost;
import dev.warpbound.gun.GunProjectile;
import dev.warpbound.gun.GunProjectiles;
import dev.warpbound.gun.GunSpec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.item.ItemStack;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.animation.AnimationController;
import software.bernie.geckolib.animation.PlayState;
import software.bernie.geckolib.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.function.Consumer;

/**
 * Дредноут-саркофаг: меш из исходной модели автора на GeckoLib. Без пилота стоит неподвижно, присев и наклонив корпус.
 * С пилотом: W/S ход с инерцией, A/D поворот ног, мышь ведёт корпус и пушку, спринт — бег, ЛКМ стрельба, ПКМ удар клешнёй, V толчок.
 * Работает на прометии и болтах: заправка снаружи ПКМ с канистрой, ведром или магазином.
 * Хитбоксы на каждую часть тела: по ним бьют и об них упираются, верхние части ещё и не дают зайти в блоки.
 */
public class DreadConceptEntity extends PathfinderMob implements GeoEntity, MultipartHost {
    private static final RawAnimation WALK = RawAnimation.begin().thenLoop("move.walk");
    private static final RawAnimation BACK = RawAnimation.begin().thenLoop("move.back");
    private static final RawAnimation RUN = RawAnimation.begin().thenLoop("move.run");
    private static final RawAnimation IDLE = RawAnimation.begin().thenLoop("misc.idle");
    private static final RawAnimation DORMANT = RawAnimation.begin().thenLoop("misc.dormant");
    private static final RawAnimation DEATH = RawAnimation.begin().thenPlayAndHold("misc.death");
    private static final RawAnimation FIRE = RawAnimation.begin().thenPlay("attack.fire");
    private static final RawAnimation MELEE = RawAnimation.begin().thenPlay("attack.melee");
    private static final RawAnimation SHOVE = RawAnimation.begin().thenPlay("attack.shove");
    private static final EntityDataAccessor<Integer> AMMO = SynchedEntityData.defineId(DreadConceptEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> FUEL = SynchedEntityData.defineId(DreadConceptEntity.class, EntityDataSerializers.INT);
    /** Запасы. Расход раз в 2 тика: на месте 1, шаг 2, бег 4. Полного бака хватает на 10 минут шага. */
    public static final int MAX_AMMO = 300, MAX_FUEL = 12000;
    private static final int BOLTS_PER_MAGAZINE = 30, FUEL_CANISTER = 4000, FUEL_BUCKET = 3000;
    /** Толчок: момент удара в тиках (SHOVE_HIT в gait.py), перезарядка, урон и сила отброса. */
    private static final int SHOVE_IMPACT_TICKS = 6, SHOVE_COOLDOWN = 22;
    private static final float SHOVE_DAMAGE = 8f, SHOVE_FORCE = 1.2f;
    /** Скорости при нормальной скорости клипа: WALK_SPEED и RUN_SPEED в tools/models/blender/dread/gait.py. */
    private static final float WALK_BLOCKS_PER_SECOND = 2.037f, RUN_BLOCKS_PER_SECOND = 4.355f;
    /** С какой скорости (блоков в секунду) вид идёт в бег. */
    private static final float RUN_THRESHOLD = 3.1f;
    /** Во сколько раз бег быстрее шага: при этом ноги совпадают с землёй у обоих клипов. */
    private static final float RUN_BOOST = RUN_BLOCKS_PER_SECOND / WALK_BLOCKS_PER_SECOND - 1f;
    /** Смыкание клешни в клипе удара: CLAW_HIT в gait.py, в тиках. */
    private static final int CLAW_IMPACT_TICKS = 11, CLAW_COOLDOWN = 30;
    private static final float CLAW_REACH = 3.6f;
    /** Длина цикла в блоках пути: на столько ступня проходит за два шага. Нужна, чтобы хитбоксы ног ходили вместе с моделью. */
    private static final float CYCLE_BLOCKS = 1.833f, STEP_SWING = 0.55f, RUN_CYCLE_BLOCKS = 2.7f, RUN_SWING = 0.67f;
    /** Сколько тиков лежит мёртвый после падения (анимация 5,4 с), потом рассыпается. */
    private static final int CORPSE_TICKS = 220;
    /** Выхлопные трубы: вправо, вверх, вперёд от центра у земли. */
    private static final float PIPE_RIGHT = 0.55f, PIPE_UP = 3.62f, PIPE_FORWARD = -0.95f;
    private static final float MAX_TURN = 2.2f, TORSO_TURN = 4.5f, TORSO_LIMIT = 75f;
    /** Глаза пилота у лобовой брони: изнутри видна только смотровая щель, поэтому корпус не должен лезть в неё. */
    private static final float SEAT_UP = 1.72f, SEAT_FORWARD = 1.28f;

    /** Клиентский хук: тряска камеры от шага. Ставит клиентский код. */
    public static Consumer<Float> stepShake = amount -> {
    };

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private final DreadConcepts.Variant variant;
    private final HitboxPart[] parts;
    private final HitboxPart[] upper;
    private float gaitDistance;
    private float throttle, boost, turnVelocity;
    public float torsoYaw, torsoYawO;
    private int attackCooldown, clawCooldown;
    private int meleeImpact = -1, shoveImpact = -1;

    public DreadConceptEntity(EntityType<? extends DreadConceptEntity> type, Level level, DreadConcepts.Variant variant) {
        super(type, level);
        this.variant = variant;
        setPersistenceRequired();
        // up — низ коробки над землёй. armor — множитель входящего урона: больше 1 — уязвимо. Размеры сняты с модели
        this.parts = new HitboxPart[]{
                part("foot_right", false, 0.95f, 0f, 0f, 1.45f, 0.42f, 0.5f),
                part("foot_left", false, -0.95f, 0f, 0f, 1.45f, 0.42f, 0.5f),
                part("leg_right", false, 0.88f, 0.4f, 0f, 0.95f, 1.15f, 0.7f),
                part("leg_left", false, -0.88f, 0.4f, 0f, 0.95f, 1.15f, 0.7f),
                part("pelvis", false, 0f, 1.2f, 0f, 1.1f, 0.85f, 0.8f),
                part("hull_right", true, 0.62f, 1.62f, 0f, 1.25f, 1.98f, 0.5f),
                part("hull_left", true, -0.62f, 1.62f, 0f, 1.25f, 1.98f, 0.5f),
                part("sarcophagus", true, 0f, 1.75f, 0.88f, 1.0f, 1.5f, 1.4f),
                part("engine", true, 0f, 1.8f, -0.82f, 1.7f, 1.8f, 1.6f),
                part("gun_arm", true, 1.43f, 1.3f, -0.1f, 0.75f, 1.95f, 0.7f),
                part("gun", true, 1.38f, 2.08f, 0.9f, 0.72f, 0.75f, 0.9f),
                part("fist_arm", true, -1.55f, 2.0f, 0f, 1.0f, 1.25f, 0.7f),
                part("fist", true, -1.62f, 0.68f, 0.45f, 1.25f, 1.42f, 0.6f),
        };
        this.upper = new HitboxPart[]{parts[5], parts[6], parts[7], parts[8], parts[9], parts[10], parts[11]};
        // Части получают ID сразу после хозяина, как у дракона
        setId(getId());
        this.torsoYaw = this.torsoYawO = getYRot();
    }

    private HitboxPart part(String name, boolean torso, float right, float up, float forward, float width, float height, float armor) {
        return new HitboxPart(this, new HitboxPart.Spec(name, torso, right, up, forward, width, height, armor));
    }

    public DreadConcepts.Variant variant() {
        return variant;
    }

    public static AttributeSupplier.Builder attributes() {
        // скорость подобрана замером под клип ходьбы: 0,066 дало 2,91 блока в секунду, поэтому 0,0462 даёт 2,04
        return PathfinderMob.createMobAttributes().add(Attributes.MAX_HEALTH, 400).add(Attributes.MOVEMENT_SPEED, 0.0462).add(Attributes.ARMOR, 20)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1).add(Attributes.ATTACK_DAMAGE, 24).add(Attributes.STEP_HEIGHT, 1.2);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(AMMO, MAX_AMMO);
        builder.define(FUEL, MAX_FUEL);
    }

    public int ammo() {
        return entityData.get(AMMO);
    }

    public int fuel() {
        return entityData.get(FUEL);
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("Ammo", ammo());
        tag.putInt("Fuel", fuel());
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.contains("Ammo")) entityData.set(AMMO, Mth.clamp(tag.getInt("Ammo"), 0, MAX_AMMO));
        if (tag.contains("Fuel")) entityData.set(FUEL, Mth.clamp(tag.getInt("Fuel"), 0, MAX_FUEL));
    }

    // ---------------------------------------------------------------- части

    @Override
    public HitboxPart[] getHitboxParts() {
        return parts;
    }

    @Override
    public void setId(int id) {
        super.setId(id);
        // parts == null, пока родительский конструктор присваивает первый ID
        if (parts != null) {
            for (int i = 0; i < parts.length; i++) parts[i].setId(id + i + 1);
        }
    }

    @Override
    public boolean hurtFromPart(HitboxPart part, DamageSource source, float amount) {
        boolean hurt = hurt(source, amount);
        if (hurt && level() instanceof ServerLevel server) {
            Vec3 at = part.getBoundingBox().getCenter();
            server.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y, at.z, 8, 0.2, 0.2, 0.2, 0.15);
            if (part.spec.armor() > 1f) server.sendParticles(ParticleTypes.LARGE_SMOKE, at.x, at.y, at.z, 3, 0.15, 0.15, 0.15, 0.02);
        }
        return hurt;
    }

    /** Точка в мире от центра у земли: вправо, вверх, вперёд по заданному повороту. */
    private Vec3 offset(float yawDeg, float right, float up, float forward) {
        float yaw = yawDeg * Mth.DEG_TO_RAD;
        // вперёд — (-sin, cos), вправо — (-cos, -sin): так в Minecraft устроен yaw
        return new Vec3(getX() - Mth.sin(yaw) * forward - Mth.cos(yaw) * right, getY() + up, getZ() + Mth.cos(yaw) * forward - Mth.sin(yaw) * right);
    }

    private void updateParts() {
        // ступни ходят вместе с моделью: левая и правая в противофазе
        double perSecond = horizontalSpeed();
        boolean running = perSecond > RUN_THRESHOLD, moving = perSecond > 0.15;
        float swing = running ? Mth.cos(gaitDistance / RUN_CYCLE_BLOCKS * Mth.TWO_PI) * RUN_SWING : Mth.cos(gaitDistance / CYCLE_BLOCKS * Mth.TWO_PI) * STEP_SWING;
        for (HitboxPart p : parts) {
            HitboxPart.Spec s = p.spec;
            float fwd = s.forward();
            if (moving) {
                if (s.name().equals("foot_right") || s.name().equals("leg_right")) fwd += swing;
                if (s.name().equals("foot_left") || s.name().equals("leg_left")) fwd -= swing;
            }
            Vec3 at = offset(s.torsoFrame() ? torsoYaw : yBodyRot, s.right(), s.up(), fwd);
            p.xo = p.xOld = p.getX();
            p.yo = p.yOld = p.getY();
            p.zo = p.zOld = p.getZ();
            p.setPos(at.x, at.y, at.z);
        }
    }

    /** Основной хитбокс уже машины: корпус и руки шире него. Верхние части не дают вдавиться в стену; если часть уже в блоке (поворот), не держим её там. */
    @Override
    public void move(MoverType type, Vec3 delta) {
        if (type == MoverType.SELF && parts != null && delta.horizontalDistanceSqr() > 1e-8) {
            double dx = delta.x, dz = delta.z;
            for (HitboxPart p : upper) {
                AABB box = p.getBoundingBox();
                if (!level().noBlockCollision(this, box)) continue;
                if (dx != 0 && !level().noBlockCollision(this, box.move(dx, 0, 0))) dx = 0;
                if (dz != 0 && !level().noBlockCollision(this, box.move(0, 0, dz))) dz = 0;
            }
            delta = new Vec3(dx, delta.y, dz);
        }
        super.move(type, delta);
    }

    @Override
    public boolean isPickable() {
        // По самой туше не бьём: удары и снаряды ловят части
        return false;
    }

    @Override
    public boolean canBeCollidedWith() {
        return isAlive();
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    protected void doPush(Entity entity) {
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    protected boolean canRide(Entity vehicle) {
        return false;
    }

    // ---------------------------------------------------------------- пилот

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        if (!isAlive()) return InteractionResult.PASS;
        // снаружи, с припасом в руке: заправка вместо посадки
        ItemStack held = player.getItemInHand(hand);
        String heldId = BuiltInRegistries.ITEM.getKey(held.getItem()).getPath();
        int fuelGain = heldId.equals("promethium_canister") ? FUEL_CANISTER : heldId.equals("crude_promethium_bucket") ? FUEL_BUCKET : 0;
        boolean magazine = heldId.equals("bolt_magazine");
        if (fuelGain > 0 || magazine) {
            if (magazine ? ammo() >= MAX_AMMO : fuel() >= MAX_FUEL) return InteractionResult.PASS;
            if (!level().isClientSide) {
                if (magazine) entityData.set(AMMO, Math.min(MAX_AMMO, ammo() + BOLTS_PER_MAGAZINE));
                else entityData.set(FUEL, Math.min(MAX_FUEL, fuel() + fuelGain));
                if (!player.getAbilities().instabuild) held.shrink(1);
                level().playSound(null, blockPosition(), magazine ? sound("gun.bolter_mag_in") : SoundEvents.BUCKET_EMPTY, SoundSource.NEUTRAL, 1f, magazine ? 0.8f : 0.7f);
            }
            return InteractionResult.sidedSuccess(level().isClientSide);
        }
        if (isVehicle() || player.isSecondaryUseActive()) return InteractionResult.PASS;
        if (!level().isClientSide) {
            player.startRiding(this);
            torsoYaw = torsoYawO = yBodyRot;
            level().playSound(null, blockPosition(), SoundEvents.IRON_DOOR_CLOSE, SoundSource.NEUTRAL, 1.2f, 0.5f);
            level().playSound(null, blockPosition(), sound("dread.foley"), SoundSource.NEUTRAL, 1.2f, 0.85f);
        }
        return InteractionResult.sidedSuccess(level().isClientSide);
    }

    @Nullable
    @Override
    public LivingEntity getControllingPassenger() {
        return getFirstPassenger() instanceof Player player && isAlive() ? player : null;
    }

    @Override
    protected void tickRidden(Player player, Vec3 input) {
        super.tickRidden(player, input);
        // без прометия мотор заглох: только докатывается
        boolean powered = fuel() > 0;
        float want = !powered ? 0f : player.zza > 0 ? 1f : player.zza < 0 ? -0.5f : 0f;
        boost += Mth.clamp((player.zza > 0 && player.isSprinting() ? 1f : 0f) - boost, -0.03f, 0.02f);
        // разгон и торможение растянуты: многотонная машина не останавливается на месте
        throttle += Mth.clamp(want - throttle, -0.06f, 0.05f);
        float targetTurn = powered ? -player.xxa * MAX_TURN * (1f - 0.3f * Math.abs(throttle)) : 0f;
        // на ходу ноги сами довернут за взглядом: иначе корпус упирается в предел поворота
        if (powered && player.zza > 0) targetTurn += Mth.clamp(Mth.wrapDegrees(player.getYRot() - getYRot()) * 0.05f, -1.4f, 1.4f);
        turnVelocity += (targetTurn - turnVelocity) * 0.18f;
        if (isControlledByLocalInstance()) {
            setYRot(getYRot() + turnVelocity);
            yBodyRot = yHeadRot = getYRot();
        }
    }

    @Override
    protected Vec3 getRiddenInput(Player player, Vec3 input) {
        return new Vec3(0, 0, throttle);
    }

    @Override
    public boolean canSprint() {
        return true;
    }

    @Override
    protected float getRiddenSpeed(Player player) {
        return (float) getAttributeValue(Attributes.MOVEMENT_SPEED) * (1f + RUN_BOOST * boost);
    }

    @Override
    protected Vec3 getPassengerAttachmentPoint(Entity passenger, EntityDimensions dimensions, float scale) {
        return new Vec3(0, SEAT_UP, SEAT_FORWARD).yRot(-torsoYaw * Mth.DEG_TO_RAD);
    }

    @Override
    protected void removePassenger(Entity passenger) {
        super.removePassenger(passenger);
        throttle = boost = turnVelocity = 0;
        setDeltaMovement(getDeltaMovement().multiply(0, 1, 0));
    }

    /** ЛКМ пилота: сервер сам держит темп, клиент шлёт, пока кнопка зажата. */
    public void pilotFire(Player pilot) {
        if (pilot.getVehicle() != this || !isAlive() || attackCooldown > 0 || fuel() <= 0) return;
        attackCooldown = variant.fireInterval();
        if (ammo() <= 0) {
            level().playSound(null, blockPosition(), sound("gun.gun_dry"), SoundSource.PLAYERS, 1f, 0.7f);
            return;
        }
        entityData.set(AMMO, ammo() - 1);
        shoot(pilot);
    }

    /** Клавиша толчка: клешня вперёд, бьёт несильно, зато отбрасывает всех перед машиной. */
    public void pilotShove(Player pilot) {
        if (pilot.getVehicle() != this || !isAlive() || clawCooldown > 0 || fuel() <= 0) return;
        clawCooldown = SHOVE_COOLDOWN;
        shoveImpact = SHOVE_IMPACT_TICKS;
        triggerAnim("attack", "shove");
    }

    /** ПКМ пилота: удар клешнёй, урон в момент смыкания. */
    public void pilotClaw(Player pilot) {
        if (pilot.getVehicle() != this || !isAlive() || clawCooldown > 0 || fuel() <= 0) return;
        clawCooldown = CLAW_COOLDOWN;
        meleeImpact = CLAW_IMPACT_TICKS;
        triggerAnim("attack", "melee");
    }

    private void shoot(Player pilot) {
        triggerAnim("attack", "fire");
        GunProjectile p = GunProjectiles.BOLT_ROUND.create(level());
        if (p == null) return;
        p.setOwner(this);
        GunSpec spec = GunSpec.of(WarpboundItems.BOLTER_ASTARTES);
        p.configure(spec);
        Vec3 at = muzzle();
        // снаряд идёт из дула в точку под прицелом пилота
        Vec3 eye = pilot.getEyePosition(), far = eye.add(pilot.getLookAngle().scale(spec.speed() * spec.lifeTicks()));
        var hit = level().clip(new ClipContext(eye, far, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, pilot));
        Vec3 target = hit.getType() == HitResult.Type.MISS ? far : hit.getLocation();
        Vec3 aim = target.subtract(at);
        aim = aim.lengthSqr() < 0.25 ? pilot.getLookAngle() : aim.normalize();
        p.setPos(at.x, at.y, at.z);
        p.setDeltaMovement(aim.scale(spec.muzzleSpeed()));
        level().addFreshEntity(p);
        level().playSound(null, at.x, at.y, at.z, sound("dread.fire"), SoundSource.PLAYERS, 3f, 0.95f + random.nextFloat() * 0.1f);
        if (level() instanceof ServerLevel server) {
            server.sendParticles(ParticleTypes.FLAME, at.x, at.y, at.z, 3, 0.05, 0.05, 0.05, 0.02);
        }
    }

    /** Дуло в мире: вместе с корпусом. */
    public Vec3 muzzle() {
        Vec3 m = variant.muzzle();
        return offset(torsoYaw, (float) m.x, (float) m.y, (float) m.z);
    }

    /** Смыкание клешни: все, кто попал в зону перед кулаком, кроме пилота. */
    private void clawImpact(ServerLevel server) {
        Vec3 at = offset(torsoYaw, -1.5f, 1.3f, 2.0f);
        AABB zone = new AABB(at, at).inflate(CLAW_REACH / 2);
        Entity pilot = getFirstPassenger();
        boolean any = false;
        for (LivingEntity e : level().getEntitiesOfClass(LivingEntity.class, zone, e -> e != this && e != pilot && e.isAlive())) {
            doHurtTarget(e);
            any = true;
        }
        server.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y, at.z, any ? 22 : 8, 0.3, 0.3, 0.3, 0.2);
    }

    /** Толчок: широкая зона перед корпусом, отбрасывает от машины и чуть вверх. */
    private void shoveImpact(ServerLevel server) {
        Vec3 at = offset(torsoYaw, -0.6f, 1.4f, 2.4f);
        Vec3 center = position();
        AABB zone = new AABB(at, at).inflate(2.4, 1.6, 2.4);
        Entity pilot = getFirstPassenger();
        DamageSource source = damageSources().mobAttack(this);
        for (LivingEntity e : level().getEntitiesOfClass(LivingEntity.class, zone, e -> e != this && e != pilot && e.isAlive())) {
            e.hurt(source, SHOVE_DAMAGE);
            Vec3 away = e.position().subtract(center).multiply(1, 0, 1);
            away = away.lengthSqr() < 1e-4 ? new Vec3(0, 0, 1) : away.normalize();
            e.push(away.x * SHOVE_FORCE, 0.3, away.z * SHOVE_FORCE);
            e.hurtMarked = true;
        }
        server.sendParticles(ParticleTypes.CRIT, at.x, at.y, at.z, 14, 0.6, 0.5, 0.6, 0.25);
        server.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y, at.z, 10, 0.3, 0.3, 0.3, 0.25);
    }

    private void burnFuel() {
        if (fuel() <= 0 || !isVehicle() || level().isClientSide) return;
        double speed = horizontalSpeed();
        int burn = speed > RUN_THRESHOLD ? 4 : speed > 0.15 ? 2 : 1;
        // 1 в покое: мотор работает, пока пилот внутри
        if (tickCount % 2 == 0) entityData.set(FUEL, Math.max(0, fuel() - burn));
    }

    // ---------------------------------------------------------------- тик

    @Override
    public void tick() {
        super.tick();
        gaitDistance += (float) (horizontalSpeed() / 20);
        updateTorso();
        updateParts();
        if (attackCooldown > 0) attackCooldown--;
        if (clawCooldown > 0) clawCooldown--;
        if (level() instanceof ServerLevel server && meleeImpact >= 0 && --meleeImpact == 0) clawImpact(server);
        if (level() instanceof ServerLevel server && shoveImpact >= 0 && --shoveImpact == 0) shoveImpact(server);
        burnFuel();
        if (level().isClientSide) exhaust();
    }

    private void updateTorso() {
        torsoYawO = torsoYaw;
        Entity pilot = getFirstPassenger();
        float target = pilot != null ? pilot.getYHeadRot() : yBodyRot;
        torsoYaw += Mth.clamp(Mth.wrapDegrees(target - torsoYaw), -TORSO_TURN, TORSO_TURN);
        float rel = Mth.wrapDegrees(torsoYaw - yBodyRot);
        if (Math.abs(rel) > TORSO_LIMIT) torsoYaw = yBodyRot + Math.signum(rel) * TORSO_LIMIT;
        // чтобы интерполяция не крутила корпус через полный круг
        torsoYawO = torsoYaw - Mth.wrapDegrees(torsoYaw - torsoYawO);
    }

    /** Поворот корпуса относительно ног, градусы: для рендера. */
    public float torsoRelative(float partial) {
        return Mth.wrapDegrees(Mth.rotLerp(partial, torsoYawO, torsoYaw) - Mth.rotLerp(partial, yBodyRotO, yBodyRot));
    }

    /** Наклон пушки за взглядом пилота, градусы, вниз положительно. */
    public float gunPitch(float partial) {
        return getFirstPassenger() instanceof Player p ? Mth.clamp(p.getViewXRot(partial), -28f, 28f) : 0f;
    }

    /** Скорость по настоящему смещению, блоков в секунду: одинакова у пилота, сервера и других игроков. */
    private double horizontalSpeed() {
        double dx = getX() - xo, dz = getZ() - zo;
        return Math.sqrt(dx * dx + dz * dz) * 20;
    }

    private boolean movingBackward() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return -(getX() - xo) * Mth.sin(yaw) + (getZ() - zo) * Mth.cos(yaw) < 0;
    }

    /** Дым из труб только при работающем моторе: лёгкий в покое, гуще на ходу. Подбитая машина горит, мёртвая долго чадит. */
    private void exhaust() {
        if (!isAlive()) {
            if (deathTime < 150 && deathTime % 2 == 0) {
                Vec3 c = position().add((random.nextDouble() - 0.5) * 1.6, 0.8 + random.nextDouble() * 0.8, (random.nextDouble() - 0.5) * 1.6);
                level().addParticle(ParticleTypes.LARGE_SMOKE, c.x, c.y, c.z, 0, 0.05, 0);
                if (deathTime % 6 == 0) level().addParticle(ParticleTypes.ELECTRIC_SPARK, c.x, c.y, c.z, 0, 0.1, 0);
            }
            return;
        }
        if (!isVehicle() || fuel() <= 0) return;
        double speed = horizontalSpeed();
        int every = speed > RUN_THRESHOLD ? 3 : speed > 0.15 ? 7 : 16;
        if (tickCount % every != 0) return;
        for (int side = -1; side <= 1; side += 2) {
            if (random.nextFloat() < 0.35f) continue;
            Vec3 at = offset(torsoYaw, side * PIPE_RIGHT, PIPE_UP, PIPE_FORWARD);
            level().addParticle(ParticleTypes.WHITE_SMOKE, at.x, at.y, at.z, 0, 0.025 + random.nextDouble() * 0.02, 0);
        }
        if (getHealth() < getMaxHealth() * 0.35f && tickCount % 16 == 0) {
            Vec3 c = offset(torsoYaw, 0, 2.6f, 0);
            level().addParticle(ParticleTypes.LARGE_SMOKE, c.x, c.y, c.z, 0, 0.06, 0);
        }
    }

    /** Лежит после анимации падения, потом рассыпается в дым. Пилот вылетает при падении. */
    @Override
    protected void tickDeath() {
        deathTime++;
        if (deathTime == 1 && !level().isClientSide) ejectPassengers();
        if (deathTime >= CORPSE_TICKS && level() instanceof ServerLevel server) {
            server.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 0.8, getZ(), 40, 1.1, 0.5, 1.1, 0.02);
            server.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 0.8, getZ(), 3, 0.8, 0.3, 0.8, 0);
            remove(RemovalReason.KILLED);
        }
    }

    /** Шаги звучат из метки клипа, ровно в момент постановки ступни: случайный ванильный шаг шёл бы не в такт. */
    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
    }

    /** Метки в клипах: step, step_run, servo, claw, clank, thud, thud_big. На клиенте: звук и пыль от удара об землю. */
    private void onAnimationSound(String name) {
        double x = getX(), y = getY(), z = getZ();
        switch (name) {
            case "step" -> {
                local(sound("dread.step"), 1.0f, 0.95f + random.nextFloat() * 0.1f);
                // лёгкий стук поверх: отсылка к железному голему
                local(SoundEvents.IRON_GOLEM_STEP, 0.35f, 0.8f + random.nextFloat() * 0.1f);
                if (random.nextFloat() < 0.5f) local(sound("dread.foley"), 0.5f, 1f);
                dust(14, 0.9);
                stepShake.accept(0.55f);
            }
            case "step_run" -> {
                // бег: шаг тяжелее и чаще, на каждом шаге лязг брони, гидравлика и удар в землю
                local(sound("dread.step"), 1.4f, 1.02f + random.nextFloat() * 0.1f);
                local(sound("dread.stomp"), 0.4f, 1.3f + random.nextFloat() * 0.1f);
                local(sound("dread.foley"), 0.8f, 1.1f);
                local(SoundEvents.IRON_GOLEM_STEP, 0.5f, 0.9f + random.nextFloat() * 0.1f);
                if (random.nextFloat() < 0.5f) local(sound("dread.servo"), 0.6f, 1.2f);
                dust(26, 1.3);
                stepShake.accept(0.85f);
            }
            case "claw" -> {
                local(sound("dread.punch"), 1.3f, 1.05f + random.nextFloat() * 0.1f);
                local(sound("dread.servo"), 0.8f, 0.7f);
                stepShake.accept(0.7f);
            }
            case "shove" -> {
                local(sound("dread.punch"), 1.1f, 1.25f + random.nextFloat() * 0.1f);
                local(sound("dread.stomp"), 0.5f, 1.4f);
                stepShake.accept(0.6f);
            }
            case "servo" -> local(sound("dread.servo"), 0.5f, 0.9f + random.nextFloat() * 0.2f);
            case "clank" -> {
                local(sound("dread.punch"), 0.45f, 0.85f + random.nextFloat() * 0.2f);
                level().addParticle(ParticleTypes.ELECTRIC_SPARK, x, y + 2.2, z, (random.nextDouble() - 0.5) * 0.2, 0.15, (random.nextDouble() - 0.5) * 0.2);
            }
            case "thud" -> {
                local(sound("dread.stomp"), 1.0f, 0.9f);
                dust(40, 1.8);
                stepShake.accept(0.8f);
            }
            case "thud_big" -> {
                local(sound("dread.fall"), 1.4f, 0.9f);
                local(sound("dread.stomp"), 1.4f, 0.75f);
                dust(80, 2.4);
                stepShake.accept(1f);
            }
            default -> {
            }
        }
    }

    private static SoundEvent sound(String name) {
        return SoundEvent.createVariableRangeEvent(Warpbound.id(name));
    }

    private void local(SoundEvent sound, float volume, float pitch) {
        level().playLocalSound(getX(), getY() + 0.5, getZ(), sound, SoundSource.NEUTRAL, volume, pitch, false);
    }

    /** Пыль из блока под ногами. */
    private void dust(int count, double spread) {
        BlockState under = level().getBlockState(blockPosition().below());
        if (under.isAir()) return;
        BlockParticleOption particle = new BlockParticleOption(ParticleTypes.BLOCK, under);
        for (int i = 0; i < count; i++) {
            double a = random.nextDouble() * Mth.TWO_PI, r = random.nextDouble() * spread;
            level().addParticle(particle, getX() + Math.cos(a) * r, getY() + 0.05, getZ() + Math.sin(a) * r, Math.cos(a) * 0.15, 0.1 + random.nextDouble() * 0.12, Math.sin(a) * 0.15);
        }
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "move", 6, state -> {
            if (isDeadOrDying()) {
                state.getController().setAnimationSpeed(1);
                return state.setAndContinue(DEATH);
            }
            // без пилота или без прометия: заглох, стоит неподвижно
            if (!isVehicle() || fuel() <= 0) {
                state.getController().setAnimationSpeed(1);
                return state.setAndContinue(DORMANT);
            }
            double speed = horizontalSpeed();
            // на месте поворот ногами тоже идёт шагом
            boolean turning = Math.abs(Mth.wrapDegrees(yBodyRot - yBodyRotO)) > 0.6f;
            if (speed > RUN_THRESHOLD) {
                state.getController().setAnimationSpeed(Mth.clamp(speed / RUN_BLOCKS_PER_SECOND, 0.6, 1.6));
                return state.setAndContinue(RUN);
            }
            if (speed > 0.15 || turning) {
                // ноги синхронны со скоростью: иначе машина скользит по земле
                state.getController().setAnimationSpeed(Mth.clamp(speed / WALK_BLOCKS_PER_SECOND, 0.6, 1.6));
                return state.setAndContinue(speed > 0.15 && movingBackward() ? BACK : WALK);
            }
            state.getController().setAnimationSpeed(1);
            return state.setAndContinue(IDLE);
        }).setSoundKeyframeHandler(event -> onAnimationSound(event.getKeyframeData().getSound())));
        controllers.add(new AnimationController<>(this, "attack", 1, state -> PlayState.STOP)
                .triggerableAnim("fire", FIRE).triggerableAnim("melee", MELEE).triggerableAnim("shove", SHOVE)
                .setSoundKeyframeHandler(event -> onAnimationSound(event.getKeyframeData().getSound())));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
