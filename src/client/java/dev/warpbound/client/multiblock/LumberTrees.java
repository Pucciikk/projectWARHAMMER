package dev.warpbound.client.multiblock;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.warpbound.industry.ChainMachineBlockEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.block.BlockRenderDispatcher;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Делянка лесопилки: уменьшенные дубы и саженцы из настоящих ванильных блоков, поэтому текстуры и цвет листвы как в обычном мире.
 * Координаты в блоках от ядра, при взгляде машины на север; глубина растёт от переда к задней стенке.
 */
final class LumberTrees {
    /** Масштаб дерева: крона в три блока влезает на делянку глубиной два блока. */
    private static final float SCALE = 0.55f;
    private static final float SOIL = 0.42f;
    private static final float[][] TREES = {{-1.6f, 3.4f}, {0f, 3.4f}, {1.6f, 3.4f}};
    private static final float[][] SAPLINGS = {{-0.8f, 2.65f}, {0.8f, 2.65f}, {-2f, 2.65f}, {2f, 2.65f}};

    private LumberTrees() {
    }

    static void render(ChainMachineBlockEntity machine, PoseStack pose, MultiBufferSource buffers, int light, int overlay) {
        BlockRenderDispatcher blocks = Minecraft.getInstance().getBlockRenderer();
        BlockState log = Blocks.OAK_LOG.defaultBlockState();
        BlockState leaves = Blocks.OAK_LEAVES.defaultBlockState();
        BlockState sapling = Blocks.OAK_SAPLING.defaultBlockState();
        pose.pushPose();
        pose.translate(0.5, 0, 0.5);
        // тот же поворот, что у шаблона: на восток задняя стенка уходит на запад
        pose.mulPose(Axis.YP.rotationDegrees(switch (machine.orientation().facing()) {
            case EAST -> -90f;
            case SOUTH -> 180f;
            case WEST -> 90f;
            default -> 0f;
        }));
        for (float[] t : TREES) {
            pose.pushPose();
            pose.translate(t[0], SOIL, t[1] - 0.5f);
            pose.scale(SCALE, SCALE, SCALE);
            pose.translate(-0.5, 0, -0.5);
            for (int y = 0; y < 4; y++) block(blocks, log, pose, 0, y, 0, buffers, light, overlay);
            // крона: два полных слоя 3×3 вокруг ствола и крест сверху
            for (int y = 2; y <= 3; y++) {
                for (int x = -1; x <= 1; x++) {
                    for (int z = -1; z <= 1; z++) {
                        if (x != 0 || z != 0) block(blocks, leaves, pose, x, y, z, buffers, light, overlay);
                    }
                }
            }
            for (int[] c : new int[][]{{0, 0}, {1, 0}, {-1, 0}, {0, 1}, {0, -1}}) {
                block(blocks, leaves, pose, c[0], 4, c[1], buffers, light, overlay);
            }
            pose.popPose();
        }
        for (float[] s : SAPLINGS) {
            pose.pushPose();
            pose.translate(s[0] - 0.3f, SOIL, s[1] - 0.8f);
            pose.scale(0.6f, 0.6f, 0.6f);
            blocks.renderSingleBlock(sapling, pose, buffers, light, overlay);
            pose.popPose();
        }
        pose.popPose();
    }

    private static void block(BlockRenderDispatcher blocks, BlockState state, PoseStack pose, int x, int y, int z, MultiBufferSource buffers, int light, int overlay) {
        pose.pushPose();
        pose.translate(x, y, z);
        blocks.renderSingleBlock(state, pose, buffers, light, overlay);
        pose.popPose();
    }
}
