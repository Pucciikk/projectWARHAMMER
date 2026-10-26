package dev.warpbound.industry;

import com.mojang.serialization.MapCodec;
import dev.warpbound.core.WarpboundBlockEntities;
import dev.warpbound.multiblock.MachineCoreBlock;
import dev.warpbound.multiblock.MachineCoreBlockEntity;
import dev.warpbound.multiblock.MultiblockCoreBlockEntity;
import dev.warpbound.multiblock.MultiblockHost;
import dev.warpbound.multiblock.MultiblockOrientation;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
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

/** Ядро Кузни Механикус: алтарь в середине переднего ряда шаблона. */
public class MechanicusForgeBlock extends MachineCoreBlock {
    public static final MapCodec<MechanicusForgeBlock> CODEC = simpleCodec(MechanicusForgeBlock::new);
    /** Точки модели в блоках от ядра (ядро смотрит на север, +Z — вглубь кузни): трубы и горн. */
    private static final double[][] CHIMNEYS = {{-1.5, 6.6, 3.5}, {1.5, 6.6, 3.5}};
    private static final double[] HEARTH = {0, 1.3, 3.0};

    public MechanicusForgeBlock(Properties properties) {
        super(properties);
        registerDefaultState(defaultBlockState().setValue(BlockStateProperties.LIT, false));
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        super.createBlockStateDefinition(builder);
        builder.add(BlockStateProperties.LIT);
    }

    @Override
    protected BlockEntityType<? extends MultiblockCoreBlockEntity> coreType() {
        return WarpboundBlockEntities.MECHANICUS_FORGE;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new MechanicusForgeBlockEntity(pos, state);
    }

    @Override
    protected InteractionResult useFormed(BlockState state, Level level, BlockPos pos, Player player, MachineCoreBlockEntity core) {
        if (!level.isClientSide) {
            player.displayClientMessage(Component.translatable(state.getValue(BlockStateProperties.LIT)
                    ? "block.warpbound.mechanicus_forge.working" : "block.warpbound.mechanicus_forge.waiting")
                    .withStyle(ChatFormatting.GOLD), true);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (!state.getValue(MultiblockHost.FORMED) || !(level.getBlockEntity(pos) instanceof MultiblockCoreBlockEntity core)) return;
        boolean lit = state.getValue(BlockStateProperties.LIT);
        for (double[] c : CHIMNEYS) {
            if (random.nextInt(lit ? 1 : 4) != 0) continue;
            Vec3 p = toWorld(core.orientation(), pos, c);
            level.addParticle(ParticleTypes.CAMPFIRE_COSY_SMOKE, p.x, p.y, p.z, 0, 0.06, 0);
        }
        if (!lit) return;
        Vec3 h = toWorld(core.orientation(), pos, HEARTH);
        level.addParticle(ParticleTypes.LAVA, h.x, h.y, h.z, 0, 0, 0);
        if (random.nextInt(2) == 0) {
            level.addParticle(ParticleTypes.ELECTRIC_SPARK, h.x + random.nextGaussian() * 0.3, h.y + 0.4, h.z + random.nextGaussian() * 0.3,
                    random.nextGaussian() * 0.1, 0.12, random.nextGaussian() * 0.1);
        }
        if (random.nextInt(8) == 0) {
            level.playLocalSound(h.x, h.y, h.z, SoundEvents.BLASTFURNACE_FIRE_CRACKLE, SoundSource.BLOCKS, 1f, 0.7f, false);
        }
    }

    /** Точку модели — в мир: поворот как у шаблона (смещение «вглубь», +Z, уходит от лица ядра). */
    public static Vec3 toWorld(MultiblockOrientation orientation, BlockPos pos, double[] local) {
        double x = local[0], z = local[2];
        double rx, rz;
        switch (orientation.facing()) {
            case EAST -> {
                rx = -z;
                rz = x;
            }
            case SOUTH -> {
                rx = -x;
                rz = -z;
            }
            case WEST -> {
                rx = z;
                rz = -x;
            }
            default -> {
                rx = x;
                rz = z;
            }
        }
        return new Vec3(pos.getX() + 0.5 + rx, pos.getY() + local[1], pos.getZ() + 0.5 + rz);
    }
}
