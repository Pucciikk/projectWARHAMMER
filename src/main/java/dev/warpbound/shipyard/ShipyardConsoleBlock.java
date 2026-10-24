package dev.warpbound.shipyard;

import com.mojang.serialization.MapCodec;
import dev.warpbound.core.WarpboundBlockEntities;
import dev.warpbound.multiblock.MultiblockCoreBlock;
import dev.warpbound.multiblock.MultiblockCoreBlockEntity;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/** Пульт верфи: ядро стапеля. ПКМ по собранной верфи — экран постройки корабля. */
public class ShipyardConsoleBlock extends MultiblockCoreBlock {
    public static final MapCodec<ShipyardConsoleBlock> CODEC = simpleCodec(ShipyardConsoleBlock::new);

    public ShipyardConsoleBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return CODEC;
    }

    @Override
    protected BlockEntityType<? extends MultiblockCoreBlockEntity> coreType() {
        return WarpboundBlockEntities.SHIPYARD;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new ShipyardBlockEntity(pos, state);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level.isClientSide) return InteractionResult.SUCCESS;
        if (!(level.getBlockEntity(pos) instanceof ShipyardBlockEntity yard) || !(player instanceof ServerPlayer sp)) {
            return InteractionResult.PASS;
        }
        if (!yard.isFormed()) {
            player.displayClientMessage(Component.translatable("shipyard.warpbound.not_formed").withStyle(ChatFormatting.GOLD), true);
        } else {
            yard.sendState(sp);
        }
        return InteractionResult.CONSUME;
    }
}
