package dev.warpbound.client.player;

import dev.warpbound.entity.astartes.AstartesConcepts;
import dev.warpbound.player.GeneForm;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import software.bernie.geckolib.animatable.GeoReplacedEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.animation.AnimationController;
import software.bernie.geckolib.animation.AnimationState;
import software.bernie.geckolib.animation.PlayState;
import software.bernie.geckolib.animation.RawAnimation;
import software.bernie.geckolib.constant.DataTickets;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.List;

/**
 * Игрок в модели формы тела: один объект на форму, состояние анимации — своё у каждого игрока (номер сущности).
 * Клип движения выбирается так же, как у NPC: по сглаженной скорости тела, с запасом при смене аллюра; присед — свой клип.
 */
public final class PlayerFormAnimatable implements GeoReplacedEntity {
    private static final RawAnimation IDLE = RawAnimation.begin().thenLoop("misc.idle");
    private static final RawAnimation SNEAK_IDLE = RawAnimation.begin().thenLoop("misc.sneak_idle");
    private static final RawAnimation DEATH = RawAnimation.begin().thenPlayAndHold("misc.death");
    private static final float STOP = 0.2f, START = 0.4f, SWITCH_MARGIN = 0.12f;

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private final GeneForm form;
    private final AstartesConcepts.Variant variant;
    private final RawAnimation[] gaits;
    private final RawAnimation sneak;

    public PlayerFormAnimatable(GeneForm form) {
        this.form = form;
        this.variant = ClientGeneForms.variant(form);
        List<AstartesConcepts.Gait> g = variant.gaits();
        this.gaits = new RawAnimation[g.size()];
        for (int i = 0; i < g.size(); i++) gaits[i] = RawAnimation.begin().thenLoop(g.get(i).clip());
        this.sneak = variant.sneak() == null ? null : RawAnimation.begin().thenLoop(variant.sneak().clip());
    }

    public GeneForm form() {
        return form;
    }

    public AstartesConcepts.Variant variant() {
        return variant;
    }

    @Override
    public EntityType<?> getReplacingEntityType() {
        return EntityType.PLAYER;
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        // у Астартес позу собирает BipedMotion (assets/warpbound/motion); клипы GeckoLib — только у форм без файла движений
        if (!variant.overlay()) controllers.add(new AnimationController<>(this, "move", 4, this::move));
    }

    private PlayState move(AnimationState<PlayerFormAnimatable> state) {
        Entity e = state.getData(DataTickets.ENTITY);
        if (!(e instanceof Player p)) return PlayState.STOP;
        state.getController().setAnimationSpeed(1);
        if (p.isDeadOrDying()) return state.setAndContinue(DEATH);
        PlayerMotion.State s = PlayerMotion.update(p);
        float speed = s.speed;
        boolean moving = s.gait >= 0 ? speed > STOP : speed > START;
        boolean crouch = p.isCrouching() && sneak != null;
        if (!moving) {
            s.gait = -1;
            return state.setAndContinue(crouch ? SNEAK_IDLE : IDLE);
        }
        if (crouch) {
            s.gait = 0;
            state.getController().setAnimationSpeed(rate(speed, variant.sneak().speed()));
            return state.setAndContinue(sneak);
        }
        s.gait = pick(speed, s.gait);
        state.getController().setAnimationSpeed(rate(speed, variant.gaits().get(s.gait).speed()));
        return state.setAndContinue(gaits[s.gait]);
    }

    private int pick(float speed, int current) {
        List<AstartesConcepts.Gait> g = variant.gaits();
        int best = 0;
        float bestErr = Float.MAX_VALUE;
        for (int i = 0; i < g.size(); i++) {
            float err = Math.abs((float) Math.log(speed / g.get(i).speed()));
            if (err < bestErr) {
                bestErr = err;
                best = i;
            }
        }
        if (current >= 0 && current < g.size() && current != best) {
            float cur = Math.abs((float) Math.log(speed / g.get(current).speed()));
            if (cur - bestErr < SWITCH_MARGIN) return current;
        }
        return best;
    }

    private static double rate(float speed, float clipSpeed) {
        return Math.min(1.5, Math.max(0.6, speed / clipSpeed));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
