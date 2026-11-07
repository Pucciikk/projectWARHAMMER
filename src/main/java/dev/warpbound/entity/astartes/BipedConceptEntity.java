package dev.warpbound.entity.astartes;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.animation.AnimationController;
import software.bernie.geckolib.animation.PlayState;
import software.bernie.geckolib.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.List;

/**
 * Двуногий в силовой броне: бродит, смотрит на игрока, отвечает ударом на удар. Каркас для Астартес и Громового воина.
 * Движение — один контроллер: аллюр выбирается по настоящей скорости тела, клип ускоряется или замедляется под неё, поэтому ступни не скользят.
 * У Астартес удар и вздрагивание накладывает клиент (BipedConceptModel) поверх движения; у Громового воина пока старые клипы.
 */
public class BipedConceptEntity extends PathfinderMob implements GeoEntity {
    private static final RawAnimation IDLE = RawAnimation.begin().thenLoop("misc.idle");
    private static final RawAnimation SNEAK_IDLE = RawAnimation.begin().thenLoop("misc.sneak_idle");
    private static final RawAnimation DEATH = RawAnimation.begin().thenPlayAndHold("misc.death");
    private static final RawAnimation MELEE = RawAnimation.begin().thenPlay("attack.melee");
    private static final RawAnimation HURT = RawAnimation.begin().thenPlay("misc.hurt");
    /** Сколько тиков лежит после падения. Клип смерти 2,7 с. */
    private static final int CORPSE_TICKS = 100;
    /** Погоня и прогулка относительно атрибута скорости: дают бег 5,6 и шаг 2,0 блока в секунду у Астартес. */
    private static final double CHASE = 1.9, STROLL = 1.13;
    /** Ниже — стоит; выше — идёт (два порога, чтобы не мигать между покоем и шагом). */
    private static final float STOP = 0.2f, START = 0.4f;
    /** Новый аллюр берётся, только если он заметно ближе по скорости: доля логарифма отношения скоростей. */
    private static final float SWITCH_MARGIN = 0.12f;
    private static final EntityDataAccessor<String> CLIP = SynchedEntityData.defineId(BipedConceptEntity.class, EntityDataSerializers.STRING);

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private final AstartesConcepts.Variant variant;
    private final RawAnimation[] gaitAnims;
    private final RawAnimation sneakAnim;

    // ---- только на клиенте: сглаженная скорость, текущий аллюр, начало удара
    private float bodySpeed;
    private int speedTick = -1;
    private int gait = -1;
    private float meleeStart = -1000;
    private boolean meleeLeft;
    private int flinchCount;

    public BipedConceptEntity(EntityType<? extends BipedConceptEntity> type, Level level, AstartesConcepts.Variant variant) {
        super(type, level);
        this.variant = variant;
        List<AstartesConcepts.Gait> gaits = variant.gaits();
        this.gaitAnims = new RawAnimation[gaits.size()];
        for (int i = 0; i < gaits.size(); i++) gaitAnims[i] = RawAnimation.begin().thenLoop(gaits.get(i).clip());
        this.sneakAnim = variant.sneak() == null ? null : RawAnimation.begin().thenLoop(variant.sneak().clip());
        setPersistenceRequired();
    }

    public static AttributeSupplier.Builder attributes(AstartesConcepts.Variant v) {
        return PathfinderMob.createMobAttributes().add(Attributes.MAX_HEALTH, v.maxHealth()).add(Attributes.ARMOR, v.armor()).add(Attributes.ATTACK_DAMAGE, v.damage())
                .add(Attributes.MOVEMENT_SPEED, v.moveSpeed()).add(Attributes.KNOCKBACK_RESISTANCE, 0.6).add(Attributes.FOLLOW_RANGE, 32);
    }

    public AstartesConcepts.Variant variant() {
        return variant;
    }

    /** Сглаженная скорость тела, блоков в секунду (клиент). */
    public float bodySpeed() {
        return bodySpeed;
    }

    /** Тик начала последнего удара (клиент) и какой рукой. */
    public float meleeStart() {
        return meleeStart;
    }

    public boolean meleeLeft() {
        return meleeLeft;
    }

    public int flinchCount() {
        return flinchCount;
    }

    /** Клип, заданный командой ({Clip:"move.walk"}) для показа на месте; пусто — обычное поведение. */
    public String forcedClip() {
        return entityData.get(CLIP);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(CLIP, "");
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new MeleeAttackGoal(this, CHASE, true));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, STROLL));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12f));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        if (!entityData.get(CLIP).isEmpty()) tag.putString("Clip", entityData.get(CLIP));
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.contains("Clip")) entityData.set(CLIP, tag.getString("Clip"));
    }

    /** Замах приходит на клиент пакетом анимации (MeleeAttackGoal зовёт swing перед уроном): с него и считаем удар. Руки чередуются. */
    @Override
    public void swing(InteractionHand hand, boolean updateSelf) {
        super.swing(hand, updateSelf);
        if (level().isClientSide) {
            meleeStart = tickCount;
            meleeLeft = !meleeLeft;
        }
    }

    @Override
    public boolean doHurtTarget(Entity target) {
        if (!variant.overlay()) triggerAnim("action", "melee");
        return super.doHurtTarget(target);
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        boolean hurt = super.hurt(source, amount);
        if (hurt && !variant.overlay() && !level().isClientSide && isAlive()) triggerAnim("flinch", "hurt");
        return hurt;
    }

    @Override
    public void handleDamageEvent(DamageSource source) {
        super.handleDamageEvent(source);
        flinchCount++;
    }

    /** Лежит, пока идёт падение и ещё немного: ванильное исчезновение на 20-м тике оборвало бы анимацию. */
    @Override
    protected void tickDeath() {
        deathTime++;
        if (deathTime >= CORPSE_TICKS && !level().isClientSide) remove(RemovalReason.KILLED);
    }

    /** Тяжёлый стук брони вместо обычных шагов. Настоящие звуки подключим вместе с движениями игрока. */
    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.IRON_GOLEM_STEP, 0.3f, 1.3f + random.nextFloat() * 0.15f);
    }

    /** Раз в тик: скорость по настоящему смещению, блоков в секунду, сглаженная за пару тиков (у чужих сущностей позиция приходит рывками). */
    public void updateSpeed() {
        if (speedTick == tickCount) return;
        speedTick = tickCount;
        double dx = getX() - xo, dz = getZ() - zo;
        float raw = (float) (Math.sqrt(dx * dx + dz * dz) * 20);
        bodySpeed += (raw - bodySpeed) * 0.45f;
    }

    /** Аллюр под скорость: ближайший по отношению скоростей, но текущий держим, пока другой не станет заметно ближе. */
    private int pickGait(float speed) {
        List<AstartesConcepts.Gait> gaits = variant.gaits();
        int best = 0;
        float bestErr = Float.MAX_VALUE;
        for (int i = 0; i < gaits.size(); i++) {
            float err = Math.abs((float) Math.log(speed / gaits.get(i).speed()));
            if (err < bestErr) {
                bestErr = err;
                best = i;
            }
        }
        if (gait >= 0 && gait < gaits.size() && gait != best) {
            float cur = Math.abs((float) Math.log(speed / gaits.get(gait).speed()));
            if (cur - bestErr < SWITCH_MARGIN) return gait;
        }
        return best;
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        // у Астартес позу целиком собирает клиент (BipedConceptModel + BipedMotion), контроллеры GeckoLib — только у старых форм
        if (variant.overlay()) return;
        controllers.add(new AnimationController<>(this, "move", 5, state -> {
            state.getController().setAnimationSpeed(1);
            if (isDeadOrDying()) return state.setAndContinue(DEATH);
            String clip = entityData.get(CLIP);
            if (!clip.isEmpty()) return state.setAndContinue(RawAnimation.begin().thenLoop(clip));
            updateSpeed();
            float speed = bodySpeed;
            boolean moving = gait >= 0 ? speed > STOP : speed > START;
            boolean sneaking = isShiftKeyDown() && sneakAnim != null;
            if (!moving) {
                gait = -1;
                return state.setAndContinue(sneaking ? SNEAK_IDLE : IDLE);
            }
            if (sneaking) {
                gait = 0;
                state.getController().setAnimationSpeed(rate(speed, variant.sneak().speed()));
                return state.setAndContinue(sneakAnim);
            }
            gait = pickGait(speed);
            state.getController().setAnimationSpeed(rate(speed, variant.gaits().get(gait).speed()));
            return state.setAndContinue(gaitAnims[gait]);
        }));
        if (!variant.overlay()) {
            controllers.add(new AnimationController<>(this, "action", 3, state -> PlayState.STOP).triggerableAnim("melee", MELEE));
            controllers.add(new AnimationController<>(this, "flinch", 2, state -> PlayState.STOP).triggerableAnim("hurt", HURT));
        }
    }

    /** Скорость проигрывания: ступни идут вровень с землёй, но не медленнее 0,6 и не быстрее 1,5 от задуманной. */
    private static double rate(float speed, float clipSpeed) {
        return Math.min(1.5, Math.max(0.6, speed / clipSpeed));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
