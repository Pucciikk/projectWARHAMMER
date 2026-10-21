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
    private final ModelPart torso, head, armR, gun, armL, fist;

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
        this.torso = body.getChild("torso");
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
        float s = Mth.sin(g);
        float c = Mth.cos(g);

        // Ноги: бедро качается, колено сгибается только когда нога идёт вперёд по воздуху
        legR.xRot = -s * 0.42f * amt;
        legL.xRot = s * 0.42f * amt;
        float liftR = Math.max(0f, c) * amt;
        float liftL = Math.max(0f, -c) * amt;
        shinR.xRot = liftR * 0.55f;
        shinL.xRot = liftL * 0.55f;
        footR.xRot = -(legR.xRot + shinR.xRot) * 0.85f;
        footL.xRot = -(legL.xRot + shinL.xRot) * 0.85f;

        // Корпус проседает в момент удара ступни (|sin| = 1) и раскачивается с боку на бок
        float impact = Math.abs(s);
        body.y += impact * impact * 3.2f * amt;   // модель в масштабе 0.5: единицы вдвое мельче
        body.zRot = s * 0.035f * amt;
        torso.xRot = 0.05f * amt + impact * 0.025f * amt;
        // Дыхание реактора на месте
        torso.y += Mth.sin(ageInTicks * 0.06f) * 0.5f;

        // Корпус крутится отдельно от ног
        float bodyYaw = Mth.rotLerp(pt, e.yBodyRotO, e.yBodyRot);
        float torsoYaw = Mth.rotLerp(pt, e.torsoYawO, e.torsoYaw);
        torso.yRot = Mth.wrapDegrees(torsoYaw - bodyYaw) * Mth.DEG_TO_RAD;

        // Пушка и голова смотрят туда же, куда пилот (или ИИ) по вертикали
        Entity pilot = e.getFirstPassenger();
        // Пилот изнутри не видит стенок саркофага и головы: только руки и ноги машины
        Minecraft mc = Minecraft.getInstance();
        boolean cockpit = pilot != null && pilot == mc.getCameraEntity() && mc.options.getCameraType().isFirstPerson();
        torso.skipDraw = cockpit;
        head.visible = !cockpit;
        float pitch = (pilot != null ? pilot.getViewXRot(pt) : headPitch) * Mth.DEG_TO_RAD;
        head.xRot = Mth.clamp(pitch, -0.4f, 0.5f);
        gun.xRot = Mth.clamp(pitch, -0.6f, 0.7f);

        // Руки: тяжёлый кулак отстаёт, пушка почти неподвижна
        armL.xRot = s * 0.12f * amt;
        fist.xRot = -0.15f + Math.abs(c) * 0.06f * amt;
        armR.xRot = -s * 0.05f * amt;
        armR.zRot = 0.02f;
        armL.zRot = -0.02f;
    }
}
