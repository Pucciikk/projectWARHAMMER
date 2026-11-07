package dev.warpbound.client.player;

import dev.warpbound.gun.GunItem;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.CrossbowItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import software.bernie.geckolib.animation.AnimationProcessor;
import software.bernie.geckolib.cache.object.GeoBone;

/**
 * Действия рук игрока-Астартес поверх позы движения: взмах (удар, копание, установка блока) и использование предметов
 * (щит, лук, арбалет, трезубец, подзорная труба, рог, еда и питьё, кисть, оружие мода). Набор — как у ванильной модели
 * (HumanoidModel.ArmPose), позы свои. Каждая рука плавно уходит в позу действия и обратно, прицел — по взгляду.
 * <p>
 * Углы в позах — в осях скрипта Blender (biped_motion.py): swing < 0 — рука вперёд, elbow > 0 — локоть согнут,
 * abduct > 0 — рука в сторону, turn > 0 — рука поворачивается внутрь вокруг вертикали (у вытянутой руки — к середине).
 */
public final class PlayerActions {
    private static final float DEG = Mth.DEG_TO_RAD;

    /** Поза руки: плечо (swing, abduct, turn), локоть, кисть; yaw — поворот за взглядом (вправо > 0), одинаковый для обеих рук. */
    private record ArmPose(float swing, float abduct, float turn, float elbow, float wrist, float yaw) {
        ArmPose(float swing, float abduct, float turn, float elbow, float wrist) {
            this(swing, abduct, turn, elbow, wrist, 0);
        }
    }

    private PlayerActions() {
    }

    /** Плавные веса действий: по руке, своё последнее действие на затухание. */
    public static final class State {
        final float[] weight = new float[2];
        final ArmPose[] last = new ArmPose[2];
        float lastTime = Float.NaN;
    }

    public static void apply(AnimationProcessor<?> p, Player player, PlayerMotion.State motion, float pt) {
        State s = motion.actions;
        float time = (player.tickCount + pt) / 20f;
        float dt = Float.isNaN(s.lastTime) ? 0 : Mth.clamp(time - s.lastTime, 0, 0.1f);
        s.lastTime = time;
        float pitch = Mth.clamp(player.getViewXRot(pt), -60, 70);
        float yaw = Mth.clamp(Mth.wrapDegrees(Mth.rotLerp(pt, player.yHeadRotO, player.yHeadRot) - Mth.rotLerp(pt, player.yBodyRotO, player.yBodyRot)), -60, 60);
        ArmPose[] target = new ArmPose[2];          // 0 — правая, 1 — левая
        float lean = 0;

        // ---- использование предмета
        if (player.isUsingItem()) {
            int using = side(player, player.getUsedItemHand());
            ItemStack stack = player.getUseItem();
            float used = (player.getTicksUsingItem() + pt) / 20f;
            UseAnim anim = stack.getUseAnimation();
            switch (anim) {
                case BLOCK -> target[using] = new ArmPose(-54 + pitch * 0.3f, 0, 30, 42, -6, yaw * 0.5f);          // ваниль: −54°, внутрь 30°
                case BOW -> {
                    float draw = Mth.clamp(used / 1.0f, 0, 1);
                    target[using] = aim(pitch, yaw, 4, 0);
                    target[1 - using] = aim(pitch, yaw, 96 + 30 * draw, 28 + 6 * draw);
                }
                case SPEAR -> {
                    target[using] = new ArmPose(-168 + Math.min(0, pitch) * 0.3f, 10, 0, 26, 0);
                    lean = -6;
                }
                case CROSSBOW -> {
                    float k = (float) Math.sin(used * 7);
                    target[using] = new ArmPose(-58, -4, 22, 36, -6);
                    target[1 - using] = new ArmPose(-34 - 8 * k, -2, 30, 104 + 10 * k, -6);
                }
                case SPYGLASS -> target[using] = new ArmPose(-106 + pitch * 0.8f, -6, 16, 52, -6, yaw * 0.75f);   // ваниль: −110° от взгляда, внутрь 15°
                case TOOT_HORN -> target[using] = new ArmPose(-84 + pitch * 0.6f, -6, 30, 62, -6, yaw * 0.6f);     // ваниль: −85°, внутрь 30°
                case EAT, DRINK -> {
                    float bob = (float) Math.sin(used * 21) * 6;
                    target[using] = new ArmPose(-58 + bob, -8, 36, 104 + bob, -6);
                    if (anim == UseAnim.DRINK) lean = -4;
                }
                case BRUSH -> {
                    float k = (float) Math.sin(used * 12);
                    target[using] = new ArmPose(-48 + pitch * 0.4f, -4, 18 + 14 * k, 40, -8);
                }
                default -> {
                }
            }
        }
        // ---- держит заряженный арбалет или оружие мода: обе руки на изготовке по взгляду
        for (InteractionHand hand : InteractionHand.values()) {
            ItemStack stack = player.getItemInHand(hand);
            int i = side(player, hand);
            if (target[i] != null || stack.isEmpty()) continue;
            boolean rifle = stack.getItem() instanceof GunItem || (stack.getItem() instanceof CrossbowItem && CrossbowItem.isCharged(stack));
            if (!rifle) continue;
            target[i] = aim(pitch, yaw, 24, 17);                         // ваниль: внутрь 17°, оружие у лица
            if (target[1 - i] == null && player.getItemInHand(hand == InteractionHand.MAIN_HAND ? InteractionHand.OFF_HAND : InteractionHand.MAIN_HAND).isEmpty())
                target[1 - i] = aim(pitch + 8, yaw, 58, 36);                 // вторая рука под цевьём: ваниль — внутрь 34°
        }

        for (int i = 0; i < 2; i++) {
            if (target[i] != null) s.last[i] = target[i];
            s.weight[i] += ((target[i] != null ? 1 : 0) - s.weight[i]) * (1 - (float) Math.exp(-dt / 0.08f));
            if (s.last[i] != null && s.weight[i] > 0.002f) pose(p, i == 0 ? "r" : "l", i == 0 ? -1 : 1, s.last[i], s.weight[i]);
        }
        if (lean != 0) add(p, "chest", -lean, 0, 0);

        // ---- взмах: удар, копание, установка блока. Кривая как у ванильной руки — начинается и кончается в покое,
        // поэтому взмахи копания идут друг за другом без рывков. Астартес бьёт корпусом: разворот сильнее ванильного.
        float a = player.getAttackAnim(pt);
        if (a > 0) {
            int i = side(player, player.swingingArm == null ? InteractionHand.MAIN_HAND : player.swingingArm);
            String sfx = i == 0 ? "_r" : "_l";
            float sign = i == 0 ? 1 : -1;
            float f = 1 - a;
            f = 1 - f * f * f * f;
            float s1 = Mth.sin(f * Mth.PI), s2 = Mth.sin(a * Mth.PI);
            float body = Mth.sin(Mth.sqrt(a) * Mth.TWO_PI) * 14;
            float raise = s1 * 68 + s2 * (40 - pitch) * 0.75f;
            add(p, "chest", 3 * s2, -sign * body, 0);
            add(p, "abdomen", 1.5f * s2, -sign * body * 0.4f, 0);
            add(p, "arm" + sfx, raise, -sign * body * 1.4f, -sign * 10 * s2);
            add(p, "forearm" + sfx, 26 * s1 - 30 * s2, 0, 0);
            add(p, "pad" + sfx, raise * 0.2f, 0, 0);
        }
    }

    /** Рука на прицел: вперёд по взгляду, поворот за головой. Грудь уже взяла пятую часть наклона и четверть поворота (BipedLayers.look). */
    private static ArmPose aim(float pitch, float yaw, float elbow, float turnIn) {
        return new ArmPose(-90 + pitch * 0.8f, 0, turnIn, elbow, 0, yaw * 0.75f);
    }

    private static int side(Player player, InteractionHand hand) {
        HumanoidArm arm = hand == InteractionHand.MAIN_HAND ? player.getMainArm() : player.getMainArm().getOpposite();
        return arm == HumanoidArm.RIGHT ? 0 : 1;
    }

    /** Сместить руку к позе с весом w. sign: 1 — левая, −1 — правая (как в скриптах Blender). */
    private static void pose(AnimationProcessor<?> p, String s, float sign, ArmPose a, float w) {
        // Blender: плечо (swing, sign·twist, −sign·out), twist < 0 — наружу, out > 0 — внутрь; GeckoLib: (−x, z, y). Взгляд вправо — поворот по часовой (Z < 0)
        lerp(p.getBone("arm_" + s), -a.swing(), -sign * a.turn() - a.yaw(), -sign * a.abduct(), w);
        lerp(p.getBone("forearm_" + s), a.elbow(), 0, 0, w);
        lerp(p.getBone("hand_" + s), -a.wrist(), 0, 0, w);
    }

    private static void lerp(GeoBone b, float x, float y, float z, float w) {
        if (b == null) return;
        b.setRotX(Mth.lerp(w, b.getRotX(), x * DEG));
        b.setRotY(Mth.lerp(w, b.getRotY(), y * DEG));
        b.setRotZ(Mth.lerp(w, b.getRotZ(), z * DEG));
    }

    private static void add(AnimationProcessor<?> p, String name, float x, float y, float z) {
        GeoBone b = p.getBone(name);
        if (b == null) return;
        b.setRotX(b.getRotX() + x * DEG);
        b.setRotY(b.getRotY() + y * DEG);
        b.setRotZ(b.getRotZ() + z * DEG);
    }
}
