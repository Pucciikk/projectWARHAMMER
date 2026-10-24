package dev.warpbound.client.multiblock;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.warpbound.network.MultiblockErrorsPayload;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderEvents;
import net.minecraft.client.renderer.LevelRenderer;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.core.BlockPos;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.List;

/**
 * Подсветка ошибок сборки мультиблока: жёлтые рамки — где не хватает блока, красные — где стоит чужой.
 * Держится несколько секунд после неудачного освящения.
 */
public final class MultiblockHighlight {
    private static final long SHOW_MS = 15_000;
    /** Дальше этого рамки не рисуются: на огромной верфи иначе сотни линий. */
    private static final double MAX_DIST_SQR = 64 * 64;

    private static List<BlockPos> missing = List.of();
    private static List<BlockPos> wrong = List.of();
    private static long until;

    private MultiblockHighlight() {
    }

    public static void show(MultiblockErrorsPayload payload) {
        missing = payload.missing();
        wrong = payload.wrong();
        until = System.currentTimeMillis() + SHOW_MS;
    }

    public static void register() {
        WorldRenderEvents.AFTER_TRANSLUCENT.register(context -> {
            if (System.currentTimeMillis() > until || (missing.isEmpty() && wrong.isEmpty())) return;
            if (context.consumers() == null) return;
            Vec3 cam = context.camera().getPosition();
            PoseStack pose = context.matrixStack();
            VertexConsumer lines = context.consumers().getBuffer(RenderType.lines());
            // Мягкое мерцание, чтобы рамки было видно на любом фоне
            float pulse = 0.6f + 0.4f * (float) Math.sin(System.currentTimeMillis() / 180.0);
            pose.pushPose();
            pose.translate(-cam.x, -cam.y, -cam.z);
            draw(pose, lines, missing, cam, 1f, 0.8f, 0.1f, pulse);
            draw(pose, lines, wrong, cam, 1f, 0.15f, 0.1f, pulse);
            pose.popPose();
        });
    }

    private static void draw(PoseStack pose, VertexConsumer lines, List<BlockPos> list, Vec3 cam,
                             float r, float g, float b, float a) {
        for (BlockPos p : list) {
            if (p.distToCenterSqr(cam) > MAX_DIST_SQR) continue;
            LevelRenderer.renderLineBox(pose, lines, new AABB(p).inflate(0.02), r, g, b, a);
        }
    }
}
