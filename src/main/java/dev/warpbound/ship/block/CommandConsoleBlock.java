package dev.warpbound.ship.block;

import com.mojang.serialization.MapCodec;
import dev.warpbound.ship.ShipConsole;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/** Командный пульт мостика (3 блока шириной): состояние корабля, навигация, Поле Геллера, реактор. */
public class CommandConsoleBlock extends ShipFixtureBlock {
    public static final MapCodec<CommandConsoleBlock> CODEC = simpleCodec(CommandConsoleBlock::new);

    public CommandConsoleBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return CODEC;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide && player instanceof ServerPlayer sp) ShipConsole.open(sp, pos);
        return InteractionResult.sidedSuccess(level.isClientSide);
    }
}
