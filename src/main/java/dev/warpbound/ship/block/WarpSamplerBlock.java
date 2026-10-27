package dev.warpbound.ship.block;

import com.mojang.serialization.MapCodec;
import dev.warpbound.core.WarpboundBlockEntities;
import dev.warpbound.core.WarpboundItems;
import dev.warpbound.ship.ShipService;
import dev.warpbound.ship.ShipState;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jetbrains.annotations.Nullable;

/**
 * Варп-пробоотборник анклава Механикус: стол 5×2 со стенкой и портом в варп, модель — warp_sampler (GeckoLib).
 * ПКМ с пустой колбой — рука набирает пробу; в варпе колба возвращается с красной варп-материей.
 * Остальные клетки стола — {@link FixturePartBlock}: ПКМ по ним приходит сюда.
 */
public class WarpSamplerBlock extends HorizontalDirectionalBlock implements EntityBlock {
    public static final MapCodec<WarpSamplerBlock> CODEC = simpleCodec(WarpSamplerBlock::new);

    public WarpSamplerBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        return defaultBlockState().setValue(FACING, ctx.getHorizontalDirection().getOpposite());
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext ctx) {
        return Shapes.block();
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.ENTITYBLOCK_ANIMATED;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level.isClientSide || !(player instanceof ServerPlayer sp)) return InteractionResult.SUCCESS;
        if (!(level.getBlockEntity(pos) instanceof WarpSamplerBlockEntity be)) return InteractionResult.PASS;
        if (be.busy()) {
            sp.displayClientMessage(Component.translatable("lab.warpbound.busy", be.secondsLeft()).withStyle(ChatFormatting.GOLD), true);
            return InteractionResult.CONSUME;
        }
        ItemStack hand = sp.getMainHandItem();
        if (!hand.is(WarpboundItems.SAMPLE_VIAL)) {
            sp.displayClientMessage(Component.translatable("lab.warpbound.need_vial").withStyle(ChatFormatting.GRAY), true);
            return InteractionResult.CONSUME;
        }
        boolean warp = ShipService.shipAboard(sp).map(s -> s.state == ShipState.ENTERING || s.state == ShipState.TRANSIT).orElse(false);
        if (!sp.getAbilities().instabuild) hand.shrink(1);
        be.start(sp, warp);
        sp.displayClientMessage(Component.translatable(warp ? "lab.warpbound.started" : "lab.warpbound.no_warp")
                .withStyle(warp ? ChatFormatting.DARK_RED : ChatFormatting.GRAY), true);
        return InteractionResult.CONSUME;
    }

    @Override
    public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new WarpSamplerBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> @Nullable BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return level.isClientSide || type != WarpboundBlockEntities.WARP_SAMPLER ? null
                : (l, p, s, be) -> WarpSamplerBlockEntity.serverTick(l, p, s, (WarpSamplerBlockEntity) be);
    }
}
