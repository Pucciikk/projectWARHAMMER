package dev.warpbound.entity.anim;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.animation.AnimationController;
import software.bernie.geckolib.animation.PlayState;
import software.bernie.geckolib.animation.RawAnimation;

/**
 * Общий контракт анимаций для моделей GeckoLib (подробно — docs/content/models.md).
 * Имена анимаций одни на все модели, поэтому модель автора подменяет заглушку без правок кода.
 * <p>
 * Два контроллера: {@code main} — состояние (стоит, идёт, бежит, особые петли),
 * {@code action} — разовые действия (удар, выстрел, каст), которые сервер запускает через triggerAnim.
 */
public final class WarpAnim {
    public static final String MAIN = "main";
    public static final String ACTION = "action";

    public static final String SWING = "attack.swing";
    public static final String SHOOT = "attack.shoot";
    public static final String CAST = "attack.cast";
    public static final String INTERACT = "misc.interact";
    public static final String TRANSFORM = "misc.transform";
    public static final String DEPLOY_NAME = "misc.deploy";

    public static final RawAnimation IDLE = RawAnimation.begin().thenLoop("misc.idle");
    public static final RawAnimation WALK = RawAnimation.begin().thenLoop("move.walk");
    public static final RawAnimation RUN = RawAnimation.begin().thenLoop("move.run");
    public static final RawAnimation REPAIR = RawAnimation.begin().thenLoop("work.repair");
    public static final RawAnimation REST = RawAnimation.begin().thenPlayAndHold("misc.rest");
    public static final RawAnimation DEPLOY = RawAnimation.begin().thenPlayAndHold("misc.deploy");

    private WarpAnim() {
    }

    /** Стоит — idle, идёт — walk; бежит (в бою), если у модели есть move.run. */
    public static <T extends LivingEntity & GeoEntity> AnimationController<T> locomotion(T entity, boolean hasRun) {
        return new AnimationController<>(entity, MAIN, 4, state -> {
            if (!state.isMoving()) return state.setAndContinue(IDLE);
            boolean fighting = hasRun && entity instanceof Mob mob && mob.isAggressive();
            return state.setAndContinue(fighting ? RUN : WALK);
        });
    }

    /** Контроллер разовых действий: играет только то, что запустил сервер. */
    public static <T extends GeoEntity> AnimationController<T> actions(T entity, String... names) {
        AnimationController<T> controller = new AnimationController<>(entity, ACTION, 2, state -> PlayState.STOP);
        for (String name : names) controller.triggerableAnim(name, RawAnimation.begin().thenPlay(name));
        return controller;
    }
}
