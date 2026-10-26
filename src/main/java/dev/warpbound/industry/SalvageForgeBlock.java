package dev.warpbound.industry;

import com.mojang.serialization.MapCodec;
import dev.warpbound.core.WarpboundBlockEntities;
import dev.warpbound.multiblock.MultiblockHost;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.AbstractFurnaceBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.AbstractFurnaceBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;

/**
 * Горн обломков: переплавляет корабельный лом в пласталь и латунь. Топливо — как у печи.
 * Несобранный — просто ядро; ПКМ пустой рукой освящает груду 3×3×3, и горн становится цельной машиной.
 */
public class SalvageForgeBlock extends AbstractFurnaceBlock {
    public static final MapCodec<SalvageForgeBlock> CODEC = simpleCodec(SalvageForgeBlock::new);

    public SalvageForgeBlock(Properties properties) {
        super(properties);
        registerDefaultState(defaultBlockState().setValue(MultiblockHost.FORMED, false));
    }

    @Override
    protected MapCodec<? extends AbstractFurnaceBlock> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        super.createBlockStateDefinition(builder);
        builder.add(MultiblockHost.FORMED);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return state.getValue(MultiblockHost.FORMED) ? RenderShape.ENTITYBLOCK_ANIMATED : RenderShape.MODEL;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new SalvageForgeBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (level.isClientSide) return null;
        return createTickerHelper(type, WarpboundBlockEntities.SALVAGE_FORGE, (lvl, pos, st, forge) -> {
            // несобранный горн не плавит
            if (forge.isFormed()) AbstractFurnaceBlockEntity.serverTick(lvl, pos, st, forge);
            forge.multiblock().serverTick((ServerLevel) lvl);
        });
    }

    @Override
    protected void openContainer(Level level, BlockPos pos, Player player) {
        if (!(level.getBlockEntity(pos) instanceof SalvageForgeBlockEntity forge)) return;
        if (forge.isFormed()) {
            player.openMenu(forge);
        } else if (player instanceof ServerPlayer sp) {
            forge.multiblock().tryForm(sp);
        }
    }

    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean moved) {
        if (!state.is(newState.getBlock()) && level.getBlockEntity(pos) instanceof SalvageForgeBlockEntity forge) {
            forge.multiblock().onCoreRemoved();
        }
        super.onRemove(state, level, pos, newState, moved);
    }

    /** Точки собранной модели в блоках от ядра (север, +Z — вглубь): зев и верх трубы. */
    private static final double[] MOUTH = {0, 0.75, -0.3};
    private static final double[] CHIMNEY = {0, 3.9, 1.0};

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (!state.getValue(MultiblockHost.FORMED) || !(level.getBlockEntity(pos) instanceof SalvageForgeBlockEntity forge)) return;
        var top = MechanicusForgeBlock.toWorld(forge.multiblock().orientation(), pos, CHIMNEY);
        level.addParticle(ParticleTypes.CAMPFIRE_COSY_SMOKE, top.x, top.y, top.z, 0, state.getValue(LIT) ? 0.07 : 0.03, 0);
        if (!state.getValue(LIT)) return;
        var mouth = MechanicusForgeBlock.toWorld(forge.multiblock().orientation(), pos, MOUTH);
        if (random.nextDouble() < 0.2) {
            level.playLocalSound(mouth.x, mouth.y, mouth.z, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, SoundSource.BLOCKS, 1f, 0.8f, false);
        }
        Direction facing = state.getValue(FACING);
        level.addParticle(ParticleTypes.LAVA, mouth.x, mouth.y, mouth.z, 0, 0, 0);
        // искры лома: горн плюётся раскалёнными осколками из зева
        if (random.nextInt(2) == 0) level.addParticle(ParticleTypes.ELECTRIC_SPARK, mouth.x, mouth.y + 0.2, mouth.z,
                facing.getStepX() * 0.1, 0.06, facing.getStepZ() * 0.1);
        level.addParticle(ParticleTypes.LARGE_SMOKE, top.x, top.y, top.z, 0, 0.04, 0);
    }
}
