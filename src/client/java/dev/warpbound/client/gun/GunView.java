package dev.warpbound.client.gun;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import dev.warpbound.Warpbound;
import dev.warpbound.core.WarpboundParticles;
import dev.warpbound.gun.GunItem;
import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.PlayerModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.player.PlayerRenderer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import org.joml.Vector3f;

/**
 * Вид оружия от первого лица. Складывается из бедра и прицела, ходьбы, запаздывания за мышью, пружин отдачи и клипов из Blender.
 * Руки — настоящие руки игрока со скином: кости arm_r и arm_l только говорят, где им быть.
 */
public final class GunView {
    private static final float ARM_SCALE = 0.7f, ARM_STRETCH = 2.1f;
    private static final float[] VIEW = new float[6], SEC = new float[1];

    // ---- пружины отдачи: x — смещение, v — скорость
    private static float backX, backV, pitchX, pitchV, rollX, rollV, sideX, sideV;
    // ---- подъём камеры: сколько ещё прибавить за кадры и сколько вернуть
    private static float camUpLeft, camSideLeft, camReturn;
    private static float flashLeft;
    private static float flashSpin;
    /** Для снимков автотеста: вспышка живёт дольше одного кадра. */
    static boolean holdFlash;
    // ---- запаздывание за мышью
    private static float swayYaw, swayPitch, lastYaw, lastPitch;
    private static long lastNanos;
    /** Дуло и окно выброса в пространстве камеры с прошлого кадра: от них стартуют снаряд, гильза и дым. */
    private static final Vector3f MUZZLE_VIEW = new Vector3f(0.2f, -0.2f, -0.8f), EJECT_VIEW = new Vector3f(0.2f, -0.1f, -0.4f);

    private GunView() {
    }

    /** Толчок на выстрел: откуда и насколько зависит от оружия. */
    static void onShot(GunVisual v, LocalPlayer player) {
        var r = player.getRandom();
        backV += v.kickBack() * 28;
        pitchV += v.kickPitch() * (22 + r.nextFloat() * 8);
        rollV += v.kickRoll() * (r.nextBoolean() ? 18 : -18);
        sideV += (r.nextFloat() - 0.5f) * v.kickRoll() * 16;
        camUpLeft += v.camUp() * (0.85f + r.nextFloat() * 0.3f);
        camSideLeft += (r.nextFloat() - 0.5f) * v.camSide();
        flashLeft = 0.055f;
                flashSpin = r.nextFloat() * 360;
        Vec3 m = muzzleWorld(Minecraft.getInstance(), 1f);
        var level = player.level();
        if (v.casing()) {
            Vec3 e = viewToWorld(Minecraft.getInstance(), EJECT_VIEW);
            Vec3 side = Vec3.directionFromRotation(0, player.getYRot() + 90);
            level.addParticle(WarpboundParticles.GUN_CASING, e.x, e.y, e.z, side.x * 0.13 + player.getDeltaMovement().x, 0.14, side.z * 0.13 + player.getDeltaMovement().z);
        }
    }

    private static float spring(float dt, float stiffness, float damping, boolean pitch, float x, float v, java.util.function.Consumer<float[]> set) {
        float[] s = {x, v};
        float a = -stiffness * s[0] - damping * s[1];
        s[1] += a * dt;
        s[0] += s[1] * dt;
        set.accept(s);
        return s[0];
    }

    private static void updateSprings(float dt, float aim) {
        // шаг ограничен: иначе на низком FPS пружины разлетаются
        dt = Math.min(dt, 0.033f);
        spring(dt, 220, 22, false, backX, backV, s -> {
            backX = s[0];
            backV = s[1];
        });
        spring(dt, 170, 16, true, pitchX, pitchV, s -> {
            pitchX = s[0];
            pitchV = s[1];
        });
        spring(dt, 150, 15, false, rollX, rollV, s -> {
            rollX = s[0];
            rollV = s[1];
        });
        spring(dt, 180, 18, false, sideX, sideV, s -> {
            sideX = s[0];
            sideV = s[1];
        });
        if (!holdFlash) flashLeft = Math.max(0, flashLeft - dt);
    }

    /** Подъём камеры растягиваем на несколько кадров, потом часть возвращаем: ствол заметно ведёт, но прицел не улетает. */
    private static void applyCameraRecoil(LocalPlayer player, float dt) {
        float take = Math.min(1, dt * 26);
        float up = camUpLeft * take, side = camSideLeft * take;
        if (Math.abs(up) > 0.0005f || Math.abs(side) > 0.0005f) {
            player.setXRot(Mth.clamp(player.getXRot() - up, -90, 90));
            player.setYRot(player.getYRot() + side);
            camUpLeft -= up;
            camSideLeft -= side;
            camReturn += up * 0.55f;
        } else if (camReturn > 0) {
            float back = Math.min(camReturn, dt * 2.2f);
            player.setXRot(Mth.clamp(player.getXRot() + back, -90, 90));
            camReturn -= back;
        }
    }

    /** Весь вид от первого лица. Заменяет ванильную руку с предметом. */
    public static void render(AbstractClientPlayer player, float partialTick, ItemStack stack, PoseStack pose, MultiBufferSource buffers, int light) {
        Minecraft mc = Minecraft.getInstance();
        if (!(stack.getItem() instanceof GunItem gun)) return;
        GunVisual v = GunVisual.of(gun);
        long nanos = System.nanoTime();
        float dt = lastNanos == 0 ? 0.016f : (nanos - lastNanos) / 1e9f;
        lastNanos = nanos;
        updateSprings(dt, GunClient.aim);
        if (player instanceof LocalPlayer local && mc.screen == null) applyCameraRecoil(local, dt);

        float aim = smooth(GunClient.aim), run = smooth(GunClient.sprint);
        // запаздывание за мышью: оружие тянется за поворотом и догоняет
        float yaw = player.getViewYRot(partialTick), pitch = player.getViewXRot(partialTick);
        float dYaw = Mth.wrapDegrees(yaw - lastYaw), dPitch = pitch - lastPitch;
        lastYaw = yaw;
        lastPitch = pitch;
        float swayK = Math.min(1, dt * 9);
        swayYaw += (Mth.clamp(dYaw, -6, 6) - swayYaw) * swayK;
        swayPitch += (Mth.clamp(dPitch, -6, 6) - swayPitch) * swayK;

        // ---- шаг: две дуги на цикл, у прицела почти не качает
        float walk = player.walkDist + (player.walkDist - player.walkDistO) * partialTick;
        float moveAmt = Math.min(1, Mth.lerp(partialTick, player.oBob, player.bob) * 5.5f);
        float bobX = Mth.sin(walk * Mth.PI * 1.1f) * 0.014f * moveAmt * (1 - aim * 0.88f) * (1 + run * 1.5f);
        float bobY = -Math.abs(Mth.cos(walk * Mth.PI * 1.1f)) * 0.018f * moveAmt * (1 - aim * 0.88f) * (1 + run * 1.8f);
        float time = player.tickCount + partialTick;
        // дыхание: совсем слабое движение, чтобы оружие не казалось приклеенным к экрану
        float breathY = Mth.sin(time * 0.05f) * 0.0035f * (1 - aim * 0.65f);
        float breathX = Mth.cos(time * 0.037f) * 0.002f * (1 - aim * 0.65f);

        float crouch = player.isCrouching() ? 0.012f * (1 - aim) : 0;
        float x = Mth.lerp(aim, v.hipX(), 0) + bobX + breathX - swayYaw * 0.0026f * (1 - aim * 0.6f) + sideX * 0.012f;
        float y = Mth.lerp(aim, v.hipY(), -v.sightZ() * v.scale()) + bobY + breathY + swayPitch * 0.0022f * (1 - aim * 0.6f) - crouch;
        float z = Mth.lerp(aim, v.hipZ(), v.aimZ()) + backX * 0.9f;

        // ---- клип двигает оружие целиком (псевдокость _view)
        GunClips.Clip clip = GunClient.activeClip(v, mc, SEC);
        boolean hasView = clip.sample("_view", SEC[0], VIEW);
        float vx = hasView ? VIEW[0] : 0, vy = hasView ? VIEW[1] : 0, vz = hasView ? VIEW[2] : 0;
        float rx = hasView ? VIEW[3] : 0, ry = hasView ? VIEW[4] : 0, rz = hasView ? VIEW[5] : 0;

        pose.pushPose();
        pose.translate(x - vx, y + vz, z + vy);
        // бег: оружие опущено и развёрнуто, как при переноске
        pose.mulPose(Axis.YP.rotationDegrees(Mth.lerp(aim, -2.5f, 0) + run * 34 - swayYaw * 0.55f * (1 - aim * 0.7f) + rz));
        pose.mulPose(Axis.XP.rotationDegrees(Mth.lerp(aim, 1.5f, 0) - run * 22 + swayPitch * 0.55f * (1 - aim * 0.7f) + pitchX * 0.9f - rx));
        pose.mulPose(Axis.ZP.rotationDegrees(run * -14 + swayYaw * 0.35f * (1 - aim * 0.7f) + rollX + ry));
        pose.translate(0, -run * 0.05f, -run * 0.02f);
        pose.scale(v.scale(), v.scale(), v.scale());

        int shown = flashLeft > 0 ? LightTexture.FULL_BRIGHT : light;
        GunRenderer renderer = GunRenderer.of(v.model());
        pose.pushPose();
        // GeckoLib сдвигает предмет к середине блока: здесь модель должна стоять в своём начале координат
        pose.translate(-0.5f, -0.51f, -0.5f);
        GunRenderer.viewPass = true;
        GunRenderer.CAPTURED.clear();
        renderer.renderByItem(stack, ItemDisplayContext.FIRST_PERSON_RIGHT_HAND, pose, buffers, shown, OverlayTexture.NO_OVERLAY);
        GunRenderer.viewPass = false;
        pose.popPose();
        // руки и вспышка — уже по позициям костей
        renderArm(player, buffers, shown, "arm_r", true);
        renderArm(player, buffers, shown, "arm_l", false);
        Matrix4f muzzle = GunRenderer.CAPTURED.get("muzzle");
        Matrix4f eject = GunRenderer.CAPTURED.get("eject");
        // за пределами этого метода матрицы не живут: координаты камеры считаем сейчас, с учётом обратного вида
        if (muzzle != null) muzzle.getTranslation(MUZZLE_VIEW);
        if (eject != null) eject.getTranslation(EJECT_VIEW);
        if (flashLeft > 0 && muzzle != null) {
            PoseStack fp = new PoseStack();
            fp.last().pose().set(muzzle);
            fp.last().normal().set(GunRenderer.CAPTURED_NORMAL.get("muzzle"));
            ShotMesh.flash(buffers, fp.last(), gun.mechanics.kind() == GunItem.Kind.LAS, v.flash(), Math.min(1, flashLeft / 0.055f), flashSpin);
        }
        if (holdFlash && GunRenderer.CAPTURED.isEmpty()) Warpbound.LOG.warn("gun: кости-точки не захвачены");
        pose.popPose();
    }

    private static float smooth(float k) {
        return k * k * (3 - 2 * k);
    }

    @SuppressWarnings("unchecked")
    static void renderArm(AbstractClientPlayer player, MultiBufferSource buffers, int light, String name, boolean right) {
        Matrix4f m = GunRenderer.CAPTURED.get(name);
        Matrix3f n = GunRenderer.CAPTURED_NORMAL.get(name);
        if (m == null) return;
        Minecraft mc = Minecraft.getInstance();
        PlayerRenderer renderer = (PlayerRenderer) mc.getEntityRenderDispatcher().getRenderer(player);
        PlayerModel<AbstractClientPlayer> model = renderer.getModel();
        ModelPart arm = right ? model.rightArm : model.leftArm, sleeve = right ? model.rightSleeve : model.leftSleeve;
        // руку ставим сами; значения нужны обратно, потому что та же модель рисует игрока в мире
        float ax = arm.x, ay = arm.y, az = arm.z, rx = arm.xRot, ry = arm.yRot, rz = arm.zRot;
        float sx = sleeve.x, sy = sleeve.y, sz = sleeve.z, srx = sleeve.xRot, sry = sleeve.yRot, srz = sleeve.zRot;
        PoseStack p = new PoseStack();
        p.last().pose().set(m);
        p.last().normal().set(n);
        p.scale(ARM_SCALE, ARM_SCALE, ARM_SCALE);
        // рука модели идёт сверху вниз (+Y к кисти): разворачиваем так, чтобы кисть была в точке кости, а локоть уходил к стрелку
        p.mulPose(Axis.XP.rotationDegrees(-90));
        // кисть в середине ладони: у модели игрока это y = 11, x около ±1 пикселя
        p.translate(right ? 1 / 16f : -1 / 16f, -11 / 16f * ARM_STRETCH, 0);
        // модель руки короче настоящей: без растяжки за кистью виден её срез, а не плечо за краем экрана
        p.scale(0.82f, ARM_STRETCH, 0.82f);
        for (ModelPart part : new ModelPart[]{arm, sleeve}) {
            part.setPos(0, 0, 0);
            part.setRotation(0, 0, 0);
        }
        ResourceLocation skin = player.getSkin().texture();
        VertexConsumer vc = buffers.getBuffer(RenderType.entitySolid(skin));
        arm.render(p, vc, light, OverlayTexture.NO_OVERLAY);
        sleeve.render(p, buffers.getBuffer(RenderType.entityTranslucent(skin)), light, OverlayTexture.NO_OVERLAY);
        arm.setPos(ax, ay, az);
        arm.setRotation(rx, ry, rz);
        sleeve.setPos(sx, sy, sz);
        sleeve.setRotation(srx, sry, srz);
    }

    // ---------------------------------------------------------------- из камеры в мир

    /** У рук своя ширина угла зрения (70°), у мира — настройка игрока: координаты надо пересчитать, чтобы точка осталась на том же месте экрана. */
    static Vec3 viewToWorld(Minecraft mc, Vector3f v) {
        Camera cam = mc.gameRenderer.getMainCamera();
        double worldFov = mc.options.fov().get() * player(mc);
        float k = (float) (Math.tan(Math.toRadians(worldFov) / 2) / Math.tan(Math.toRadians(70) / 2));
        // матрица рук в 1.21 уже содержит обратный поворот камеры: v — смещение от камеры в осях мира, поворачивать его ещё раз нельзя.
        // раскладываем по векторам камеры только затем, чтобы поправка угла зрения легла на боковые оси, а не на глубину
        Vector3f look = cam.getLookVector(), up = cam.getUpVector(), left = cam.getLeftVector();
        float ahead = v.dot(look), high = v.dot(up) * k, side = -v.dot(left) * k;
        return cam.getPosition().add(
                look.x() * ahead + up.x() * high - left.x() * side,
                look.y() * ahead + up.y() * high - left.y() * side,
                look.z() * ahead + up.z() * high - left.z() * side);
    }

    private static double player(Minecraft mc) {
        return mc.player == null ? 1 : mc.player.getFieldOfViewModifier();
    }

    static Vec3 muzzleWorld(Minecraft mc, float partial) {
        return viewToWorld(mc, MUZZLE_VIEW);
    }

    /** Дуло чужого оружия и своего в виде от третьего лица: по голове и направлению взгляда, точнее не нужно. */
    static Vec3 approxMuzzle(Entity shooter, float partial) {
        Vec3 eye = shooter.getEyePosition(partial), look = shooter.getViewVector(partial);
        Vec3 right = look.cross(new Vec3(0, 1, 0));
        right = right.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : right.normalize();
        return eye.add(look.scale(1.0)).add(right.scale(0.32)).add(0, -0.34, 0);
    }
}
