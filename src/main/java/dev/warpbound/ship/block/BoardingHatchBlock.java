package dev.warpbound.ship.block;

import com.mojang.serialization.MapCodec;
import net.minecraft.world.level.block.Block;

/**
 * Внешний люк корабля: та же гермодверь, но при герметизации перед выходом в космос он запирается
 * (внутренние двери отсеков только закрываются). Открыть снова — с пульта или на орбите у дока.
 */
public class BoardingHatchBlock extends BulkheadDoorBlock {
    public static final MapCodec<BoardingHatchBlock> CODEC = simpleCodec(BoardingHatchBlock::new);

    public BoardingHatchBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends Block> codec() {
        return CODEC;
    }
}
