package dev.warpbound.client.player;

import dev.warpbound.Warpbound;
import dev.warpbound.client.entity.BipedLayers;
import dev.warpbound.client.entity.BipedMotion;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import software.bernie.geckolib.animation.AnimationProcessor;
import software.bernie.geckolib.animation.AnimationState;
import software.bernie.geckolib.constant.DataTickets;
import software.bernie.geckolib.model.GeoModel;

/**
 * Модель игрока в форме тела: те же geo и текстура, что у NPC. Позу собирает BipedMotion по состоянию игрока
 * (скорость, земля или воздух, присед, взмах, смерть), поверх — хват предмета, вздрагивание и взгляд.
 */
public final class PlayerFormModel extends GeoModel<PlayerFormAnimatable> {
    private final ResourceLocation geo, texture, animation;
    private final BipedMotion.Input input = new BipedMotion.Input();

    public PlayerFormModel(String model) {
        this.geo = Warpbound.id("geo/entity/" + model + ".geo.json");
        this.texture = Warpbound.id("textures/entity/" + model + ".png");
        this.animation = Warpbound.id("animations/entity/" + model + ".animation.json");
    }

    @Override
    public ResourceLocation getModelResource(PlayerFormAnimatable animatable) {
        return geo;
    }

    @Override
    public ResourceLocation getTextureResource(PlayerFormAnimatable animatable) {
        return texture;
    }

    @Override
    public ResourceLocation getAnimationResource(PlayerFormAnimatable animatable) {
        return animation;
    }

    @Override
    public void setCustomAnimations(PlayerFormAnimatable animatable, long instanceId, AnimationState<PlayerFormAnimatable> state) {
        Entity e = state.getData(DataTickets.ENTITY);
        if (!(e instanceof Player p)) return;
        float pt = state.getPartialTick();
        AnimationProcessor<PlayerFormAnimatable> proc = getAnimationProcessor();
        PlayerMotion.State s = PlayerMotion.update(p);
        BipedMotion.Input in = input;
        in.time = (p.tickCount + pt) / 20f;
        in.speed = s.speed;
        in.vy = (float) (p.getY() - p.yo);
        in.reset();
        in.onGround = p.onGround();
        in.crouching = p.isCrouching();
        boolean water = p.isInWater();
        if (p.isSleeping()) in.special = "sleep";
        else if (p.isPassenger()) in.special = "sit";
        else if (p.isFallFlying()) in.special = "glide";
        else if (p.isVisuallySwimming()) in.special = water ? "swim" : "crawl";
        else if (p.onClimbable() && !p.onGround()) in.special = "climb";
        else if (water && !p.onGround()) in.special = "tread";
        else if (p.getAbilities().flying && !p.onGround()) in.special = "fly";
        // взмах игрока — по ванильной кривой в PlayerActions (копание повторяет взмах без рывков), клип удара NPC здесь не нужен
        in.swingStart = -1000;
        in.deathSec = p.isDeadOrDying() ? (p.deathTime + pt) / 20f : -1;
        BipedMotion.animate(proc, animatable.form().model(), s.motion, in);
        if (!p.isAlive()) return;
        // держит предмет: рука чуть вперёд, локоть согнут сильнее — меч и кирка не уходят в бедро
        for (HumanoidArm arm : HumanoidArm.values()) {
            boolean main = p.getMainArm() == arm;
            if ((main ? p.getMainHandItem() : p.getOffhandItem()).isEmpty()) continue;
            String side = arm == HumanoidArm.RIGHT ? "_r" : "_l";
            BipedLayers.add(proc, "arm" + side, 7, 0, 0);
            BipedLayers.add(proc, "forearm" + side, 18, 0, 0);
        }
        BipedLayers.flinch(proc, p.hurtTime, p.hurtDuration, pt, s.flinches % 2 == 0);
        PlayerActions.apply(proc, p, s, pt);
        float yaw = Mth.wrapDegrees(Mth.rotLerp(pt, p.yHeadRotO, p.yHeadRot) - Mth.rotLerp(pt, p.yBodyRotO, p.yBodyRot));
        BipedLayers.look(proc, yaw, p.getViewXRot(pt));
    }
}
