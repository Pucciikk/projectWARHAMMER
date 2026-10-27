package dev.warpbound.client.gear;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.warpbound.network.LasBeamPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderEvents;
import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix4f;
import org.joml.Vector3f;

import java.util.ArrayList;
import java.util.List;

/**
 * Луч лазгана: тонкая одиночная жёлтая черта от ствола до цели, гаснет за пару тиков.
 * Начало считается на клиенте: у себя в первом лице — от ствола в руке на экране, у других — от ствола в их руках.
 */
public final class LasBeams {
    private static final int LIFE_MS = 180;
    private static final List<Beam> BEAMS = new ArrayList<>();

    private record Beam(int shooter, Vec3 end, long born) {
    }

    private LasBeams() {
    }

    public static void register() {
        ClientPlayNetworking.registerGlobalReceiver(LasBeamPayload.TYPE, (payload, context) ->
                BEAMS.add(new Beam(payload.shooter(), new Vec3(payload.x(), payload.y(), payload.z()), System.currentTimeMillis())));
        WorldRenderEvents.AFTER_TRANSLUCENT.register(context -> {
            if (BEAMS.isEmpty() || context.consumers() == null) return;
            long now = System.currentTimeMillis();
            BEAMS.removeIf(b -> now - b.born > LIFE_MS);
            Minecraft mc = Minecraft.getInstance();
            if (mc.level == null) return;
            Camera camera = context.camera();
            Vec3 cam = camera.getPosition();
            PoseStack pose = context.matrixStack();
            VertexConsumer vc = context.consumers().getBuffer(RenderType.lightning());
            pose.pushPose();
            pose.translate(-cam.x, -cam.y, -cam.z);
            Matrix4f m = pose.last().pose();
            for (Beam b : BEAMS) {
                Entity shooter = mc.level.getEntity(b.shooter);
                if (shooter == null) continue;
                Vec3 start = muzzle(mc, camera, shooter, context.tickCounter().getGameTimeDeltaPartialTick(true));
                float fade = 1f - (now - b.born) / (float) LIFE_MS;
                quad(vc, m, cam, start, b.end, 0.05f, 1f, 0.75f, 0.1f, 0.25f * fade);   // мягкий ореол
                quad(vc, m, cam, start, b.end, 0.014f, 1f, 0.95f, 0.45f, 0.95f * fade); // жёлтое ядро
            }
            pose.popPose();
        });
    }

    /** Ствол: в первом лице — справа снизу от центра экрана, в третьем — у правой руки стрелка на изготовке. */
    private static Vec3 muzzle(Minecraft mc, Camera camera, Entity shooter, float partial) {
        if (shooter == mc.player && mc.options.getCameraType().isFirstPerson()) {
            Vector3f look = camera.getLookVector(), up = camera.getUpVector(), left = camera.getLeftVector();
            return camera.getPosition().add(look.x * 1.0 - left.x * 0.42 - up.x * 0.3,
                    look.y * 1.0 - left.y * 0.42 - up.y * 0.3, look.z * 1.0 - left.z * 0.42 - up.z * 0.3);
        }
        Vec3 eye = shooter.getEyePosition(partial);
        Vec3 look = shooter.getViewVector(partial);
        float yaw = (shooter instanceof LivingEntity l ? l.yBodyRot : shooter.getYRot()) * ((float) Math.PI / 180f);
        Vec3 right = new Vec3(-Math.cos(yaw), 0, -Math.sin(yaw));
        return eye.add(look.scale(1.3)).add(right.scale(0.3)).add(0, -0.25, 0);
    }

    private static void quad(VertexConsumer vc, Matrix4f m, Vec3 cam, Vec3 a, Vec3 b, float width,
                             float r, float g, float bl, float alpha) {
        Vec3 dir = b.subtract(a);
        Vec3 toCam = cam.subtract(a.add(b).scale(0.5));
        Vec3 side = dir.cross(toCam).normalize().scale(width);
        vc.addVertex(m, (float) (a.x + side.x), (float) (a.y + side.y), (float) (a.z + side.z)).setColor(r, g, bl, alpha);
        vc.addVertex(m, (float) (a.x - side.x), (float) (a.y - side.y), (float) (a.z - side.z)).setColor(r, g, bl, alpha);
        vc.addVertex(m, (float) (b.x - side.x), (float) (b.y - side.y), (float) (b.z - side.z)).setColor(r, g, bl, alpha);
        vc.addVertex(m, (float) (b.x + side.x), (float) (b.y + side.y), (float) (b.z + side.z)).setColor(r, g, bl, alpha);
        // обратная сторона: тип рендера молнии отсекает грани, повёрнутые от камеры
        vc.addVertex(m, (float) (b.x + side.x), (float) (b.y + side.y), (float) (b.z + side.z)).setColor(r, g, bl, alpha);
        vc.addVertex(m, (float) (b.x - side.x), (float) (b.y - side.y), (float) (b.z - side.z)).setColor(r, g, bl, alpha);
        vc.addVertex(m, (float) (a.x - side.x), (float) (a.y - side.y), (float) (a.z - side.z)).setColor(r, g, bl, alpha);
        vc.addVertex(m, (float) (a.x + side.x), (float) (a.y + side.y), (float) (a.z + side.z)).setColor(r, g, bl, alpha);
    }
}
