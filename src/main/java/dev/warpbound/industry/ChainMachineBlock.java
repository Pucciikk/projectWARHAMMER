package dev.warpbound.industry;

import com.mojang.serialization.MapCodec;
import dev.warpbound.core.WarpboundBlockEntities;
import dev.warpbound.multiblock.MachineCoreBlock;
import dev.warpbound.multiblock.MachineCoreBlockEntity;
import dev.warpbound.multiblock.MultiblockCoreBlockEntity;
import dev.warpbound.multiblock.MultiblockHost;
import net.fabricmc.fabric.api.transfer.v1.context.ContainerItemContext;
import net.fabricmc.fabric.api.transfer.v1.fluid.FluidStorage;
import net.fabricmc.fabric.api.transfer.v1.fluid.FluidStorageUtil;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Ядро машины цепочки: модель, анимация, эффекты, окно. Логика и порты — в {@link ChainMachineBlockEntity}.
 * Точки эффектов — в блоках от ядра, как в {@link MechanicusForgeBlock#toWorld}: x, высота, глубина.
 */
public class ChainMachineBlock extends MachineCoreBlock {
    /** Что машина выпускает, пока работает: дым из труб, искры у рабочего места, звук раз в несколько секунд. */
    public record Effects(double[][] smoke, double[][] sparks, SoundEvent sound, float pitch) {
    }

    private final Effects effects;
    private final MapCodec<ChainMachineBlock> codec;

    public ChainMachineBlock(Properties properties, Effects effects) {
        super(properties);
        this.effects = effects;
        this.codec = simpleCodec(p -> new ChainMachineBlock(p, effects));
        registerDefaultState(defaultBlockState().setValue(BlockStateProperties.LIT, false));
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return codec;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        super.createBlockStateDefinition(builder);
        builder.add(BlockStateProperties.LIT);
    }

    @Override
    protected BlockEntityType<? extends MultiblockCoreBlockEntity> coreType() {
        return WarpboundBlockEntities.CHAIN_MACHINE;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new ChainMachineBlockEntity(pos, state);
    }

    @Override
    protected InteractionResult useFormed(BlockState state, Level level, BlockPos pos, Player player, MachineCoreBlockEntity core) {
        if (!level.isClientSide && core instanceof ChainMachineBlockEntity machine) player.openMenu(machine);
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    /** Ведро по машине: налить во входной бак или набрать из выходного. */
    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand, BlockHitResult hit) {
        if (level.getBlockEntity(pos) instanceof ChainMachineBlockEntity machine && machine.isFormed()
                && ContainerItemContext.forPlayerInteraction(player, hand).find(FluidStorage.ITEM) != null) {
            boolean done = FluidStorageUtil.interactWithFluidStorage(machine.fluidStorage(false), player, hand)
                    || FluidStorageUtil.interactWithFluidStorage(machine.fluidStorage(true), player, hand);
            if (done) return ItemInteractionResult.sidedSuccess(level.isClientSide);
        }
        return super.useItemOn(stack, state, level, pos, player, hand, hit);
    }

    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean moved) {
        if (!state.is(newState.getBlock()) && level.getBlockEntity(pos) instanceof ChainMachineBlockEntity machine) machine.dropContents();
        super.onRemove(state, level, pos, newState, moved);
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (!state.getValue(MultiblockHost.FORMED) || !state.getValue(BlockStateProperties.LIT)
                || !(level.getBlockEntity(pos) instanceof MultiblockCoreBlockEntity core)) return;
        for (double[] s : effects.smoke()) {
            if (random.nextBoolean()) continue;
            Vec3 p = MechanicusForgeBlock.toWorld(core.orientation(), pos, s);
            level.addParticle(ParticleTypes.CAMPFIRE_COSY_SMOKE, p.x, p.y, p.z, 0, 0.07, 0);
        }
        for (double[] s : effects.sparks()) {
            if (random.nextInt(3) != 0) continue;
            Vec3 p = MechanicusForgeBlock.toWorld(core.orientation(), pos, s);
            level.addParticle(ParticleTypes.LAVA, p.x, p.y, p.z, 0, 0, 0);
        }
        if (effects.sound() != null && random.nextInt(8) == 0) {
            level.playLocalSound(pos.getX() + 0.5, pos.getY() + 1.5, pos.getZ() + 0.5, effects.sound(), SoundSource.BLOCKS,
                    0.8f, effects.pitch(), false);
        }
    }
}
