package dev.warpbound.start;

import dev.warpbound.core.WarpboundItems;
import dev.warpbound.operator.OperatorArrival;
import dev.warpbound.quest.QuestManager;
import dev.warpbound.quest.StoryFlags;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Вокс-маяк спасательной капсулы. Разбитый чинится вокс-модулем и металлом;
 * починенный принимает Знак Омниссии: освятить (ПКМ) — прилетит техножрец,
 * осквернить (Shift+ПКМ) — явится тёмный техножрец.
 */
public class VoxBeaconBlock extends HorizontalDirectionalBlock {
    public static final BooleanProperty REPAIRED = BooleanProperty.create("repaired");
    public static final com.mojang.serialization.MapCodec<VoxBeaconBlock> CODEC = simpleCodec(VoxBeaconBlock::new);

    /** Что нужно для починки, кроме вокс-модуля в руке. */
    private static final int IRON = 8, COPPER = 8, REDSTONE = 8;

    public VoxBeaconBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(REPAIRED, false));
    }

    @Override
    protected com.mojang.serialization.MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, REPAIRED);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
    }

    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
                                              Player player, InteractionHand hand, BlockHitResult hit) {
        if (!state.getValue(REPAIRED) && stack.is(WarpboundItems.VOX_MODULE)) {
            if (level instanceof ServerLevel server && player instanceof ServerPlayer sp) repair(server, pos, state, sp, stack);
            return ItemInteractionResult.sidedSuccess(level.isClientSide);
        }
        if (state.getValue(REPAIRED) && stack.is(WarpboundItems.OMNISSIAH_SIGIL)) {
            if (level instanceof ServerLevel server && player instanceof ServerPlayer sp) {
                if (!player.getAbilities().instabuild) stack.shrink(1);
                if (player.isShiftKeyDown()) {
                    OperatorArrival.desecrate(server, pos, sp);
                } else {
                    OperatorArrival.callShuttle(server, pos, sp);
                }
            }
            return ItemInteractionResult.sidedSuccess(level.isClientSide);
        }
        return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level.isClientSide) return InteractionResult.SUCCESS;
        if (state.getValue(REPAIRED)) {
            player.displayClientMessage(Component.literal("Маяк передаёт сигнал в пустоту. Ему нужен знак, на который ответят.")
                    .withStyle(ChatFormatting.GREEN), true);
            if (player instanceof ServerPlayer sp) QuestManager.setFlag(sp, StoryFlags.BEACON_REPAIRED);
        } else {
            player.displayClientMessage(Component.literal(String.format(
                    "Маяк разбит. Нужен вокс-модуль в руке и %d железа, %d меди, %d редстоуна в инвентаре.",
                    IRON, COPPER, REDSTONE)).withStyle(ChatFormatting.GOLD), true);
        }
        return InteractionResult.CONSUME;
    }

    private static void repair(ServerLevel level, BlockPos pos, BlockState state, ServerPlayer player, ItemStack module) {
        boolean creative = player.getAbilities().instabuild;
        if (!creative && (count(player, Items.IRON_INGOT) < IRON || count(player, Items.COPPER_INGOT) < COPPER
                || count(player, Items.REDSTONE) < REDSTONE)) {
            player.displayClientMessage(Component.literal(String.format(
                    "Не хватает деталей: %d железа, %d меди, %d редстоуна.", IRON, COPPER, REDSTONE))
                    .withStyle(ChatFormatting.RED), true);
            return;
        }
        if (!creative) {
            take(player, Items.IRON_INGOT, IRON);
            take(player, Items.COPPER_INGOT, COPPER);
            take(player, Items.REDSTONE, REDSTONE);
            module.shrink(1);
        }
        level.setBlock(pos, state.setValue(REPAIRED, true), Block.UPDATE_ALL);
        level.playSound(null, pos, SoundEvents.ANVIL_USE, SoundSource.BLOCKS, 0.8f, 1.2f);
        level.playSound(null, pos, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 1f, 1.4f);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, pos.getX() + 0.5, pos.getY() + 1.1, pos.getZ() + 0.5,
                30, 0.4, 0.3, 0.4, 0.2);
        player.displayClientMessage(Component.literal("Вокс-маяк ожил. Сигнал ушёл в небо.")
                .withStyle(ChatFormatting.GREEN), true);
        QuestManager.setFlag(player, StoryFlags.BEACON_REPAIRED);
    }

    private static int count(Player player, Item item) {
        return player.getInventory().countItem(item);
    }

    private static void take(Player player, Item item, int amount) {
        var inv = player.getInventory();
        for (int i = 0; i < inv.getContainerSize() && amount > 0; i++) {
            ItemStack s = inv.getItem(i);
            if (!s.is(item)) continue;
            int n = Math.min(amount, s.getCount());
            s.shrink(n);
            amount -= n;
        }
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (state.getValue(REPAIRED)) {
            if (random.nextInt(4) == 0) {
                level.addParticle(ParticleTypes.GLOW, pos.getX() + 0.5, pos.getY() + 1.05, pos.getZ() + 0.5, 0, 0.05, 0);
            }
        } else if (random.nextInt(3) == 0) {
            level.addParticle(ParticleTypes.ELECTRIC_SPARK, pos.getX() + random.nextDouble(), pos.getY() + 0.9,
                    pos.getZ() + random.nextDouble(), 0, 0.02, 0);
            if (random.nextInt(4) == 0) level.addParticle(ParticleTypes.SMOKE, pos.getX() + 0.5, pos.getY() + 1, pos.getZ() + 0.5, 0, 0.03, 0);
        }
    }
}
