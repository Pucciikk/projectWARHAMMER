package dev.warpbound.ship.block;

import com.mojang.serialization.MapCodec;
import dev.warpbound.ship.ShipNavigation;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/** Навигационный стол мостика: ПКМ — карта пунктов назначения. */
public class NavTableBlock extends ShipFixtureBlock {
    public static final MapCodec<NavTableBlock> CODEC = simpleCodec(NavTableBlock::new);

    public NavTableBlock(Properties properties) {
        super(properties, Block.box(0, 0, 0, 16, 13, 16));
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return CODEC;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide && player instanceof ServerPlayer sp) ShipNavigation.openTable(sp);
        return InteractionResult.sidedSuccess(level.isClientSide);
    }
}
