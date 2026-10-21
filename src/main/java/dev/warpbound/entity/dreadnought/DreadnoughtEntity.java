package dev.warpbound.entity.dreadnought;

import dev.warpbound.entity.multipart.HitboxPart;
import dev.warpbound.entity.multipart.MultipartHost;
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
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

/**
 * Дредноут: шагоход с пилотом в саркофаге.
 * Ноги поворачиваются медленно (A/D), корпус следит за взглядом пилота с ограничением,
 * скорость набирается и сбрасывается с инерцией и «толкается» на каждом шаге.
 */
public class DreadnoughtEntity extends PathfinderMob implements MultipartHost {
    /**
     * Масштаб относительно модели. По Imperial Armour 2 дредноут Mk IV — 3,7 м в высоту;
     * берём «игровой» масштаб крупнее (~5 блоков), как делают в играх по 40k,
     * чтобы рядом с игроком (1,8 блока) он выглядел машиной, а не игрушкой.
     */
    public static final float SCALE = 1.3f;
    /** Путь за один шаг в блоках: за это расстояние фаза походки проходит π. */
    public static final float STRIDE = 1.3f;
    /** Доля цикла, когда нога стоит на земле. Больше половины — есть фаза опоры на обе ноги. */
    public static final float STANCE = 0.6f;
    private static final float MAX_TURN = 2.4f;        // град/тик
    private static final float TORSO_TURN = 3.5f;      // град/тик
    private static final float TORSO_LIMIT = 70f;      // насколько корпус может обогнать ноги
    private static final float SEAT_HEIGHT = 2.54f * SCALE;   // глаза пилота на ~4.3, внутри саркофага
    private static final float SEAT_FORWARD = 0.4f * SCALE;

    /** Клиентский хук шага (звук, пыль, тряска камеры). Ставит клиентский код. */
    public static StepListener stepListener = (entity, right) -> {
    };

    public interface StepListener {
        void onStep(DreadnoughtEntity entity, boolean rightFoot);
    }

    private final HitboxPart[] parts;

    private float throttle;
    private float turnVelocity;

    public float torsoYaw;
    public float torsoYawO;
    /** Фаза походки в радианах; правая пятка бьёт в землю при gait = 2kπ, левая — при (2k+1)π. */
    public float gait;
    public float gaitO;
    /** 0..1, насколько сейчас идёт: для амплитуды анимации. */
    public float stride;
    public float strideO;
    private int lastStepIndex;

    // Клиентские пружины для вторичного движения: корпус кренится при разгоне,
    // вздрагивает от каждого шага, руки догоняют поворот корпуса с запаздыванием
    public final Spring lean = new Spring(0.08f, 0.25f);
    public final Spring jolt = new Spring(0.22f, 0.18f);
    public final Spring armLag = new Spring(0.10f, 0.22f);
    private float lastSpeed;
    private float lastTorsoYaw;

    public DreadnoughtEntity(EntityType<? extends DreadnoughtEntity> type, Level level) {
        super(type, level);
        this.parts = new HitboxPart[]{
                part("leg_right", false, 0.75f, 0f, 0f, 0.95f, 1.75f, 0.7f),
                part("leg_left", false, -0.75f, 0f, 0f, 0.95f, 1.75f, 0.7f),
                part("pelvis", false, 0f, 1.37f, 0f, 0.85f, 0.8f, 0.6f),
                part("slab_right", true, 0.89f, 2.11f, -0.06f, 0.9f, 1.7f, 0.5f),
                part("slab_left", true, -0.89f, 2.11f, -0.06f, 0.9f, 1.7f, 0.5f),
                part("sarcophagus", true, 0f, 2.11f, 0.5f, 0.85f, 1.8f, 1.5f),
                part("sensor", true, 0f, 3.87f, 0.62f, 0.4f, 0.25f, 1.25f),
                part("engine", true, 0f, 2.31f, -1.03f, 0.9f, 2.1f, 2.0f),
                part("cannon_arm", true, 1.81f, 1.75f, 0f, 0.6f, 1.6f, 0.6f),
                part("cannon", true, 1.81f, 2.51f, 1.6f, 0.6f, 0.6f, 0.9f),
                part("fist_arm", true, -1.81f, 2.09f, 0.3f, 0.95f, 0.95f, 0.6f),
                part("fist", true, -1.81f, 2.09f, 1.45f, 0.8f, 0.95f, 0.6f),
        };
        // Части получают ID сразу после хозяина, как у дракона
        this.setId(this.getId());
        this.torsoYaw = this.torsoYawO = this.getYRot();
    }

    private HitboxPart part(String name, boolean torso, float right, float up, float fwd, float w, float h, float armor) {
        // Размеры сняты с модели (32 ед. = 1 блок) и умножаются на общий масштаб
        return new HitboxPart(this, new HitboxPart.Spec(name, torso, right * SCALE, up * SCALE, fwd * SCALE,
                w * SCALE, h * SCALE, armor));
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Mob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 400.0)
                .add(Attributes.ARMOR, 20.0)
                .add(Attributes.ARMOR_TOUGHNESS, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.055)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.EXPLOSION_KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.STEP_HEIGHT, 1.6)
                .add(Attributes.GRAVITY, 0.12)
                .add(Attributes.SAFE_FALL_DISTANCE, 6.0)
                .add(Attributes.FALL_DAMAGE_MULTIPLIER, 0.5)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(1, new LookAtPlayerGoal(this, Player.class, 12.0f));
        this.goalSelector.addGoal(2, new RandomLookAroundGoal(this));
    }

    // --- части ---

    @Override
    public HitboxPart[] getHitboxParts() {
        return parts;
    }

    @Override
    public void setId(int id) {
        super.setId(id);
        // parts == null, пока родительский конструктор присваивает первый ID
        if (parts != null) {
            for (int i = 0; i < parts.length; i++) {
                parts[i].setId(id + i + 1);
            }
        }
    }

    @Override
    public boolean hurtFromPart(HitboxPart part, DamageSource source, float amount) {
        boolean hurt = this.hurt(source, amount);
        if (hurt && this.level() instanceof ServerLevel server) {
            Vec3 at = part.getBoundingBox().getCenter();
            server.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x, at.y, at.z, 8, 0.2, 0.2, 0.2, 0.15);
            if (part.spec.armor() > 1.0f) {
                // Уязвимое место: искры гуще и дымок
                server.sendParticles(ParticleTypes.LARGE_SMOKE, at.x, at.y, at.z, 4, 0.15, 0.15, 0.15, 0.02);
            }
        }
        return hurt;
    }

    /** Без частей позиция хитбоксов не обновлялась бы между тиками. */
    private void updateParts() {
        float legSwing = Mth.cos(gait) * 0.4f * SCALE * stride;   // правая нога впереди в момент удара пятки (gait = 0)
        for (HitboxPart p : parts) {
            HitboxPart.Spec s = p.spec;
            float yaw = (s.torsoFrame() ? torsoYaw : yBodyRot) * Mth.DEG_TO_RAD;
            float fwd = s.forward();
            if (s.name().equals("leg_right")) fwd += legSwing;
            if (s.name().equals("leg_left")) fwd -= legSwing;
            // Вперёд — (-sin, cos), вправо — (-cos, -sin): так в Minecraft устроен yaw
            double x = getX() - Mth.sin(yaw) * fwd - Mth.cos(yaw) * s.right();
            double z = getZ() + Mth.cos(yaw) * fwd - Mth.sin(yaw) * s.right();
            double y = getY() + s.up();
            p.xo = p.xOld = p.getX();
            p.yo = p.yOld = p.getY();
            p.zo = p.zOld = p.getZ();
            p.setPos(x, y, z);
        }
    }

    // --- тик ---

    @Override
    public void tick() {
        super.tick();
        updateTorso();
        updateGait();
        updateParts();
        if (level().isClientSide) {
            updateSprings();
        }
    }

    private void updateSprings() {
        float speed = (float) Math.sqrt((getX() - xo) * (getX() - xo) + (getZ() - zo) * (getZ() - zo));
        float accel = speed - lastSpeed;
        lastSpeed = speed;
        // Разгон — корпус отстаёт и откидывается назад, торможение — клюёт вперёд
        lean.update(Mth.clamp(-accel * 18f, -1f, 1f));
        jolt.update(0f);
        float yawVel = Mth.wrapDegrees(torsoYaw - lastTorsoYaw);
        lastTorsoYaw = torsoYaw;
        armLag.update(Mth.clamp(-yawVel / 4f, -1f, 1f));
    }

    /** Затухающая пружина: x догоняет цель с перелётом, как тяжёлая подвеска. */
    public static final class Spring {
        private final float stiffness;
        private final float damping;
        public float x;
        public float xO;
        private float v;

        Spring(float stiffness, float damping) {
            this.stiffness = stiffness;
            this.damping = damping;
        }

        void update(float target) {
            xO = x;
            v += (target - x) * stiffness - v * damping;
            x += v;
        }

        void kick(float impulse) {
            v += impulse * 0.35f;
        }

        public float get(float partialTick) {
            return Mth.lerp(partialTick, xO, x);
        }
    }

    private void updateTorso() {
        torsoYawO = torsoYaw;
        Entity pilot = getFirstPassenger();
        float target = pilot != null ? pilot.getYHeadRot() : this.yHeadRot;
        torsoYaw += Mth.clamp(Mth.wrapDegrees(target - torsoYaw), -TORSO_TURN, TORSO_TURN);
        float rel = Mth.wrapDegrees(torsoYaw - yBodyRot);
        if (Math.abs(rel) > TORSO_LIMIT) {
            torsoYaw = yBodyRot + Math.signum(rel) * TORSO_LIMIT;
        }
        // Чтобы интерполяция не крутила корпус через полный круг
        torsoYawO = torsoYaw - Mth.wrapDegrees(torsoYaw - torsoYawO);
    }

    private void updateGait() {
        gaitO = gait;
        strideO = stride;
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        double dx = getX() - xo;
        double dz = getZ() - zo;
        // Знак — вперёд или назад: при заднем ходе ноги шагают назад
        float forward = (float) (-dx * Mth.sin(yaw) + dz * Mth.cos(yaw));
        float turn = Math.abs(Mth.wrapDegrees(yBodyRot - yBodyRotO)) * 0.012f;
        float advance = forward + Math.signum(forward == 0 ? 1 : forward) * turn;
        gait += advance * Mth.PI / STRIDE;
        float moving = Mth.clamp(Math.abs(advance) / 0.1f, 0f, 1f);
        stride += (moving - stride) * 0.15f;

        if (level().isClientSide && stride > 0.2f) {
            int stepIndex = Mth.floor(gait / Mth.PI);
            if (stepIndex != lastStepIndex) {
                stepListener.onStep(this, (stepIndex & 1) == 0);
                jolt.kick(-1.0f * stride);
            }
            lastStepIndex = stepIndex;
        } else {
            lastStepIndex = Mth.floor(gait / Mth.PI);
        }
    }

    // --- пилот ---

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        if (this.isVehicle() || player.isSecondaryUseActive()) {
            return InteractionResult.PASS;
        }
        if (!this.level().isClientSide) {
            player.startRiding(this);
            this.level().playSound(null, this.blockPosition(), SoundEvents.IRON_DOOR_CLOSE, SoundSource.NEUTRAL, 1.2f, 0.5f);
        }
        return InteractionResult.sidedSuccess(this.level().isClientSide);
    }

    @Nullable
    @Override
    public LivingEntity getControllingPassenger() {
        return this.getFirstPassenger() instanceof Player player ? player : super.getControllingPassenger();
    }

    @Override
    protected void tickRidden(Player player, Vec3 input) {
        super.tickRidden(player, input);
        float targetThrottle = player.zza > 0 ? 1f : player.zza < 0 ? -0.45f : 0f;
        // Разгон и торможение растянуты на секунды: многотонная машина не останавливается на месте
        throttle += Mth.clamp(targetThrottle - throttle, -0.022f, 0.018f);
        float targetTurn = -player.xxa * MAX_TURN * (1f - 0.35f * Math.abs(throttle));
        turnVelocity += (targetTurn - turnVelocity) * 0.12f;
        if (this.isControlledByLocalInstance()) {
            this.setYRot(this.getYRot() + turnVelocity);
            this.yBodyRot = this.yHeadRot = this.getYRot();
        }
    }

    @Override
    protected Vec3 getRiddenInput(Player player, Vec3 input) {
        // Скорость пульсирует: максимум посреди шага, минимум когда ступня бьёт в землю
        float surge = 0.55f + 0.45f * Math.abs(Mth.sin(gait));
        return new Vec3(0, 0, throttle * surge);
    }

    @Override
    protected float getRiddenSpeed(Player player) {
        return (float) this.getAttributeValue(Attributes.MOVEMENT_SPEED);
    }

    @Override
    protected Vec3 getPassengerAttachmentPoint(Entity passenger, EntityDimensions dimensions, float scale) {
        // Сиденье в саркофаге, а саркофаг поворачивается вместе с корпусом
        return new Vec3(0, SEAT_HEIGHT, SEAT_FORWARD).yRot(-torsoYaw * Mth.DEG_TO_RAD);
    }

    @Override
    protected void removePassenger(Entity passenger) {
        super.removePassenger(passenger);
        throttle = 0;
        turnVelocity = 0;
    }

    // --- физическое поведение ---

    @Override
    public boolean isPickable() {
        // По самой туше не бьём: удары и стрелы ловят части
        return false;
    }

    @Override
    public boolean canBeCollidedWith() {
        return this.isAlive();
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

    // --- звуки ---

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.IRON_GOLEM_DAMAGE;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.GENERIC_EXPLODE.value();
    }

    @Override
    public float getVoicePitch() {
        return 0.6f;
    }

    @Override
    protected void playStepSound(net.minecraft.core.BlockPos pos, net.minecraft.world.level.block.state.BlockState state) {
        // Шаги озвучивает клиент по фазе походки
    }
}
