package dev.warpbound.industry;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import dev.warpbound.core.DataRegistry;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ItemParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

import java.util.Optional;

/**
 * Ручной пресс: заготовка в руке, ПКМ — удар. Несколько ударов — и деталь готова.
 * Shift+ПКМ пустой рукой меняет штамп (шестерня или пластина). Ход пресса виден на модели.
 */
public class ManualPressBlock extends HorizontalDirectionalBlock {
    public static final MapCodec<ManualPressBlock> CODEC = simpleCodec(ManualPressBlock::new);
    public static final EnumProperty<Die> DIE = EnumProperty.create("die", Die.class);
    /** Сколько ударов уже сделано по текущей заготовке. */
    public static final IntegerProperty STROKES = IntegerProperty.create("strokes", 0, 7);

    public static final DataRegistry<PressingRecipe> RECIPES = new DataRegistry<>("pressing", PressingRecipe.CODEC);

    private static final VoxelShape SHAPE = Shapes.or(
            Block.box(1, 0, 1, 15, 4, 15),     // станина
            Block.box(2, 4, 2, 4, 14, 4), Block.box(12, 4, 2, 14, 14, 4),
            Block.box(2, 4, 12, 4, 14, 14), Block.box(12, 4, 12, 14, 14, 14),
            Block.box(1, 14, 1, 15, 16, 15));  // верхняя траверса

    public enum Die implements StringRepresentable {
        GEAR("gear"), PLATE("plate");

        public static final Codec<Die> CODEC = StringRepresentable.fromEnum(Die::values);
        private final String name;

        Die(String name) {
            this.name = name;
        }

        @Override
        public String getSerializedName() {
            return name;
        }

        Die next() {
            return values()[(ordinal() + 1) % values().length];
        }
    }

    public ManualPressBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(DIE, Die.GEAR).setValue(STROKES, 0));
    }

    public static void register() {
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, DIE, STROKES);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPE;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!player.isShiftKeyDown()) return InteractionResult.PASS;
        if (!level.isClientSide) {
            Die die = state.getValue(DIE).next();
            level.setBlock(pos, state.setValue(DIE, die).setValue(STROKES, 0), Block.UPDATE_ALL);
            level.playSound(null, pos, SoundEvents.IRON_TRAPDOOR_CLOSE, SoundSource.BLOCKS, 1f, 1.2f);
            player.displayClientMessage(Component.translatable("block.warpbound.manual_press.die",
                    Component.translatable("block.warpbound.manual_press.die." + die.getSerializedName()))
                    .withStyle(ChatFormatting.GOLD), true);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
                                              Player player, InteractionHand hand, BlockHitResult hit) {
        Optional<PressingRecipe> recipe = RECIPES.all().values().stream()
                .filter(r -> r.matches(stack, state.getValue(DIE))).findFirst();
        if (recipe.isEmpty()) return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        if (!(level instanceof ServerLevel server)) return ItemInteractionResult.SUCCESS;

        int strokes = state.getValue(STROKES) + 1;
        server.sendParticles(new ItemParticleOption(ParticleTypes.ITEM, stack), pos.getX() + 0.5, pos.getY() + 0.3,
                pos.getZ() + 0.5, 6, 0.15, 0.05, 0.15, 0.08);
        if (strokes < recipe.get().presses()) {
            server.playSound(null, pos, SoundEvents.ANVIL_PLACE, SoundSource.BLOCKS, 0.4f, 1.4f + strokes * 0.1f);
            level.setBlock(pos, state.setValue(STROKES, Math.min(strokes, 7)), Block.UPDATE_ALL);
            return ItemInteractionResult.SUCCESS;
        }
        // Последний удар: заготовка становится деталью
        server.playSound(null, pos, SoundEvents.ANVIL_USE, SoundSource.BLOCKS, 0.8f, 1.1f);
        server.sendParticles(ParticleTypes.ELECTRIC_SPARK, pos.getX() + 0.5, pos.getY() + 0.4, pos.getZ() + 0.5,
                8, 0.2, 0.1, 0.2, 0.15);
        if (!player.getAbilities().instabuild) stack.shrink(1);
        ItemStack out = recipe.get().output();
        if (!player.getInventory().add(out)) player.drop(out, false);
        level.setBlock(pos, state.setValue(STROKES, 0), Block.UPDATE_ALL);
        return ItemInteractionResult.SUCCESS;
    }
}
