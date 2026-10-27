package dev.warpbound.ship.block;

import dev.warpbound.core.WarpboundBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Карта Империума: данных нет, нужна только ради рендера табло (StarChartRenderer). */
public class StarChartBlockEntity extends BlockEntity {
    public StarChartBlockEntity(BlockPos pos, BlockState state) {
        super(WarpboundBlockEntities.STAR_CHART, pos, state);
    }
}
