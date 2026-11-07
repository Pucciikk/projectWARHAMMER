package dev.warpbound.client.entity;

import dev.warpbound.Warpbound;
import dev.warpbound.entity.astartes.BipedConceptEntity;
import net.minecraft.util.Mth;
import software.bernie.geckolib.animation.AnimationProcessor;
import software.bernie.geckolib.animation.AnimationState;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;

import java.util.HashMap;
import java.util.Map;

/**
 * Модель NPC Астартес и Громового воина. Если у модели есть файл движений (assets/warpbound/motion), позу целиком собирает BipedMotion:
 * своя фаза шага, смешивание аллюров, воздух, удар, смерть. Поверх — вздрагивание и взгляд. Без файла работают клипы GeckoLib (Громовой воин пока).
 */
public final class BipedConceptModel extends DefaultedEntityGeoModel<BipedConceptEntity> {
    private final Map<Integer, BipedMotion.State> states = new HashMap<>();
    private final BipedMotion.Input input = new BipedMotion.Input();

    public BipedConceptModel(String model) {
        super(Warpbound.id(model));
    }

    @Override
    public void setCustomAnimations(BipedConceptEntity entity, long instanceId, AnimationState<BipedConceptEntity> state) {
        float pt = state.getPartialTick();
        AnimationProcessor<BipedConceptEntity> p = getAnimationProcessor();
        if (entity.variant().overlay()) {
            entity.updateSpeed();
            if (entity.isRemoved()) states.remove(entity.getId());
            BipedMotion.Input in = input;
            in.reset();
            in.time = (entity.tickCount + pt) / 20f;
            in.speed = entity.bodySpeed();
            in.vy = (float) (entity.getY() - entity.yo);
            in.onGround = entity.onGround() || entity.isNoAi();                // у мобов без ИИ Minecraft не обновляет «на земле»
            if (entity.isPassenger()) in.special = "sit";
            else if (entity.onClimbable() && !entity.onGround()) in.special = "climb";
            else if (entity.isInWater() && !entity.onGround()) in.special = "tread";
            in.crouching = entity.isCrouching();
            // клип на месте ({NoAI:1b,Clip:"move.walk"}): изображаем скорость этого аллюра, ноги идут как при ходьбе
            String clip = entity.forcedClip();
            if (!clip.isEmpty()) {
                for (var g : entity.variant().gaits()) if (g.clip().equals(clip)) in.speed = g.speed();
                if (entity.variant().sneak() != null && entity.variant().sneak().clip().equals(clip)) {
                    in.speed = entity.variant().sneak().speed();
                    in.crouching = true;
                }
                if (clip.equals("misc.idle")) in.speed = 0;
            }
            in.swingStart = entity.meleeStart() / 20f;
            in.swingLeft = entity.meleeLeft();
            in.deathSec = entity.isDeadOrDying() ? (entity.deathTime + pt) / 20f : -1;
            BipedMotion.animate(p, entity.variant().model(), states.computeIfAbsent(entity.getId(), i -> new BipedMotion.State()), in);
            if (entity.isAlive()) BipedLayers.flinch(p, entity.hurtTime, entity.hurtDuration, pt, (entity.getId() + entity.flinchCount()) % 2 == 0);
        }
        if (!entity.isAlive()) return;
        float yaw = Mth.wrapDegrees(Mth.rotLerp(pt, entity.yHeadRotO, entity.yHeadRot) - Mth.rotLerp(pt, entity.yBodyRotO, entity.yBodyRot));
        BipedLayers.look(p, yaw, entity.getViewXRot(pt));
    }
}
