package dev.warpbound.client.gun;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.util.Mth;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;

/** Цепной меч от первого лица: клинок поднят наискось, удары идут по клипам из Blender, на оборотах оружие мелко дрожит от мотора. */
public final class ChainswordView {
    private static final float SCALE = 0.6f, HIP_X = 0.6f, HIP_Y = -0.46f, HIP_Z = -0.8f;
    /** Рукоять в этой точке модели (блоки): меч вращается вокруг кисти. */
    private static final float GRIP_Z = 0.13f, BLADE_ROLL = -10f, REST_LEAN = -22f;
    private static final float[] VIEW = new float[6], SEC = new float[1];
    private static float swayYaw, swayPitch, lastYaw, lastPitch;
    private static long lastNanos;

    private ChainswordView() {
    }

    public static void render(AbstractClientPlayer player, float partialTick, ItemStack stack, PoseStack pose, MultiBufferSource buffers, int light) {
        Minecraft mc = Minecraft.getInstance();
        long nanos = System.nanoTime();
        float dt = lastNanos == 0 ? 0.016f : Math.min(0.05f, (nanos - lastNanos) / 1e9f);
        lastNanos = nanos;
        float yaw = player.getViewYRot(partialTick), pitch = player.getViewXRot(partialTick);
        float dYaw = Mth.wrapDegrees(yaw - lastYaw), dPitch = pitch - lastPitch;
        lastYaw = yaw;
        lastPitch = pitch;
        float k = Math.min(1, dt * 9);
        swayYaw += (Mth.clamp(dYaw, -6, 6) - swayYaw) * k;
        swayPitch += (Mth.clamp(dPitch, -6, 6) - swayPitch) * k;

        float walk = player.walkDist + (player.walkDist - player.walkDistO) * partialTick;
        float moveAmt = Math.min(1, Mth.lerp(partialTick, player.oBob, player.bob) * 5.5f);
        float bobX = Mth.sin(walk * Mth.PI * 1.1f) * 0.018f * moveAmt;
        float bobY = -Math.abs(Mth.cos(walk * Mth.PI * 1.1f)) * 0.024f * moveAmt;
        float time = player.tickCount + partialTick;
        float breath = Mth.sin(time * 0.05f) * 0.004f;
        // мотор трясёт меч: быстрая дрожь, на холостом ходу чуть заметная
        float rev = ChainswordClient.rev();
        float shake = 0.0012f + 0.0042f * rev;
        float shakeX = Mth.sin(time * 7.3f) * shake, shakeY = Mth.cos(time * 9.1f) * shake;

        GunClips.Clip clip = ChainswordClient.activeClip(mc, SEC);
        boolean has = clip.sample("_view", SEC[0], VIEW);
        float vx = has ? VIEW[0] : 0, vy = has ? VIEW[1] : 0, vz = has ? VIEW[2] : 0;
        float rx = has ? VIEW[3] : 0, ry = has ? VIEW[4] : 0, rz = has ? VIEW[5] : 0;

        pose.pushPose();
        pose.translate(HIP_X + bobX + shakeX - swayYaw * 0.0028f - vx, HIP_Y + bobY + breath + shakeY + swayPitch * 0.0024f + vz, HIP_Z + vy);
        // дуга удара идёт в плоскости экрана, как стрелка часов: так клинок пересекает весь кадр, а не уходит вперёд в точку
        pose.mulPose(Axis.ZP.rotationDegrees(REST_LEAN + ry));
        // поза покоя как у ванильного меча: рукоять внизу справа, кончик уходит вверх, вправо и к игроку
        pose.mulPose(Axis.YP.rotationDegrees(-swayYaw * 0.6f + rz));
        pose.mulPose(Axis.XP.rotationDegrees(98 + swayPitch * 0.6f - rx));
        // клинок ребром вперёд, как у ванильного меча: плоскостью к стрелку он выглядел бы взятым поперёк
        pose.mulPose(Axis.ZP.rotationDegrees(BLADE_ROLL + swayYaw * 0.35f));
        pose.scale(SCALE, SCALE, SCALE);
        pose.translate(0, 0, -GRIP_Z);

        ChainswordRenderer renderer = ChainswordRenderer.get();
        pose.pushPose();
        pose.translate(-0.5f, -0.51f, -0.5f);
        GunRenderer.viewPass = true;
        GunRenderer.CAPTURED.clear();
        renderer.renderByItem(stack, ItemDisplayContext.FIRST_PERSON_RIGHT_HAND, pose, buffers, light, OverlayTexture.NO_OVERLAY);
        GunRenderer.viewPass = false;
        pose.popPose();
        // как с обычным мечом: рука в кадре не рисуется, только оружие
        pose.popPose();
    }
}
