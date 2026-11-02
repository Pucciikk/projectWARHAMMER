package dev.warpbound.industry.machine;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Труба с окошками: сущность блока без тика хранит только то, что видно внутри. */
public class FluidPipeBlock extends ConduitBlock implements EntityBlock {
    public FluidPipeBlock(Properties properties) {
        super(MachineSpec.Kind.FLUID, properties);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new FluidPipeBlockEntity(pos, state);
    }
}
