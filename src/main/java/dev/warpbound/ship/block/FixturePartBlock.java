package dev.warpbound.ship.block;

import net.minecraft.core.BlockPos;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Часть крупного корабельного оборудования: невидимый прочный блок в отсеке (ставится структурой интерьера).
 * ПКМ — как по самому оборудованию: ищется ближайшее ядро в пределах {@link #REACH} блоков.
 */
public class FixturePartBlock extends Block {
    private static final int REACH = 3;

    public FixturePartBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.INVISIBLE;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        BlockPos best = null;
        double bestDist = Double.MAX_VALUE;
        for (BlockPos p : BlockPos.betweenClosed(pos.offset(-REACH, -REACH, -REACH), pos.offset(REACH, REACH, REACH))) {
            if (level.getBlockState(p).getBlock() instanceof ShipFixtureBlock fixture && fixture.isBig()) {
                double d = p.distSqr(pos);
                if (d < bestDist) {
                    bestDist = d;
                    best = p.immutable();
                }
            }
        }
        if (best == null) return InteractionResult.PASS;
        return level.getBlockState(best).useWithoutItem(level, player, hit.withPosition(best));
    }
}
