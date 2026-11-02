package dev.warpbound.client.multiblock;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.warpbound.Warpbound;
import dev.warpbound.core.ChainContentList;
import dev.warpbound.industry.machine.FluidPipeBlockEntity;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.PipeBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;

/**
 * Окошки трубы: латунная рамка со стеклом на гранях рукава, за стеклом течёт жидкость своего цвета и в сторону настоящего потока.
 * На прямом участке окно длинное, через весь кусок, поэтому линия читается как непрерывная.
 */
public final class FluidPipeRenderer implements BlockEntityRenderer<FluidPipeBlockEntity> {
    private static final ResourceLocation FRAME = Warpbound.id("textures/block/pipe_window.png");
    private static final ResourceLocation FLOW = Warpbound.id("textures/block/pipe_flow.png");
    /** Поверхность трубы от оси и ширина окна, в долях блока. */
    private static final float SURFACE = 3.04f / 16, HALF_W = 2.1f / 16;
    private static final float SCROLL = 0.045f;

    @Override
    public void render(FluidPipeBlockEntity be, float partialTick, PoseStack pose, MultiBufferSource buffers, int light, int overlay) {
        BlockState state = be.getBlockState();
        Fluid fluid = be.fluid();
        boolean hasFluid = fluid != Fluids.EMPTY;
        long time = be.getLevel() == null ? 0 : be.getLevel().getGameTime();
        boolean flowing = hasFluid && be.flowing(time);
        float scroll = flowing ? ((time + partialTick) * SCROLL) % 1f : 0f;
        // яркая жидкость чуть светится сама, стоячая темнее
        int bright = LightTexture.pack(Math.max(LightTexture.block(light), flowing ? 12 : 6), LightTexture.sky(light));
        int colour = hasFluid ? (flowing ? 0xF0000000 : 0xB0000000) | colourOf(fluid) : 0;

        VertexConsumer frame = buffers.getBuffer(RenderType.entityCutout(FRAME));
        // прямой участок: одно длинное окно через центр
        Direction.Axis straight = straightAxis(state);
        if (straight != null) {
            Direction pos = Direction.fromAxisAndDirection(straight, Direction.AxisDirection.POSITIVE);
            drawWindow(frame, pose, pos, -6.5f / 16, 6.5f / 16, light, overlay);
            if (hasFluid) {
                VertexConsumer flow = buffers.getBuffer(RenderType.entityTranslucent(FLOW));
                Direction from = be.from();
                // поток по оси: положительный, если входит с отрицательной стороны
                float sign = from == null || from.getAxisDirection() == Direction.AxisDirection.NEGATIVE ? 1 : -1;
                drawFlow(flow, pose, pos, -6f / 16, 6f / 16, scroll * sign, colour, bright, overlay);
            }
            return;
        }
        for (Direction d : Direction.values()) {
            if (!state.getValue(PipeBlock.PROPERTY_BY_DIRECTION.get(d))) continue;
            drawWindow(frame, pose, d, 3.3f / 16, 6.5f / 16, light, overlay);
        }
        if (hasFluid) {
            VertexConsumer flow = buffers.getBuffer(RenderType.entityTranslucent(FLOW));
            for (Direction d : Direction.values()) {
                if (!state.getValue(PipeBlock.PROPERTY_BY_DIRECTION.get(d))) continue;
                // от центра наружу, кроме рукава, откуда жидкость пришла
                float sign = d == be.from() ? -1 : 1;
                drawFlow(flow, pose, d, 3.8f / 16, 6f / 16, scroll * sign, colour, bright, overlay);
            }
        }
    }

    private static Direction.Axis straightAxis(BlockState state) {
        for (Direction.Axis axis : Direction.Axis.values()) {
            Direction a = Direction.fromAxisAndDirection(axis, Direction.AxisDirection.POSITIVE);
            if (!state.getValue(PipeBlock.PROPERTY_BY_DIRECTION.get(a)) || !state.getValue(PipeBlock.PROPERTY_BY_DIRECTION.get(a.getOpposite()))) continue;
            boolean others = false;
            for (Direction d : Direction.values()) {
                if (d.getAxis() != axis && state.getValue(PipeBlock.PROPERTY_BY_DIRECTION.get(d))) others = true;
            }
            if (!others) return axis;
        }
        return null;
    }

    private static int colourOf(Fluid fluid) {
        if (fluid == Fluids.WATER) return 0x3A7CD6;
        ResourceLocation key = BuiltInRegistries.FLUID.getKey(fluid);
        return ChainContentList.FLUIDS.getOrDefault(key.getPath(), 0x808080);
    }

    /** Рамка на всех гранях вокруг оси рукава: d — направление вдоль, от a до b по нему. */
    private static void drawWindow(VertexConsumer vc, PoseStack pose, Direction d, float a, float b, int light, int overlay) {
        for (Direction side : Direction.values()) {
            if (side.getAxis() == d.getAxis()) continue;
            quad(vc, pose, d, side, SURFACE, a, b, HALF_W + 0.45f / 16, 0, Math.abs(b - a) * 2, 0xFFFFFFFF, light, overlay);
        }
    }

    private static void drawFlow(VertexConsumer vc, PoseStack pose, Direction d, float a, float b, float scroll, int colour, int light, int overlay) {
        for (Direction side : Direction.values()) {
            if (side.getAxis() == d.getAxis()) continue;
            quad(vc, pose, d, side, SURFACE + 0.04f / 16, a, b, HALF_W - 0.1f / 16, -scroll, -scroll + Math.abs(b - a) * 2, colour, light, overlay);
        }
    }

    private static void quad(VertexConsumer vc, PoseStack pose, Direction along, Direction side, float out, float a, float b, float halfW,
                             float v0, float v1, int colour, int light, int overlay) {
        Direction across = crossOf(along, side);
        var last = pose.last();
        float[][] corners = {{a, -halfW}, {b, -halfW}, {b, halfW}, {a, halfW}};
        float[][] uvs = {{0, v0}, {0, v1}, {1, v1}, {1, v0}};
        boolean flip = across.getAxisDirection() != along.getAxisDirection() ^ side.getAxisDirection() == Direction.AxisDirection.NEGATIVE;
        for (int n = 0; n < 4; n++) {
            int i = flip ? 3 - n : n;
            float t = corners[i][0], w = corners[i][1];
            float x = 0.5f + along.getStepX() * t + across.getStepX() * w + side.getStepX() * out;
            float y = 0.5f + along.getStepY() * t + across.getStepY() * w + side.getStepY() * out;
            float z = 0.5f + along.getStepZ() * t + across.getStepZ() * w + side.getStepZ() * out;
            vc.addVertex(last, x, y, z).setColor(colour).setUv(uvs[i][0], uvs[i][1]).setOverlay(overlay).setLight(light)
                    .setNormal(last, side.getStepX(), side.getStepY(), side.getStepZ());
        }
    }

    /** Третья ось. */
    private static Direction crossOf(Direction a, Direction b) {
        for (Direction.Axis axis : Direction.Axis.values()) {
            if (axis != a.getAxis() && axis != b.getAxis()) return Direction.fromAxisAndDirection(axis, Direction.AxisDirection.POSITIVE);
        }
        return Direction.UP;
    }
}
