package dev.warpbound.client.entity;

import dev.warpbound.entity.dreadnought.DreadnoughtEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.HierarchicalModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;

/**
 * Анимация процедурная: всё считается из фазы походки, поэтому шаг на экране
 * всегда совпадает с толчком скорости, пылью и тряской камеры.
 */
public class DreadnoughtModel extends HierarchicalModel<DreadnoughtEntity> {
    private final ModelPart root;
    private final ModelPart body;
    private final ModelPart legR, shinR, footR;
    private final ModelPart legL, shinL, footL;
    private final ModelPart waist, torso, head, armR, gun, armL, fist;

    public DreadnoughtModel(ModelPart root) {
        // entityCutout (с отсечением граней): пилот видит наружу сквозь стенки корпуса
        super(RenderType::entityCutout);
        this.root = root;
        this.body = root.getChild("body");
        this.legR = body.getChild("leg_r");
        this.shinR = legR.getChild("shin_r");
        this.footR = shinR.getChild("foot_r");
        this.legL = body.getChild("leg_l");
        this.shinL = legL.getChild("shin_l");
        this.footL = shinL.getChild("foot_l");
        this.waist = body.getChild("waist");
        this.torso = waist.getChild("torso");
        this.head = torso.getChild("head");
        this.armR = torso.getChild("arm_r");
        this.gun = armR.getChild("gun");
        this.armL = torso.getChild("arm_l");
        this.fist = armL.getChild("fist");
    }

    @Override
    public ModelPart root() {
        return root;
    }

    @Override
    public void setupAnim(DreadnoughtEntity e, float limbSwing, float limbSwingAmount, float ageInTicks,
                          float netHeadYaw, float headPitch) {
        root.getAllParts().forEach(ModelPart::resetPose);
        float pt = ageInTicks - e.tickCount;
        float g = Mth.lerp(pt, e.gaitO, e.gait);
        float amt = Mth.lerp(pt, e.strideO, e.stride);
        float run = Mth.lerp(pt, e.runO, e.run) * amt;

        // --- ноги: опорная нога равномерно уходит назад, переносимая — быстрой дугой с подъёмом колена.
        // На бегу опора короче, мах шире, колено выше
        Leg r = leg(g / Mth.TWO_PI, amt, run);
        Leg l = leg(g / Mth.TWO_PI + 0.5f, amt, run);
        r.apply(legR, shinR, footR);
        l.apply(legL, shinL, footL);
        // Высоту таза задаёт стоящая на земле нога: отсюда естественное покачивание вверх-вниз
        float drop = r.stance && l.stance ? Math.min(r.drop, l.drop) : r.stance ? r.drop : l.stance ? l.drop : Math.min(r.drop, l.drop);
        float jolt = e.jolt.get(pt);
        // На бегу таз ещё и подпрыгивает дважды за цикл — на каждом толчке
        body.y += drop - jolt * 3.0f - run * Math.abs(Mth.sin(g)) * 2.5f;

        // --- таз: кренится к опорной ноге и поворачивается вслед за выносимой.
        // Ноги и ступни компенсируют крен, чтобы стоять отвесно; «талия» гасит
        // качание, поэтому таз ходит под саркофагом заметно, а сам корпус — мягко.
        float shift = Mth.cos(g - 0.6f * Mth.PI) * amt;
        float roll = shift * (0.07f + 0.05f * run);
        float hipYaw = Mth.cos(g) * (0.10f + 0.06f * run) * amt;
        body.zRot = roll;
        body.yRot = hipYaw;
        legR.zRot = -roll;
        legL.zRot = -roll;
        waist.zRot = -roll * 0.75f;
        waist.yRot = -hipYaw * 0.8f;
        waist.x -= shift * 0.8f;
        torso.x -= shift * 0.8f;
        // Бег: корпус пошатывается из стороны в сторону с запаздыванием и клюёт на каждом шаге
        torso.zRot = -shift * 0.02f + Mth.sin(g - 0.9f) * 0.05f * run;
        // Плечи закручиваются навстречу шагу
        float twist = -hipYaw * 0.3f;

        // --- инерция: откидывается при разгоне, клюёт при торможении и от удара пятки
        float lean = e.lean.get(pt);
        torso.xRot = 0.04f * amt + 0.10f * run + lean * 0.10f - jolt * 0.05f
                + Mth.sin(2f * g - 0.8f) * 0.035f * run;
        torso.y += Mth.sin(ageInTicks * 0.06f) * 0.5f;          // дыхание реактора

        float bodyYaw = Mth.rotLerp(pt, e.yBodyRotO, e.yBodyRot);
        float torsoYaw = Mth.rotLerp(pt, e.torsoYawO, e.torsoYaw);
        torso.yRot = Mth.wrapDegrees(torsoYaw - bodyYaw) * Mth.DEG_TO_RAD + twist;

        // --- пилот, прицел, кабина
        Entity pilot = e.getFirstPassenger();
        // Пилот изнутри не видит стенок саркофага и головы: только руки и ноги машины
        Minecraft mc = Minecraft.getInstance();
        boolean cockpit = pilot != null && pilot == mc.getCameraEntity() && mc.options.getCameraType().isFirstPerson();
        torso.skipDraw = cockpit;
        head.visible = !cockpit;
        float pitch = (pilot != null ? pilot.getViewXRot(pt) : headPitch) * Mth.DEG_TO_RAD;
        head.xRot = Mth.clamp(pitch, -0.4f, 0.5f);
        gun.xRot = Mth.clamp(pitch, -0.6f, 0.7f) - jolt * 0.08f;
        if (pilot == null) {
            // Без пилота сервоприводы «ищут» цель: пушка чуть подёргивается
            head.yRot = Mth.sin(ageInTicks * 0.021f) * 0.35f;
            gun.yRot = Mth.sin(ageInTicks * 0.07f) * 0.02f + Mth.sin(ageInTicks * 0.19f) * 0.012f;
        }

        // --- руки: тяжёлый кулак раскачивается и отстаёт при повороте, пушка почти неподвижна
        float lag = e.armLag.get(pt);
        armL.xRot = Mth.sin(g) * (0.10f + 0.16f * run) * amt - jolt * 0.10f;
        armL.yRot = lag * 0.14f;
        fist.xRot = -0.12f + Math.abs(Mth.cos(g)) * 0.05f * amt - jolt * 0.08f;
        armR.xRot = -Mth.sin(g) * (0.04f + 0.08f * run) * amt;
        armR.yRot = lag * 0.08f;
        armR.zRot = 0.02f;
        armL.zRot = -0.02f;
    }

    // Длины звеньев ноги в единицах модели (бедро 56 → колено 34 → голеностоп 10)
    private static final float THIGH = 22f;
    private static final float SHIN = 24f;
    /** Поза покоя: лёгкий присед, колени вперёд, как у референсов. */
    private static final float REST_THIGH = -0.16f;
    private static final float REST_SHIN = 0.32f;
    private static final float SWING = 0.42f;   // вместе с STRIDE подобрано так, чтобы опорная ступня не скользила

    private record Leg(float thigh, float shin, float foot, float drop, boolean stance) {
        void apply(ModelPart t, ModelPart s, ModelPart f) {
            t.xRot = thigh;
            s.xRot = shin;
            f.xRot = foot;
        }
    }

    private static Leg leg(float cycle, float amt, float run) {
        float p = cycle - Mth.floor(cycle);
        float stanceLen = Mth.lerp(run, DreadnoughtEntity.STANCE, DreadnoughtEntity.RUN_STANCE);
        // мах растёт вместе с длиной шага, чтобы опорная ступня не скользила
        float amp = SWING * (1f + (DreadnoughtEntity.RUN_STRIDE - 1f) * run);
        float swing;
        float knee;
        float toe = 0f;
        boolean stance = p < stanceLen;
        if (stance) {
            float u = p / stanceLen;
            swing = amp - 2f * amp * u;
            knee = (0.12f + 0.18f * run) * (float) Math.exp(-u * 10f);   // колено гасит удар пятки
        } else {
            float q = (p - stanceLen) / (1f - stanceLen);
            float eased = q * q * (3f - 2f * q);
            swing = -amp + 2f * amp * eased;
            knee = Mth.sin(q * Mth.PI) * (0.55f + 0.4f * run);
            toe = Mth.sin(q * Mth.PI) * (0.15f + 0.1f * run);
        }
        // Отрицательный поворот по X выносит ногу вперёд
        float thigh = REST_THIGH - swing * amt;
        float shin = REST_SHIN + knee * amt;
        float foot = -(thigh + shin) - toe * amt;
        float drop = THIGH + SHIN - (THIGH * Mth.cos(thigh) + SHIN * Mth.cos(thigh + shin));
        return new Leg(thigh, shin, foot, drop, stance || amt < 0.05f);
    }
}
