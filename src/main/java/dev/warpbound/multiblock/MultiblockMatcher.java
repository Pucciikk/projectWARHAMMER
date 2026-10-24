package dev.warpbound.multiblock;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

import java.util.ArrayList;
import java.util.List;

/**
 * Сверка шаблона с миром. Возвращает все несовпадения сразу, а не первое:
 * игрок должен видеть, что и где не так.
 */
public final class MultiblockMatcher {
    private MultiblockMatcher() {
    }

    /** Несовпавшая клетка: где, что ожидалось и что стоит. */
    public record Mismatch(BlockPos pos, Component expected, BlockState actual) {
    }

    public record Result(MultiblockOrientation orientation, List<BlockPos> members, List<Mismatch> mismatches) {
        public boolean ok() {
            return mismatches.isEmpty();
        }
    }

    public static Result match(Level level, BlockPos core, List<MultiblockDefinition.Cell> cells,
                               MultiblockOrientation orientation) {
        List<BlockPos> members = new ArrayList<>(cells.size());
        List<Mismatch> mismatches = new ArrayList<>();
        for (MultiblockDefinition.Cell cell : cells) {
            BlockPos pos = orientation.toWorld(core, cell.offset());
            BlockState state = level.getBlockState(pos);
            if (cell.matches().test(state)) {
                if (!state.isAir()) members.add(pos);
            } else {
                mismatches.add(new Mismatch(pos, cell.expected(), state));
            }
        }
        return new Result(orientation, members, mismatches);
    }

    /**
     * Перебирает отражение (если разрешено) при заданном повороте ядра и
     * возвращает собранный вариант или вариант с наименьшим числом ошибок.
     */
    public static Result best(Level level, BlockPos core, MultiblockDefinition def,
                              List<MultiblockDefinition.Cell> cells, net.minecraft.core.Direction facing) {
        Result best = match(level, core, cells, new MultiblockOrientation(facing, false));
        if (best.ok() || !def.mirrorable()) return best;
        Result mirrored = match(level, core, cells, new MultiblockOrientation(facing, true));
        return mirrored.mismatches().size() < best.mismatches().size() ? mirrored : best;
    }
}
