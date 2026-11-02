package dev.warpbound.client.multiblock;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.warpbound.Warpbound;
import dev.warpbound.industry.machine.MachineSpec;
import dev.warpbound.industry.machine.PortPumps;
import dev.warpbound.multiblock.MultiblockOrientation;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.resources.ResourceLocation;

/**
 * Разъёмы на цоколе машины. Жидкость и энергия — цветная рамка на грани блока. Предметы — настоящий люк:
 * короб внутрь машины, тёмное нутро, стекло сверху и резиновые шторки, которые качаются, пока машина работает.
 * Конвейер заводит предмет в этот короб, поэтому он не исчезает на границе, а уезжает за шторки.
 */
final class PortRenderer {
    private static final ResourceLocation PORT = Warpbound.id("textures/block/machine_port.png");
    private static final ResourceLocation HATCH = Warpbound.id("textures/block/machine_hatch.png");
    /** Глубина люка внутрь блока, полуширина и верх проёма. */
    private static final float DEPTH = 0.56f, HALF = 0.44f, OPEN_HALF = 0.36f, TOP = 0.72f, OPEN_TOP = 0.6f;
    private static final int STRIPS = 6;

    /** Области текстуры люка: сторона, стекло, нутро, шторка, цветная полоса. */
    private static final float[] SIDE = {0, 0, .5f, .5f}, GLASS = {.5f, 0, 1, .5f}, DARK = {0, .5f, .5f, 1}, STRIP = {.5f, .5f, .625f, 1}, BAND = {.625f, .5f, 1, 1};

    private PortRenderer() {
    }

    static void draw(long[] ports, MultiblockOrientation orientation, PoseStack pose, MultiBufferSource buffers, int light, int overlay, float time, boolean working) {
        VertexConsumer flat = null;
        VertexConsumer hatch = null;
        PoseStack.Pose last = pose.last();
        for (long packed : ports) {
            BlockPos at = orientation.toWorld(BlockPos.ZERO, PortPumps.unpackOffset(packed));
            Direction face = orientation.rotation().rotate(PortPumps.unpackFace(packed));
            MachineSpec.Kind kind = PortPumps.unpackKind(packed);
            int colour = colour(kind, PortPumps.unpackOutput(packed));
            if (kind == MachineSpec.Kind.ITEM) {
                if (hatch == null) hatch = buffers.getBuffer(RenderType.entityTranslucent(HATCH));
                hatch(hatch, last, at, face, colour, light, overlay, time, working);
            } else {
                if (flat == null) flat = buffers.getBuffer(RenderType.entityCutout(PORT));
                flatPort(flat, last, at, face, colour, light, overlay);
            }
        }
    }

    private static int colour(MachineSpec.Kind kind, boolean output) {
        return switch (kind) {
            case ENERGY -> 0xFFE0452E;
            case FLUID -> output ? 0xFF4AB8E8 : 0xFF2A6FD0;
            case ITEM -> output ? 0xFFF0C040 : 0xFFB08020;
        };
    }

    private static void flatPort(VertexConsumer vc, PoseStack.Pose pose, BlockPos at, Direction face, int colour, int light, int overlay) {
        float out = 0.51f, half = 0.34f;
        float cx = at.getX() + 0.5f + face.getStepX() * out;
        float cy = at.getY() + 0.5f + face.getStepY() * out;
        float cz = at.getZ() + 0.5f + face.getStepZ() * out;
        Direction u = face.getAxis() == Direction.Axis.Y ? Direction.EAST : face.getClockWise();
        Direction v = face.getAxis() == Direction.Axis.Y ? Direction.SOUTH : Direction.UP;
        float[][] corners = {{-1, -1}, {1, -1}, {1, 1}, {-1, 1}};
        float[][] uvs = {{0, 1}, {1, 1}, {1, 0}, {0, 0}};
        for (int i = 0; i < 4; i++) {
            float a = corners[i][0] * half, b = corners[i][1] * half;
            vc.addVertex(pose, cx + u.getStepX() * a + v.getStepX() * b, cy + u.getStepY() * a + v.getStepY() * b, cz + u.getStepZ() * a + v.getStepZ() * b)
                    .setColor(colour).setUv(uvs[i][0], uvs[i][1]).setOverlay(overlay).setLight(light)
                    .setNormal(pose, face.getStepX(), face.getStepY(), face.getStepZ());
        }
    }

    /** Точка люка: w — поперёк, h — высота от низа блока, d — вглубь машины от грани блока. */
    private record Frame(float ox, float oy, float oz, Direction face, Direction side) {
        float[] p(float w, float h, float d) {
            float n = 0.5f - d;
            return new float[]{ox + 0.5f + face.getStepX() * n + side.getStepX() * w, oy + h, oz + 0.5f + face.getStepZ() * n + side.getStepZ() * w};
        }
    }

    private static void hatch(VertexConsumer vc, PoseStack.Pose pose, BlockPos at, Direction face, int colour, int light, int overlay, float time, boolean working) {
        Frame f = new Frame(at.getX(), at.getY(), at.getZ(), face, face.getClockWise());
        int white = 0xFFFFFFFF;
        float nx = face.getStepX(), nz = face.getStepZ();
        // нутро: задняя стенка, пол, бока изнутри
        quad(vc, pose, f.p(-OPEN_HALF, 0.02f, DEPTH), f.p(OPEN_HALF, 0.02f, DEPTH), f.p(OPEN_HALF, OPEN_TOP, DEPTH), f.p(-OPEN_HALF, OPEN_TOP, DEPTH), DARK, white, light, overlay, nx, 0, nz);
        quad(vc, pose, f.p(-OPEN_HALF, 0.02f, 0), f.p(OPEN_HALF, 0.02f, 0), f.p(OPEN_HALF, 0.02f, DEPTH), f.p(-OPEN_HALF, 0.02f, DEPTH), DARK, white, light, overlay, 0, 1, 0);
        // наружные бока и косяки проёма
        float sx = f.side().getStepX(), sz = f.side().getStepZ();
        quad(vc, pose, f.p(HALF, 0, 0), f.p(HALF, 0, DEPTH), f.p(HALF, TOP, DEPTH), f.p(HALF, TOP, 0), SIDE, white, light, overlay, sx, 0, sz);
        quad(vc, pose, f.p(-HALF, 0, DEPTH), f.p(-HALF, 0, 0), f.p(-HALF, TOP, 0), f.p(-HALF, TOP, DEPTH), SIDE, white, light, overlay, -sx, 0, -sz);
        quad(vc, pose, f.p(-HALF, 0, 0), f.p(-OPEN_HALF, 0, 0), f.p(-OPEN_HALF, TOP, 0), f.p(-HALF, TOP, 0), SIDE, white, light, overlay, nx, 0, nz);
        quad(vc, pose, f.p(OPEN_HALF, 0, 0), f.p(HALF, 0, 0), f.p(HALF, TOP, 0), f.p(OPEN_HALF, TOP, 0), SIDE, white, light, overlay, nx, 0, nz);
        // цветная полоса над проёмом: вход темнее, выход ярче
        quad(vc, pose, f.p(-OPEN_HALF, OPEN_TOP, 0), f.p(OPEN_HALF, OPEN_TOP, 0), f.p(OPEN_HALF, TOP, 0), f.p(-OPEN_HALF, TOP, 0), BAND, colour, light, overlay, nx, 0, nz);
        // крыша со стеклом: сквозь неё виден предмет внутри
        quad(vc, pose, f.p(-HALF, TOP, 0), f.p(HALF, TOP, 0), f.p(HALF, TOP, DEPTH), f.p(-HALF, TOP, DEPTH), GLASS, white, light, overlay, 0, 1, 0);
        // шторки
        float w = 2 * OPEN_HALF / STRIPS;
        for (int i = 0; i < STRIPS; i++) {
            float x0 = -OPEN_HALF + i * w + 0.006f, x1 = x0 + w - 0.012f;
            float swing = working ? (float) Math.sin(time * 0.22f + i * 1.3f) * 0.05f : 0;
            float bottom = 0.34f;
            quad(vc, pose, f.p(x0, bottom, -swing), f.p(x1, bottom, -swing), f.p(x1, OPEN_TOP, 0), f.p(x0, OPEN_TOP, 0), STRIP, white, light, overlay, nx, 0, nz);
        }
    }

    private static void quad(VertexConsumer vc, PoseStack.Pose pose, float[] a, float[] b, float[] c, float[] d, float[] uv, int colour, int light, int overlay, float nx, float ny, float nz) {
        put(vc, pose, a, uv[0], uv[3], colour, light, overlay, nx, ny, nz);
        put(vc, pose, b, uv[2], uv[3], colour, light, overlay, nx, ny, nz);
        put(vc, pose, c, uv[2], uv[1], colour, light, overlay, nx, ny, nz);
        put(vc, pose, d, uv[0], uv[1], colour, light, overlay, nx, ny, nz);
    }

    private static void put(VertexConsumer vc, PoseStack.Pose pose, float[] p, float u, float v, int colour, int light, int overlay, float nx, float ny, float nz) {
        vc.addVertex(pose, p[0], p[1], p[2]).setColor(colour).setUv(u, v).setOverlay(overlay).setLight(light).setNormal(pose, nx, ny, nz);
    }
}
