package dev.warpbound.industry;

import com.mojang.serialization.MapCodec;
import dev.warpbound.core.WarpboundBlockEntities;
import dev.warpbound.core.WarpboundItems;
import dev.warpbound.multiblock.MachineCoreBlock;
import dev.warpbound.multiblock.MachineCoreBlockEntity;
import dev.warpbound.multiblock.MultiblockCoreBlockEntity;
import dev.warpbound.multiblock.MultiblockHost;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.phys.Vec3;

/** Ядро прометиевого экстрактора: пульт в середине переднего ряда. ПКМ — состояние бака, с ведром — забрать прометий. */
public class PromethiumExtractorBlock extends MachineCoreBlock {
    public static final MapCodec<PromethiumExtractorBlock> CODEC = simpleCodec(PromethiumExtractorBlock::new);
    /** Точки модели в блоках от ядра: дымовые трубы и устье скважины. */
    private static final double[][] STACKS = {{-1.75, 8.6, 11.9}, {1.75, 8.6, 11.9}};
    private static final double[] WELL = {0, 3.4, 1.5};

    public PromethiumExtractorBlock(Properties properties) {
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
        return WarpboundBlockEntities.PROMETHIUM_EXTRACTOR;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new PromethiumExtractorBlockEntity(pos, state);
    }

    @Override
    protected InteractionResult useFormed(BlockState state, Level level, BlockPos pos, Player player, MachineCoreBlockEntity core) {
        if (level instanceof ServerLevel sl && core instanceof PromethiumExtractorBlockEntity be) {
            ItemStack hand = player.getMainHandItem();
            if (hand.is(Items.BUCKET) && be.drainBucket()) {
                if (!player.getAbilities().instabuild) hand.shrink(1);
                ItemStack full = new ItemStack(WarpboundItems.CRUDE_PROMETHIUM_BUCKET);
                if (!player.getInventory().add(full)) player.drop(full, false);
                sl.playSound(null, pos, SoundEvents.BUCKET_FILL_LAVA, SoundSource.BLOCKS, 1f, 0.8f);
            }
            player.displayClientMessage(Component.translatable("block.warpbound.promethium_extractor.status",
                    be.stored() / PromethiumExtractorBlockEntity.BUCKET, PromethiumExtractorBlockEntity.CAPACITY / PromethiumExtractorBlockEntity.BUCKET,
                    be.richness(sl)).withStyle(ChatFormatting.GOLD), true);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (!state.getValue(MultiblockHost.FORMED) || !state.getValue(BlockStateProperties.LIT)
                || !(level.getBlockEntity(pos) instanceof MultiblockCoreBlockEntity core)) return;
        for (double[] s : STACKS) {
            Vec3 p = MechanicusForgeBlock.toWorld(core.orientation(), pos, s);
            level.addParticle(ParticleTypes.CAMPFIRE_SIGNAL_SMOKE, p.x, p.y, p.z, 0, 0.09, 0);
            if (random.nextInt(4) == 0) level.addParticle(ParticleTypes.FLAME, p.x, p.y - 0.1, p.z, 0, 0.03, 0);
        }
        Vec3 w = MechanicusForgeBlock.toWorld(core.orientation(), pos, WELL);
        if (random.nextInt(3) == 0) level.addParticle(ParticleTypes.SMOKE, w.x, w.y, w.z, 0, 0.02, 0);
        if (random.nextInt(10) == 0) {
            level.playLocalSound(w.x, w.y, w.z, SoundEvents.PISTON_EXTEND, SoundSource.BLOCKS, 0.7f, 0.5f, false);
            level.playLocalSound(w.x, w.y, w.z, SoundEvents.IRON_GOLEM_STEP, SoundSource.BLOCKS, 0.9f, 0.6f, false);
        }
    }
}
